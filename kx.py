"""
kx: tiny matplotlib helper.

Token grammar for kx.plot(spec):   kind-theme-flag-flag-...
  kind  : line | scatter | bar | hist
  theme : any file name in styles/
  flags : grid | leg | logx | logy | tight
"""
import glob
import inspect
import os
import sys
from typing import Any

import matplotlib.pyplot as plt

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
    plt.style.use(_style_path(name))
    if palette:
        plt.rcParams["axes.prop_cycle"] = plt.cycler(color=palette)
    plt.rcParams.update({k.replace("__", "."): v for k, v in rc.items()})
