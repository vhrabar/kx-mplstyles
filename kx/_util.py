"""Small helpers shared by the kinds."""
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike


def label(arr: ArrayLike, default: str) -> str:
    """Use a pandas Series name as legend label when there is one."""
    name = getattr(arr, "name", None)
    return str(name) if name is not None else default


def categories(z: ArrayLike) -> list[Any] | None:
    """Category values of z if it is text, bool or categorical; None if z is numeric."""
    s = z if isinstance(z, pd.Series) else pd.Series(np.asarray(z))
    if isinstance(s.dtype, pd.CategoricalDtype):
        return list(s.cat.categories)
    if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
        return None
    return sorted(s.dropna().unique(), key=str)
