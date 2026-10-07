"""
kx: tiny matplotlib helper.

Token grammar for kx.plot(spec):   kind-theme-flag-flag-...
  kind  : line | scatter | bar | hist
  theme : any file name in styles/
  flags : grid | leg | logx | logy | tight
"""
import contextlib
import glob
import inspect
import os
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

_root = os.path.dirname(os.path.abspath(__file__))

KINDS = {"line", "scatter", "bar", "hist"}
FLAGS = {"grid", "leg", "logx", "logy", "tight"}


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


# ---------- setup ----------
def use(name: str = "dark", palette: list[str] | None = None, **rc: Any) -> None:
    """Apply a theme, optional palette (list of hex colors), and rcParam overrides.
    Use double underscore for dots:  figure__figsize=(8, 4)  ->  figure.figsize
    """
    plt.style.use(["default", _style_path(name)])      # reset first so themes never mix
    if palette:
        plt.rcParams["axes.prop_cycle"] = plt.cycler(color=palette)
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
    return (kinds or ["line"])[0], (picked or [None])[0], set(toks) & FLAGS


def _label(arr: ArrayLike, default: str) -> str:
    """Use a pandas Series name as legend label when there is one."""
    name = getattr(arr, "name", None)
    return str(name) if name is not None else default


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

    style = plt.style.context(["default", _style_path(theme)]) if theme else contextlib.nullcontext()
    with style:
        ax = ax or plt.subplots()[1]

        if kind == "line":                      # y and z against x
            ax.plot(x, y, label=_label(y, "y"))
            if z is not None:
                ax.plot(x, z, label=_label(z, "z"))
        elif kind == "scatter":                 # z -> point color
            sc = ax.scatter(x, y, c=z, s=18)
            if z is not None:
                ax.figure.colorbar(sc, ax=ax, label=_label(z, "z"))
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
        if "leg" in flags:   ax.legend()
        if "logx" in flags:  ax.set_xscale("log")
        if "logy" in flags:  ax.set_yscale("log")
        if title:            ax.set_title(title)
        if "tight" in flags: ax.figure.tight_layout()
    return ax
