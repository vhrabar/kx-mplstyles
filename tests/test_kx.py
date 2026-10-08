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


# ---------- palettes ----------
OKABE = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]


def test_okabe_palette() -> None:
    assert "okabe" in kx.palettes()
    assert kx.palette("okabe") == OKABE


def test_use_named_palette() -> None:
    kx.use("light", palette="okabe")
    ax = kx.plot(X, Y, Z, "line")
    assert [to_hex(ln.get_color()).upper() for ln in ax.lines] == OKABE[:2]


def test_palette_keeps_theme_linestyles() -> None:
    kx.use("paper", palette="okabe")
    cycle = mpl.rcParams["axes.prop_cycle"].by_key()
    assert cycle["color"] == OKABE
    assert cycle["linestyle"][:6] == ["-", "--", ":", "-.", "-", "--"]
    assert len(cycle["linestyle"]) == len(OKABE)


def test_unknown_palette() -> None:
    with pytest.raises(ValueError, match="unknown palette"):
        kx.use("dark", palette="nope")


def test_palettes_discovers_new_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "styles" / "palettes").mkdir(parents=True)
    (tmp_path / "styles" / "palettes" / "mine.txt").write_text("# comment\n\n112233\n  AABBCC  \n")
    monkeypatch.setattr(kx, "_root", str(tmp_path))
    assert kx.palettes() == ["mine"]
    assert kx.styles() == []                    # the subfolder is not a theme
    assert kx.palette("mine") == ["#112233", "#AABBCC"]


# ---------- colormaps ----------
def test_cmaps_lists_matplotlib_builtins() -> None:
    assert kx.cmaps() == sorted(kx.BUILTIN_CMAPS)   # all present on matplotlib >= 3.10


def test_cmaps_skips_names_missing_from_matplotlib(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(kx, "BUILTIN_CMAPS", ("viridis", "notacmap"))
    assert kx.cmaps() == ["viridis"]


@pytest.mark.parametrize("name", kx.BUILTIN_CMAPS)
def test_use_cmap_colours_scatter(name: str) -> None:
    kx.use("light", cmap=name)
    assert kx.plot(X, Y, Z, "scatter").collections[0].get_cmap().name == name


def test_unknown_cmap_leaves_theme_untouched() -> None:
    kx.use("dark")
    with pytest.raises(ValueError, match="unknown cmap"):
        kx.use("light", cmap="nope")
    assert to_hex(mpl.rcParams["axes.facecolor"]) == "#111418"


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


def test_paper_cycles_linestyles_for_greyscale_print() -> None:
    ax = kx.plot(X, Y, Z, "line-paper")
    assert ax.lines[0].get_linestyle() != ax.lines[1].get_linestyle()


def test_scatter_size_follows_theme_markersize() -> None:
    small = kx.plot(X, Y, "scatter-science").collections[0].get_sizes()[0]
    large = kx.plot(X, Y, "scatter-poster").collections[0].get_sizes()[0]
    assert kx.plot(X, Y, "scatter").collections[0].get_sizes()[0] == 18
    assert small < 18 < large


def test_every_shipped_style_loads() -> None:
    for name in kx.styles():
        kx.use(name)


# ---------- transparency ----------
def test_show_grammar_source(capsys: pytest.CaptureFixture[str]) -> None:
    kx.show("dark")
    assert "111418" in capsys.readouterr().out
    kx.grammar()
    out = capsys.readouterr().out
    assert "scatter" in out and "dark" in out and "logy" in out and "okabe" in out and "vanimo" in out
    kx.source()
    assert "def plot(" in capsys.readouterr().out


# ---------- data ----------
def test_datasets_and_load() -> None:
    assert {"waves", "cloud", "monthly", "dists"} <= set(kx.datasets())
    assert list(kx.load("waves").columns) == ["x", "y", "z"]


def test_load_unknown() -> None:
    with pytest.raises(ValueError, match="unknown dataset"):
        kx.load("nope")
