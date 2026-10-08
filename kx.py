"""
kx: tiny matplotlib helper.

Token grammar for kx.plot(spec):   kind-theme-flag-flag-...
  kind  : line | step | area | band | scatter | bar | hist
  theme : any file name in styles/
  flags : grid | leg | logx | logy | tight | stack | norm  (stack and norm: area only)

Palettes (kx.use(theme, palette="okabe")): any file name in styles/palettes/
Colormaps (kx.use(theme, cmap="magma")):  kx.cmaps()
"""
import contextlib
import glob
import inspect
import os
import sys
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

_root = os.path.dirname(os.path.abspath(__file__))

KINDS = {"line", "step", "area", "band", "scatter", "bar", "hist"}
FLAGS = {"grid", "leg", "logx", "logy", "tight", "stack", "norm"}
KIND_FLAGS = {"stack": {"area"}, "norm": {"area"}}
BUILTIN_CMAPS = ("viridis", "magma", "plasma", "inferno", "cividis", "turbo",
                 "twilight", "coolwarm", "berlin", "managua", "vanimo")


# ---------- discovery / transparency ----------
def styles() -> list[str]:
    """List available theme names."""
    return sorted(os.path.basename(p)[:-len(".mplstyle")]
                  for p in glob.glob(os.path.join(_root, "styles", "*.mplstyle")))


def _style_path(name: str) -> str:
    """Path to styles/<name>.mplstyle; unknown names raise ValueError."""
    if name not in styles():
        raise ValueError(f"unknown theme {name!r}. Available: {styles()}")
    return os.path.join(_root, "styles", f"{name}.mplstyle")


def palettes() -> list[str]:
    """List available palette names."""
    return sorted(os.path.basename(p)[:-len(".txt")]
                  for p in glob.glob(os.path.join(_root, "styles", "palettes", "*.txt")))


def palette(name: str) -> list[str]:
    """Colors of styles/palettes/<name>.txt as '#RRGGBB' strings (one hex per line, '#' lines are comments)."""
    return _read_palette(name)


def _read_palette(name: str) -> list[str]:
    """palette() under a name that kx.use's `palette` argument does not shadow."""
    if name not in palettes():
        raise ValueError(f"unknown palette {name!r}. Available: {palettes()}")
    with open(os.path.join(_root, "styles", "palettes", f"{name}.txt")) as f:
        lines = (line.strip() for line in f)
        return [f"#{line}" for line in lines if line and not line.startswith("#")]


def cmaps() -> list[str]:
    """List supported colormap names that this matplotlib version has."""
    return sorted(n for n in BUILTIN_CMAPS if n in mpl.colormaps)


def show(name: str) -> None:
    """Print the contents of a style file."""
    with open(_style_path(name)) as f:
        print(f.read())


def source() -> None:
    """Print the source of this module."""
    print(inspect.getsource(sys.modules[__name__]))


def grammar() -> None:
    """Print the valid tokens for kx.plot specs."""
    print("kind :", sorted(KINDS))
    print("theme:", styles())
    print("flags:", sorted(FLAGS))
    print("palettes (kx.use):", palettes())
    print("cmaps    (kx.use):", cmaps())


# ---------- setup ----------
def use(name: str = "dark", palette: str | list[str] | None = None, cmap: str | None = None,
        **rc: Any) -> None:
    """Apply a theme, optional palette (name from styles/palettes/ or list of colors),
    colormap (one of kx.cmaps()), and rcParam overrides.
    Use double underscore for dots:  figure__figsize=(8, 4)  ->  figure.figsize
    """
    if cmap is not None and cmap not in cmaps():
        raise ValueError(f"unknown cmap {cmap!r}. Available: {cmaps()}")
    plt.style.use(["default", _style_path(name)])      # reset first so themes never mix
    if cmap:
        plt.rcParams["image.cmap"] = cmap
    if palette:
        colors = _read_palette(palette) if isinstance(palette, str) else list(palette)
        # swap only the colors; other cycled props (paper's linestyles) repeat to the new length
        rest = {k: v for k, v in plt.rcParams["axes.prop_cycle"].by_key().items() if k != "color"}
        plt.rcParams["axes.prop_cycle"] = plt.cycler(
            color=colors, **{k: [v[i % len(v)] for i in range(len(colors))] for k, v in rest.items()})
    plt.rcParams.update({k.replace("__", "."): v for k, v in rc.items()})


# ---------- data ----------
def datasets() -> list[str]:
    """List CSV names available to kx.load()."""
    return sorted(os.path.basename(p)[:-len(".csv")]
                  for p in glob.glob(os.path.join(_root, "data", "*.csv")))


def load(name: str) -> pd.DataFrame:
    """Read data/<name>.csv that ships with the dataset."""
    if name not in datasets():
        raise ValueError(f"unknown dataset {name!r}. Available: {datasets()}")
    return pd.read_csv(os.path.join(_root, "data", f"{name}.csv"))


