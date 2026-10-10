"""kx.plot: the one-liner. Kinds live in kx/kinds/; this file checks input and applies common flags."""
import contextlib

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

from . import kinds  # noqa: F401  (registers every kind)
from ._spec import KINDS, parse
from ._theme import style_path

OUTSIDE = {"loc": "center left", "bbox_to_anchor": (1, 0.5)}       # legend right of the axes


def plot(x: ArrayLike, y: ArrayLike | None = None, z: ArrayLike | str | None = None,
         spec: str | None = None, title: str | None = None, ax: Axes | None = None,
         by: ArrayLike | None = None) -> Axes:
    """kx.plot(x, y, z, 'scatter-dark-grid-leg')   or   kx.plot(x, y, 'bar-light')

    by= gives a group label per x value, one curve, box or violin per group:
    kx.plot(df.value, spec='kde', by=df.group).

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
    if "date" in flags:                         # strings and numbers become dates; a Series keeps its name
        x = pd.to_datetime(x)

    style = plt.style.context(["default", style_path(theme)]) if theme else contextlib.nullcontext()
    with style:
        ax = ax or plt.subplots()[1]
        kind.draw(ax, x, y, z, flags, **({"by": by} if by is not None else {}))
        _common(ax, name, kind.value_axis, flags)
        if title:            ax.set_title(title)
        if "tight" in flags: ax.figure.tight_layout()
    return ax


def _common(ax: Axes, name: str, value_axis: str, flags: set[str]) -> None:
    """Flags every kind takes: legend, scales, value-axis format, ticks."""
    values = ax.xaxis if value_axis == "x" else ax.yaxis
    if "grid" in flags:  ax.grid(True)
    if flags & {"leg", "legout"}:               # a 100% stack has no free corner: legend goes right
        old = ax.get_legend()
        outside = "legout" in flags or (name == "area" and "norm" in flags)
        if old is None or outside:              # moving a kind's own legend keeps its title
            ax.legend(title=old.get_title().get_text() if old else None, **(OUTSIDE if outside else {}))
    if flags & {"logx", "logxy"}: ax.set_xscale("log")
    if flags & {"logy", "logxy"}: ax.set_yscale("log")
    if "symlogy" in flags:        ax.set_yscale("symlog")
    if "zero" in flags:                         # stretch the value axis to include 0
        lo, hi = values.get_view_interval()
        (ax.set_xlim if value_axis == "x" else ax.set_ylim)(min(lo, 0), max(hi, 0))
    if "eq" in flags:    ax.set_aspect("equal")
    if "pct" in flags and not isinstance(values.get_major_formatter(), mpl.ticker.PercentFormatter):
        values.set_major_formatter(mpl.ticker.PercentFormatter(1))  # 0.25 -> 25%; area-norm is already %
    if "si" in flags:    values.set_major_formatter(mpl.ticker.EngFormatter(sep=""))   # 1500 -> 1.5k
    if "date" in flags:
        loc = mdates.AutoDateLocator()
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
    if "rot" in flags:                          # rotation stays for ticks matplotlib adds later
        ax.tick_params(axis="x", labelrotation=45)
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
