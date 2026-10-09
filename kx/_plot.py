"""kx.plot: the one-liner. Kinds live in kx/kinds/; this file checks input and applies common flags."""
import contextlib

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

from . import kinds  # noqa: F401  (registers every kind)
from ._spec import KINDS, parse
from ._theme import style_path


def plot(x: ArrayLike, y: ArrayLike | None = None, z: ArrayLike | str | None = None,
         spec: str | None = None, title: str | None = None, ax: Axes | None = None,
         by: ArrayLike | None = None) -> Axes:
    """kx.plot(x, y, z, 'scatter-dark-grid-leg')   or   kx.plot(x, y, 'bar-light')

    by= gives a group label per x value, one curve per group: kx.plot(df.value, spec='kde', by=df.group).

    A theme in the spec applies to this plot only; kx.use() sets the notebook default.
    """
    if isinstance(z, str):                      # kx.plot(x, y, "spec"): spec given as 3rd arg
        if spec is not None:
            raise TypeError("spec given twice (as z and as spec=)")
        z, spec = None, z
    name, theme, flags = parse(spec or "line")
    kind = KINDS[name]
    if kind.needs_y and y is None:
        raise ValueError(f"kind {name!r} needs both x and y")
    if by is not None and not kind.takes_by:
        raise ValueError(f"by= only works with kind {sorted(k.name for k in KINDS.values() if k.takes_by)}, "
                         f"not {name!r}")
    if kind.check:
        kind.check(y, z, flags)

    style = plt.style.context(["default", style_path(theme)]) if theme else contextlib.nullcontext()
    with style:
        ax = ax or plt.subplots()[1]
        kind.draw(ax, x, y, z, flags, **({"by": by} if by is not None else {}))

        if "grid" in flags:  ax.grid(True)
        if "leg" in flags and ax.get_legend() is None:   # a 100% stack has no free corner: legend goes right
            outside = name == "area" and "norm" in flags
            ax.legend(**({"loc": "center left", "bbox_to_anchor": (1, 0.5)} if outside else {}))
        if "logx" in flags:  ax.set_xscale("log")
        if "logy" in flags:  ax.set_yscale("log")
        if title:            ax.set_title(title)
        if "tight" in flags: ax.figure.tight_layout()
    return ax
