from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_hex

import kx

X = np.linspace(1, 10, 20)
Y = np.sin(X) + 2
Z = np.cos(X) + 2


# ---------- spec parsing ----------
def test_parse_order_does_not_matter() -> None:
    assert kx._parse("scatter-dark-grid-leg") == kx._parse("leg-grid-dark-scatter")


def test_parse_defaults_to_line_and_no_theme() -> None:
    assert kx._parse("grid") == ("line", None, {"grid"})


@pytest.mark.parametrize("spec, match", [
    ("line-nope", "unknown tokens"),
    ("line--dark", "unknown tokens"),
    ("line-scatter", "more than one kind"),
    ("dark-light", "more than one theme"),
])
def test_parse_rejects_bad_specs(spec: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        kx._parse(spec)


# ---------- each kind, with and without z ----------
@pytest.mark.parametrize("with_z", [False, True])
def test_line(with_z: bool) -> None:
    ax = kx.plot(X, Y, Z if with_z else None, "line")
    assert len(ax.lines) == (2 if with_z else 1)


@pytest.mark.parametrize("with_z", [False, True])
def test_scatter_colorbar_only_with_z(with_z: bool) -> None:
    ax = kx.plot(X, Y, Z if with_z else None, "scatter")
    assert len(ax.collections) == 1
    assert len(ax.figure.axes) == (2 if with_z else 1)


@pytest.mark.parametrize("with_z", [False, True])
def test_bar_groups_and_category_ticks(with_z: bool) -> None:
    cats = ["a", "b", "c"]
    ax = kx.plot(cats, [1, 2, 3], [3, 2, 1] if with_z else None, "bar")
    assert len(ax.patches) == (6 if with_z else 3)
    assert [t.get_text() for t in ax.get_xticklabels()] == cats


@pytest.mark.parametrize("arrays", [1, 2, 3])
def test_hist_overlays_each_array(arrays: int) -> None:
    ax = kx.plot(*[X, Y, Z][:arrays], spec="hist")
    assert len(ax.containers) == arrays


# ---------- flags, title, labels ----------
def test_flags() -> None:
    ax = kx.plot(X, Y, Z, "line-grid-leg-logx-logy-tight", title="t")
    assert ax.get_xscale() == ax.get_yscale() == "log"
    assert ax.get_legend() is not None
    assert all(g.get_visible() for g in ax.get_xgridlines())
    assert ax.get_title() == "t"


def test_series_names_become_labels() -> None:
    df = pd.DataFrame({"x": X, "speed": Y, "accel": Z})
    ax = kx.plot(df.x, df.speed, df.accel, "line-leg")
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["speed", "accel"]


# ---------- call shapes ----------
def test_spec_as_third_positional() -> None:
    ax = kx.plot(X, Y, "bar")
    assert len(ax.patches) == len(X)


def test_spec_given_twice() -> None:
    with pytest.raises(TypeError):
        kx.plot(X, Y, "line", spec="bar")


def test_non_hist_needs_y() -> None:
    with pytest.raises(ValueError, match="needs both x and y"):
        kx.plot(X, spec="line")


def test_draws_into_given_ax() -> None:
    import matplotlib.pyplot as plt
    fig, (a, b) = plt.subplots(1, 2)
    assert kx.plot(X, Y, "line", ax=b) is b
    assert len(a.lines) == 0


# ---------- themes ----------
def test_theme_in_spec_is_local() -> None:
    before = dict(mpl.rcParams)
    ax = kx.plot(X, Y, "line-dark")
    assert to_hex(ax.get_facecolor()) == "#111418"
    assert {k for k in before if str(before[k]) != str(mpl.rcParams[k])} == set()


def test_use_sets_global_theme() -> None:
    kx.use("dark")
    assert to_hex(mpl.rcParams["axes.facecolor"]) == "#111418"


def test_use_resets_before_applying() -> None:
    kx.use("dark")                              # dark sets bold titles, light does not
    kx.use("light")
    assert mpl.rcParams["axes.titleweight"] == "normal"


def test_use_palette_and_rc_overrides() -> None:
    kx.use("light", palette=["#264653", "#e9c46a"], figure__figsize=(5, 2))
    assert mpl.rcParams["axes.prop_cycle"].by_key()["color"] == ["#264653", "#e9c46a"]
    assert tuple(mpl.rcParams["figure.figsize"]) == (5, 2)


@pytest.mark.parametrize("fn", [kx.use, kx.show])
def test_unknown_theme(fn) -> None:  # noqa: ANN001
    with pytest.raises(ValueError, match="unknown theme"):
        fn("nope")


def test_styles_discovers_new_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "styles").mkdir()
    (tmp_path / "styles" / "mine.mplstyle").write_text("lines.linewidth: 3\n")
    monkeypatch.setattr(kx, "_root", str(tmp_path))
    assert kx.styles() == ["mine"]
    assert kx.plot(X, Y, "line-mine").lines[0].get_linewidth() == 3


def test_every_shipped_style_loads() -> None:
    for name in kx.styles():
        kx.use(name)


# ---------- transparency ----------
def test_show_grammar_source(capsys: pytest.CaptureFixture[str]) -> None:
    kx.show("dark")
    assert "111418" in capsys.readouterr().out
    kx.grammar()
    out = capsys.readouterr().out
    assert "scatter" in out and "dark" in out and "logy" in out
    kx.source()
    assert "def plot(" in capsys.readouterr().out


# ---------- data ----------
def test_datasets_and_load() -> None:
    assert {"waves", "cloud", "monthly", "dists"} <= set(kx.datasets())
    assert list(kx.load("waves").columns) == ["x", "y", "z"]


def test_load_unknown() -> None:
    with pytest.raises(ValueError, match="unknown dataset"):
        kx.load("nope")