# ---------- the one-liner plot ----------
def _parse(spec: str) -> tuple[str, str | None, set[str]]:
    """Split 'kind-theme-flag-...' into (kind, theme, flags). Strict: no guessing."""
    toks = spec.split("-")
    themes = set(styles())
    unknown = [t for t in toks if t not in KINDS | FLAGS | themes]
    if unknown:
        raise ValueError(f"unknown tokens: {unknown}. Run kx.grammar() to see valid ones.")
    kinds = [t for t in toks if t in KINDS]
    picked = [t for t in toks if t in themes]
    if len(kinds) > 1:
        raise ValueError(f"spec {spec!r} has more than one kind: {kinds}")
    if len(picked) > 1:
        raise ValueError(f"spec {spec!r} has more than one theme: {picked}")
    kind = (kinds or ["line"])[0]
    for flag in set(toks) & KIND_FLAGS.keys():
        if kind not in KIND_FLAGS[flag]:
            raise ValueError(f"flag {flag!r} only works with kind {sorted(KIND_FLAGS[flag])}, not {kind!r}")
    return kind, (picked or [None])[0], set(toks) & FLAGS


def _label(arr: ArrayLike, default: str) -> str:
    """Use a pandas Series name as legend label when there is one."""
    name = getattr(arr, "name", None)
    return str(name) if name is not None else default


def _categories(z: ArrayLike) -> list[Any] | None:
    """Category values of z if it is text, bool or categorical; None if z is numeric."""
    s = z if isinstance(z, pd.Series) else pd.Series(np.asarray(z))
    if isinstance(s.dtype, pd.CategoricalDtype):
        return list(s.cat.categories)
    if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
        return None
    return sorted(s.dropna().unique(), key=str)


def plot(x: ArrayLike, y: ArrayLike | None = None, z: ArrayLike | str | None = None,
         spec: str | None = None, title: str | None = None, ax: Axes | None = None) -> Axes:
    """kx.plot(x, y, z, 'scatter-dark-grid-leg')   or   kx.plot(x, y, 'bar-light')

    A theme in the spec applies to this plot only; kx.use() sets the notebook default.
    """
    if isinstance(z, str):                      # kx.plot(x, y, "spec"): spec given as 3rd arg
        if spec is not None:
            raise TypeError("spec given twice (as z and as spec=)")
        z, spec = None, z
    kind, theme, flags = _parse(spec or "line")
    if kind != "hist" and y is None:
        raise ValueError(f"kind {kind!r} needs both x and y")
    if kind == "band" and z is None:
        raise ValueError("kind 'band' needs z: the half-width of the band (y - z to y + z)")
    if "norm" in flags and z is None:
        raise ValueError("flag 'norm' needs two series (y and z) to split 100% between")

    style = plt.style.context(["default", _style_path(theme)]) if theme else contextlib.nullcontext()
    with style:
        ax = ax or plt.subplots()[1]

        if kind == "line":                      # y and z against x
            ax.plot(x, y, label=_label(y, "y"))
            if z is not None:
                ax.plot(x, z, label=_label(z, "z"))
        elif kind == "step":                    # like line, drawn as steps centred on each x
            ax.step(x, y, where="mid", label=_label(y, "y"))
            if z is not None:
                ax.step(x, z, where="mid", label=_label(z, "z"))
        elif kind == "area":                    # filled; stack = on top of each other, norm = 100% stack
            series = [(np.asarray(a, dtype=float), _label(a, n)) for a, n in ((y, "y"), (z, "z")) if a is not None]
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
                    line, = ax.plot(x, v, label=n)
                    ax.fill_between(x, v, color=line.get_color(), alpha=0.3, linewidth=0)
        elif kind == "band":                    # y line with a y ± z band
            mid, half = np.asarray(y, dtype=float), np.asarray(z, dtype=float)
            line, = ax.plot(x, mid, label=_label(y, "y"))
            ax.fill_between(x, mid - half, mid + half, color=line.get_color(), alpha=0.25,
                            linewidth=0, label=f"± {_label(z, 'z')}")
        elif kind == "scatter":                 # z -> colorbar (numbers) or legend (categories)
            size = 0.5 * plt.rcParams["lines.markersize"] ** 2
            cats = None if z is None else _categories(z)
            if cats is None:
                sc = ax.scatter(x, y, c=z, s=size)
                if z is not None:
                    ax.figure.colorbar(sc, ax=ax, label=_label(z, "z"))
            else:
                xs, ys, zs = np.asarray(x), np.asarray(y), np.asarray(z, dtype=object)
                for c in cats:
                    m = zs == c
                    ax.scatter(xs[m], ys[m], s=size, label=str(c))
                ax.legend(title=_label(z, "z"))
        elif kind == "bar":                     # y and z grouped, x = category labels
            w = 0.4
            idx = np.arange(len(x))
            if z is None:
                ax.bar(idx, y, 2 * w, label=_label(y, "y"))
            else:
                ax.bar(idx - w / 2, y, w, label=_label(y, "y"))
                ax.bar(idx + w / 2, z, w, label=_label(z, "z"))
            ax.set_xticks(idx, [str(v) for v in x])
        elif kind == "hist":                    # up to three overlaid distributions
            for arr, n in zip((x, y, z), "xyz"):
                if arr is not None:
                    ax.hist(arr, bins=30, alpha=0.6, label=_label(arr, n))

        if "grid" in flags:  ax.grid(True)
        if "leg" in flags and ax.get_legend() is None:   # a 100% stack has no free corner: legend goes right
            ax.legend(**({"loc": "center left", "bbox_to_anchor": (1, 0.5)} if "norm" in flags else {}))
        if "logx" in flags:  ax.set_xscale("log")
        if "logy" in flags:  ax.set_yscale("log")
        if title:            ax.set_title(title)
        if "tight" in flags: ax.figure.tight_layout()
    return ax
