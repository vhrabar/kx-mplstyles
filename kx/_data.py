"""Demo data that ships in data/."""
import pandas as pd

from . import _files


def datasets() -> list[str]:
    """List CSV names available to kx.load()."""
    return _files.names("data", ".csv")


def load(name: str) -> pd.DataFrame:
    """Read data/<name>.csv that ships with the package."""
    if name not in datasets():
        raise ValueError(f"unknown dataset {name!r}. Available: {datasets()}")
    return pd.read_csv(_files.path("data", f"{name}.csv"))
