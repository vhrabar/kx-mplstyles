from collections.abc import Iterator

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def clean_mpl() -> Iterator[None]:
    """Each test starts from matplotlib defaults and leaves no figures or rcParams behind."""
    with matplotlib.rc_context():
        matplotlib.rcdefaults()
        yield
    plt.close("all")
