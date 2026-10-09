"""Distribution kinds."""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

from .._spec import kind
from .._util import categories, label


def _finite(arr: ArrayLike) -> np.ndarray:
    """Values as floats, NaN and inf dropped: a gap in the data is not a value."""
    v = np.asarray(arr, dtype=float).ravel()
    return v[np.isfinite(v)]


def _series(x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None) -> list[tuple[np.ndarray, str]]:
    return [(_finite(a), label(a, n)) for a, n in ((x, "x"), (y, "y"), (z, "z")) if a is not None]


def _split(x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None,
           by: ArrayLike | None) -> list[tuple[np.ndarray, str]]:
    """x, y, z as separate series, or with by= x split into one series per group (categories in order)."""
    if by is None:
        return _series(x, y, z)
    if y is not None or z is not None:
        raise ValueError("by= splits x into groups; pass only x, not y or z")
    xs, groups = np.asarray(x, dtype=float).ravel(), np.asarray(by, dtype=object).ravel()
    if len(xs) != len(groups):
        raise ValueError(f"by= has {len(groups)} values but x has {len(xs)}")
    cats = categories(by)
    if cats is None:
        cats = sorted(pd.unique(groups[pd.notna(groups)]))
    return [(_finite(xs[groups == c]), str(c)) for c in cats]


def _need(series: list[tuple[np.ndarray, str]], kind: str, distinct: int) -> None:
    for v, n in series:
        if len(np.unique(v)) < distinct:
            what = "a finite value" if distinct == 1 else f"at least {distinct} distinct finite values"
            raise ValueError(f"{kind} of {n!r} needs {what}")


@kind("hist", flags=("stack", "norm", "cum"), needs_y=False)
def hist(ax: Axes, x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None, flags: set[str]) -> None:
    """Up to three distributions x, y, z on the same 30 bins, overlaid.
    stack = on top of each other, norm = density (area 1), cum = cumulative outlines (with norm: the CDF)."""
    series = _series(x, y, z)
    edges = np.histogram_bin_edges(np.concatenate([v for v, _ in series]), bins=30)
    values, names = [v for v, _ in series], [n for _, n in series]
    if "stack" in flags:
        ax.hist(values, edges, histtype="barstacked", label=names,
                density="norm" in flags, cumulative="cum" in flags)
    else:                                       # overlaid cumulative fills hide each other: outlines instead
        look = {"histtype": "step", "linewidth": 1.5} if "cum" in flags else {"alpha": 0.6}
        for v, n in zip(values, names, strict=True):
            ax.hist(v, edges, label=n, density="norm" in flags, cumulative="cum" in flags, **look)


def density(v: np.ndarray, grid: np.ndarray, bw: float) -> np.ndarray:
    """Gaussian KDE of v on grid with bandwidth bw, in chunks so big v does not need a len(v) x len(grid) array."""
    out = np.zeros_like(grid)
    for i in range(0, len(v), 4096):
        out += np.exp(-0.5 * ((grid[:, None] - v[None, i:i + 4096]) / bw) ** 2).sum(axis=1)
    return out / (len(v) * bw * np.sqrt(2 * np.pi))


def bandwidth(v: np.ndarray) -> float:
    """Silverman's rule of thumb, the IQR form: one outlier does not flatten the curve."""
    iqr = np.subtract(*np.percentile(v, [75, 25]))
    spread = min(v.std(ddof=1), iqr / 1.349) if iqr > 0 else v.std(ddof=1)
    return 0.9 * spread * len(v) ** -0.2


@kind("kde", needs_y=False, takes_by=True)
def kde(ax: Axes, x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None, flags: set[str],
        by: ArrayLike | None = None) -> None:
    """Smooth density curves of x, y, z (Gaussian KDE, Silverman bandwidth).
    by= splits x into one curve per group: kx.plot(df.value, spec='kde', by=df.group)."""
    series = _split(x, y, z, by)
    _need(series, "kde", 2)
    bws = [bandwidth(v) for v, _ in series]
    lo = min(v.min() - 3 * bw for (v, _), bw in zip(series, bws, strict=True))
    hi = max(v.max() + 3 * bw for (v, _), bw in zip(series, bws, strict=True))
    grid = np.linspace(lo, hi, 256)
    for (v, n), bw in zip(series, bws, strict=True):
        d = density(v, grid, bw)
        ln, = ax.plot(grid, d, label=n)
        ax.fill_between(grid, d, color=ln.get_color(), alpha=0.15, linewidth=0)
    ax.set_ylim(bottom=0)
    if by is not None:
        ax.legend(title=label(by, "by"))


@kind("ecdf", needs_y=False, takes_by=True)
def ecdf(ax: Axes, x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None, flags: set[str],
         by: ArrayLike | None = None) -> None:
    """Empirical CDF of x, y, z: the share of values <= each x, a step up of 1/n at every value.
    by= splits x into one curve per group."""
    series = _split(x, y, z, by)
    _need(series, "ecdf", 1)
    for v, n in series:
        v = np.sort(v)
        ax.step(np.r_[v[0], v], np.arange(len(v) + 1) / len(v), where="post", label=n)
    ax.set_ylim(0, 1.02)
    if by is not None:
        ax.legend(title=label(by, "by"))


def _per_group(ax: Axes, names: list[str], by: ArrayLike | None) -> None:
    """One tick per series, named; with by= the axis is named after the groups."""
    ax.set_xticks(range(1, len(names) + 1), names)
    if by is not None:
        ax.set_xlabel(label(by, "by"))


@kind("box", needs_y=False, takes_by=True)
def box(ax: Axes, x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None, flags: set[str],
        by: ArrayLike | None = None) -> None:
    """Box plots of x, y, z side by side: median, quartile box, whiskers to 1.5 IQR, outliers as points.
    by= splits x into one box per group."""
    series = _split(x, y, z, by)
    _need(series, "box", 1)
    ink = plt.rcParams["text.color"]           # whiskers and medians in the theme's ink, not black on dark
    line = {"color": ink}
    parts = ax.boxplot([v for v, _ in series], patch_artist=True, boxprops={"edgecolor": ink}, medianprops=line,
                       whiskerprops=line, capprops=line, flierprops={"markeredgecolor": ink})
    for i, patch in enumerate(parts["boxes"]):
        patch.set_facecolor((*mpl.colors.to_rgb(f"C{i}"), 0.7))      # alpha on the fill only, edge stays solid
    _per_group(ax, [n for _, n in series], by)


@kind("violin", needs_y=False, takes_by=True)
def violin(ax: Axes, x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None, flags: set[str],
           by: ArrayLike | None = None) -> None:
    """Violin plots of x, y, z side by side: a mirrored KDE with the median and quartiles marked.
    by= splits x into one violin per group."""
    series = _split(x, y, z, by)
    _need(series, "violin", 2)
    values = [v for v, _ in series]
    parts = ax.violinplot(values, showextrema=False)
    for i, body in enumerate(parts["bodies"]):
        body.set(facecolor=f"C{i}", edgecolor=f"C{i}", alpha=0.6)
    pos = np.arange(1, len(values) + 1)
    q1, med, q3 = np.array([np.percentile(v, [25, 50, 75]) for v in values]).T
    ink = plt.rcParams["text.color"]
    ax.vlines(pos, q1, q3, color=ink, linewidth=3)
    ax.scatter(pos, med, color=plt.rcParams["axes.facecolor"], edgecolor=ink, zorder=3)
    _per_group(ax, [n for _, n in series], by)
