"""Distribution kinds."""
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

from .._spec import kind
from .._util import label


@kind("hist", needs_y=False)
def hist(ax: Axes, x: ArrayLike, y: ArrayLike | None, z: ArrayLike | None, flags: set[str]) -> None:
    """Up to three overlaid distributions: x, y and z."""
    for arr, n in zip((x, y, z), "xyz"):
        if arr is not None:
            ax.hist(arr, bins=30, alpha=0.6, label=label(arr, n))
