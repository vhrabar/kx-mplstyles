"""Basic kinds: y and z against x."""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

from .._spec import kind
from .._util import categories, label


@kind("line")
def line(ax: Axes, x: ArrayLike, y: ArrayLike, z: ArrayLike | None, flags: set[str]) -> None:
    """y and z against x."""
    ax.plot(x, y, label=label(y, "y"))
    if z is not None:
        ax.plot(x, z, label=label(z, "z"))


@kind("step")
def step(ax: Axes, x: ArrayLike, y: ArrayLike, z: ArrayLike | None, flags: set[str]) -> None:
    """Like line, drawn as steps centred on each x."""
    ax.step(x, y, where="mid", label=label(y, "y"))
    if z is not None:
        ax.step(x, z, where="mid", label=label(z, "z"))


def _check_area(y: ArrayLike, z: ArrayLike | None, flags: set[str]) -> None:
    if "norm" in flags and z is None:
        raise ValueError("flag 'norm' needs two series (y and z) to split 100% between")


@kind("area", flags=("stack", "norm"), check=_check_area)
def area(ax: Axes, x: ArrayLike, y: ArrayLike, z: ArrayLike | None, flags: set[str]) -> None:
    """Filled y and z; stack = on top of each other, norm = 100% stack."""
    series = [(np.asarray(a, dtype=float), label(a, n)) for a, n in ((y, "y"), (z, "z")) if a is not None]
    if "norm" in flags:
        total = sum(v for v, _ in series)
        with np.errstate(invalid="ignore", divide="ignore"):
            series = [(100 * v / total, n) for v, n in series]
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(100))
        ax.set_ylim(0, 100)
    if "stack" in flags or "norm" in flags:
        ax.stackplot(x, *(v for v, _ in series), labels=[n for _, n in series])
    else:
        for v, n in series:
            ln, = ax.plot(x, v, label=n)
            ax.fill_between(x, v, color=ln.get_color(), alpha=0.3, linewidth=0)


def _check_band(y: ArrayLike, z: ArrayLike | None, flags: set[str]) -> None:
    if z is None:
        raise ValueError("kind 'band' needs z: the half-width of the band (y - z to y + z)")


@kind("band", check=_check_band)
def band(ax: Axes, x: ArrayLike, y: ArrayLike, z: ArrayLike, flags: set[str]) -> None:
    """y line with a y ± z band."""
    mid, half = np.asarray(y, dtype=float), np.asarray(z, dtype=float)
    ln, = ax.plot(x, mid, label=label(y, "y"))
    ax.fill_between(x, mid - half, mid + half, color=ln.get_color(), alpha=0.25,
                    linewidth=0, label=f"± {label(z, 'z')}")


@kind("scatter")
def scatter(ax: Axes, x: ArrayLike, y: ArrayLike, z: ArrayLike | None, flags: set[str]) -> None:
    """y against x; z becomes a colorbar (numbers) or a legend (categories)."""
    size = 0.5 * plt.rcParams["lines.markersize"] ** 2
    cats = None if z is None else categories(z)
    if cats is None:
        sc = ax.scatter(x, y, c=z, s=size)
        if z is not None:
            ax.figure.colorbar(sc, ax=ax, label=label(z, "z"))
    else:
        xs, ys, zs = np.asarray(x), np.asarray(y), np.asarray(z, dtype=object)
        for c in cats:
            m = zs == c
            ax.scatter(xs[m], ys[m], s=size, label=str(c))
        ax.legend(title=label(z, "z"))


@kind("bar", flags=("stack",))
def bar(ax: Axes, x: ArrayLike, y: ArrayLike, z: ArrayLike | None, flags: set[str],
        horizontal: bool = False) -> None:
    """y and z grouped per category, x = category labels; stack = z on top of y."""
    w = 0.4
    idx = np.arange(len(x))
    draw = ax.barh if horizontal else ax.bar
    if z is None:
        draw(idx, y, 2 * w, label=label(y, "y"))
    elif "stack" in flags:                      # z starts where y ends, so the bar's end is the total
        draw(idx, y, 2 * w, label=label(y, "y"))
        draw(idx, z, 2 * w, np.asarray(y, dtype=float), label=label(z, "z"))
    else:
        draw(idx - w / 2, y, w, label=label(y, "y"))
        draw(idx + w / 2, z, w, label=label(z, "z"))
    (ax.set_yticks if horizontal else ax.set_xticks)(idx, [str(v) for v in x])


@kind("barh", flags=("stack",))
def barh(ax: Axes, x: ArrayLike, y: ArrayLike, z: ArrayLike | None, flags: set[str]) -> None:
    """Like bar, lying down: categories (x) top to bottom, bar lengths along the x axis."""
    bar(ax, x, y, z, flags, horizontal=True)
    ax.invert_yaxis()                           # first category on top, read like a table
