import re
from collections.abc import Callable
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
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


@pytest.mark.parametrize(("spec", "match"), [
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


def test_scatter_text_z_becomes_legend() -> None:
    labels = np.where(Z > 2, "high", "low")
    ax = kx.plot(X, Y, pd.Series(labels, name="level"), "scatter")
    assert len(ax.figure.axes) == 1                    # no colorbar
    assert len(ax.collections) == 2
    leg = ax.get_legend()
    assert leg.get_title().get_text() == "level"
    assert [t.get_text() for t in leg.get_texts()] == ["high", "low"]
    assert sum(len(c.get_offsets()) for c in ax.collections) == len(X)


def test_scatter_categorical_keeps_category_order_and_bool_is_category() -> None:
    cats = pd.Series(pd.Categorical(np.where(Z > 2, "b", "a"), categories=["b", "a"]))
    assert [t.get_text() for t in kx.plot(X, Y, cats, "scatter").get_legend().get_texts()] == ["b", "a"]
    assert [t.get_text() for t in kx.plot(X, Y, Z > 2, "scatter-leg").get_legend().get_texts()] == ["False", "True"]


@pytest.mark.parametrize("with_z", [False, True])
def test_step(with_z: bool) -> None:
    ax = kx.plot(X, Y, Z if with_z else None, "step")
    assert len(ax.lines) == (2 if with_z else 1)
    assert all(ln.get_drawstyle() == "steps-mid" for ln in ax.lines)


def test_area_overlaps_by_default() -> None:
    ax = kx.plot(X, Y, Z, "area")
    assert len(ax.lines) == 2
    assert len(ax.collections) == 2


def test_area_stack() -> None:
    ax = kx.plot(X, Y, Z, "area-stack-leg")
    assert len(ax.collections) == 2
    assert len(ax.lines) == 0
    top = ax.collections[1].get_paths()[0].vertices[:, 1].max()
    assert top == pytest.approx((Y + Z).max())


def test_area_norm_is_100_percent_stack() -> None:
    ax = kx.plot(X, Y, Z, "area-norm")
    top = ax.collections[1].get_paths()[0].vertices[:, 1].max()
    assert top == pytest.approx(100)
    assert ax.get_ylim() == (0, 100)
    assert ax.yaxis.get_major_formatter()(50, 0) == "50%"


def test_area_norm_legend_sits_outside() -> None:
    leg = kx.plot(X, Y, Z, "area-norm-leg").get_legend()
    assert leg.get_bbox_to_anchor().bounds[0] > leg.axes.bbox.bounds[0]    # anchored right of the axes


def test_band_is_y_plus_minus_z() -> None:
    ax = kx.plot(X, Y, np.full_like(Y, 0.5), "band-leg")
    ys = ax.collections[0].get_paths()[0].vertices[:, 1]
    assert ys.min() == pytest.approx(Y.min() - 0.5)
    assert ys.max() == pytest.approx(Y.max() + 0.5)
    assert to_hex(ax.collections[0].get_facecolor()[0]) == to_hex(ax.lines[0].get_color())
    assert len(ax.get_legend().get_texts()) == 2


@pytest.mark.parametrize(("spec", "call", "match"), [
    ("band", lambda s: kx.plot(X, Y, spec=s), "needs z"),
    ("area-norm", lambda s: kx.plot(X, Y, spec=s), "needs two series"),
    ("line-stack", lambda s: kx.plot(X, Y, Z, s), "only works with kind"),
    ("bar-norm", lambda s: kx.plot(X, Y, Z, s), "only works with kind"),
    ("line-cum", lambda s: kx.plot(X, Y, Z, s), "only works with kind"),
    ("kde-stack", lambda s: kx.plot(X, Y, Z, s), "only works with kind"),
    ("hist", lambda s: kx.plot(X, spec=s, by=X > 5), "by= only works with kind"),
    ("kde", lambda s: kx.plot(X, Y, spec=s, by=X > 5), "pass only x"),
    ("kde", lambda s: kx.plot(X, spec=s, by=[1, 2]), "has 2 values but x has 20"),
    ("kde", lambda s: kx.plot(np.ones(5), spec=s), "at least 2 distinct"),
])
def test_new_kind_errors(spec: str, call: Callable[[str], Axes], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        call(spec)


@pytest.mark.parametrize("with_z", [False, True])
def test_bar_groups_and_category_ticks(with_z: bool) -> None:
    cats = ["a", "b", "c"]
    ax = kx.plot(cats, [1, 2, 3], [3, 2, 1] if with_z else None, "bar")
    assert len(ax.patches) == (6 if with_z else 3)
    assert [t.get_text() for t in ax.get_xticklabels()] == cats


@pytest.mark.parametrize("name", ["bar", "barh"])
def test_bar_stack_puts_z_on_top_of_y(name: str) -> None:
    ax = kx.plot(["a", "b", "c"], [1, 2, 3], [3, 2, 1], f"{name}-stack-leg")
    _, z_bars = ax.containers
    start, length, thickness = ("get_x", "get_width", "get_height") if name == "barh" \
        else ("get_y", "get_height", "get_width")
    assert [getattr(p, start)() for p in z_bars] == [1, 2, 3]
    assert [getattr(p, start)() + getattr(p, length)() for p in z_bars] == [4, 4, 4]
    assert {getattr(p, thickness)() for p in ax.patches} == {0.8}          # full width, not split
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["y", "z"]


@pytest.mark.parametrize("with_z", [False, True])
def test_barh_categories_top_to_bottom(with_z: bool) -> None:
    cats = ["a", "b", "c"]
    ax = kx.plot(cats, [1, 2, 3], [3, 2, 1] if with_z else None, "barh")
    assert len(ax.patches) == (6 if with_z else 3)
    assert [p.get_width() for p in ax.containers[0]] == [1, 2, 3]
    assert [t.get_text() for t in ax.get_yticklabels()] == cats
    assert ax.yaxis_inverted()


@pytest.mark.parametrize("arrays", [1, 2, 3])
def test_hist_overlays_each_array(arrays: int) -> None:
    ax = kx.plot(*[X, Y, Z][:arrays], spec="hist")
    assert len(ax.containers) == arrays


def test_hist_shares_bins_across_arrays() -> None:
    ax = kx.plot(np.arange(10.0), np.arange(5.0, 20.0), spec="hist")
    lefts = [[p.get_x() for p in c] for c in ax.containers]
    assert lefts[0] == lefts[1]
    assert lefts[0][0] == 0
    assert lefts[0][-1] + ax.containers[0][-1].get_width() == pytest.approx(19)


def test_hist_stack_puts_y_on_top_of_x() -> None:
    ax = kx.plot(np.arange(10.0), np.arange(10.0), spec="hist-stack-leg")
    xs, ys = ax.containers
    assert [p.get_y() for p in ys] == [p.get_height() for p in xs]
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["x", "y"]


@pytest.mark.parametrize(("spec", "total"), [("hist-norm", None), ("hist-cum", 20), ("hist-norm-cum", 1)])
def test_hist_norm_and_cum(spec: str, total: float | None) -> None:
    ax = kx.plot(X, spec=spec)
    if total is None:                           # density: bar areas sum to 1
        assert sum(p.get_height() * p.get_width() for p in ax.containers[0]) == pytest.approx(1)
    else:                                       # cumulative outline: ends at everything
        assert ax.patches[0].get_xy()[:, 1].max() == pytest.approx(total)


def test_hist_ignores_nan() -> None:
    ax = kx.plot(np.r_[X, np.nan, np.inf], spec="hist-cum")
    assert ax.patches[0].get_xy()[:, 1].max() == len(X)


def test_hist_stack_cum_keeps_filled_bars() -> None:
    ax = kx.plot(X, Y, spec="hist-stack-cum")
    assert ax.containers[1][-1].get_y() + ax.containers[1][-1].get_height() == 2 * len(X)


@pytest.mark.parametrize("arrays", [1, 2, 3])
def test_kde_draws_a_curve_per_array_with_area_one(arrays: int) -> None:
    ax = kx.plot(*[X, Y, Z][:arrays], spec="kde-leg")
    assert len(ax.lines) == arrays
    for ln in ax.lines:
        gx, gy = ln.get_data()
        assert (gy.sum() * (gx[1] - gx[0])) == pytest.approx(1, abs=1e-3)       # even grid: area = sum * step
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["x", "y", "z"][:arrays]


def test_kde_matches_gaussian_formula() -> None:
    from kx.kinds.dist import density
    v, grid = np.array([0.0, 1.0]), np.array([0.0, 0.5])
    expected = (np.exp(-0.5 * ((grid[:, None] - v) / 0.5) ** 2) / (0.5 * np.sqrt(2 * np.pi))).mean(axis=1)
    assert density(v, grid, 0.5) == pytest.approx(expected)


def test_kde_by_groups() -> None:
    df = pd.DataFrame({"v": np.r_[X, X + 20], "g": ["a"] * len(X) + ["b"] * len(X)})
    ax = kx.plot(df.v, spec="kde", by=df.g)
    assert len(ax.lines) == 2
    peaks = [ln.get_xdata()[np.argmax(ln.get_ydata())] for ln in ax.lines]
    assert peaks[0] < 12 < peaks[1]
    leg = ax.get_legend()
    assert leg.get_title().get_text() == "g"
    assert [t.get_text() for t in leg.get_texts()] == ["a", "b"]


def test_kde_by_numeric_groups_sorted() -> None:
    ax = kx.plot(np.r_[X, X], spec="kde", by=[2] * len(X) + [1] * len(X))
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["1", "2"]


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
    _, (a, b) = plt.subplots(1, 2)
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


@pytest.mark.parametrize(("name", "mpl_name"), [("set1", "Set1"), ("set2", "Set2"), ("dark2", "Dark2"),
                                                ("paired", "Paired"), ("tab10", "tab10"), ("tab20", "tab20")])
def test_palettes_match_matplotlib(name: str, mpl_name: str) -> None:
    assert [c.lower() for c in kx.palette(name)] == [to_hex(c) for c in mpl.colormaps[mpl_name].colors]


def test_okabe_palette() -> None:
    assert "okabe" in kx.palettes()
    assert kx.palette("okabe") == OKABE


@pytest.mark.parametrize("name", kx.palettes())
def test_palette_file_is_valid(name: str) -> None:
    colors = kx.palette(name)
    assert len(colors) >= 3
    assert all(re.fullmatch(r"#[0-9A-F]{6}", c) for c in colors), colors
    assert len(set(colors)) == len(colors)
    assert "#FFFFFF" not in colors              # white vanishes on light themes


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
    monkeypatch.setattr(kx._files, "root", str(tmp_path))
    assert kx.palettes() == ["mine"]
    assert kx.styles() == []                    # the subfolder is not a theme
    assert kx.palette("mine") == ["#112233", "#AABBCC"]


# ---------- colormaps ----------
def test_cmaps_lists_matplotlib_builtins() -> None:
    assert kx.cmaps() == sorted(n for n in kx.BUILTIN_CMAPS + kx.VENDORED_CMAPS if n in mpl.colormaps)
    assert set(kx.BUILTIN_CMAPS) - {"berlin", "managua", "vanimo"} <= set(kx.cmaps())   # only these need 3.10


def test_cmaps_skips_names_missing_from_matplotlib(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(kx._theme, "BUILTIN_CMAPS", ("viridis", "notacmap"))
    monkeypatch.setattr(kx._theme, "VENDORED_CMAPS", ())
    assert kx.cmaps() == ["viridis"]


@pytest.mark.parametrize("name", kx.VENDORED_CMAPS)
def test_vendored_cmaps_are_registered(name: str) -> None:
    assert mpl.colormaps[name].N == 256
    assert name in kx.cmaps()


@pytest.mark.parametrize("name", ["viridis", *kx.VENDORED_CMAPS])
def test_use_reversed_cmap(name: str) -> None:
    kx.use("light", cmap=f"{name}_r")
    rev = kx.plot(X, Y, Z, "scatter").collections[0].get_cmap()
    assert rev.name == f"{name}_r"
    assert to_hex(rev(1.0)) == to_hex(mpl.colormaps[name](0.0))


@pytest.mark.parametrize("name", kx.BUILTIN_CMAPS + kx.VENDORED_CMAPS)
def test_use_cmap_colours_scatter(name: str) -> None:
    if name not in mpl.colormaps:
        pytest.skip(f"{name} needs a newer matplotlib")
    kx.use("light", cmap=name)
    assert kx.plot(X, Y, Z, "scatter").collections[0].get_cmap().name == name


def test_unknown_cmap_leaves_theme_untouched() -> None:
    kx.use("dark")
    with pytest.raises(ValueError, match="unknown cmap"):
        kx.use("light", cmap="nope")
    with pytest.raises(ValueError, match="unknown cmap"):
        kx.use("light", cmap="nope_r")
    assert to_hex(mpl.rcParams["axes.facecolor"]) == "#111418"


@pytest.mark.parametrize("fn", [kx.use, kx.show])
def test_unknown_theme(fn) -> None:  # noqa: ANN001
    with pytest.raises(ValueError, match="unknown theme"):
        fn("nope")


def test_styles_discovers_new_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "styles").mkdir()
    (tmp_path / "styles" / "mine.mplstyle").write_text("lines.linewidth: 3\n")
    monkeypatch.setattr(kx._files, "root", str(tmp_path))
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
    assert "scatter" in out
    assert "dark" in out
    assert "logy" in out
    assert "okabe" in out
    assert "viridis" in out
    kx.source()
    assert "def plot(" in capsys.readouterr().out



def test_grammar_and_source_of_one_kind(capsys: pytest.CaptureFixture[str]) -> None:
    kx.grammar("area")
    out = capsys.readouterr().out
    assert "100% stack" in out
    assert "'norm'" in out
    assert "'grid'" in out
    kx.source("band")
    out = capsys.readouterr().out
    assert out.lstrip().startswith("@kind(\"band\"")
    assert "def scatter(" not in out


@pytest.mark.parametrize("fn", [kx.grammar, kx.source])
def test_unknown_kind(fn) -> None:  # noqa: ANN001
    with pytest.raises(ValueError, match="unknown kind"):
        fn("nope")


@pytest.mark.parametrize("name", ["line", "grid", "a-b"])
def test_kind_names_stay_unique_tokens(name: str) -> None:
    with pytest.raises(ValueError, match="taken"):
        kx._spec.kind(name)(lambda *a: None)

# ---------- data ----------
def test_datasets_and_load() -> None:
    assert {"waves", "cloud", "monthly", "dists"} <= set(kx.datasets())
    assert list(kx.load("waves").columns) == ["x", "y", "z"]


def test_load_unknown() -> None:
    with pytest.raises(ValueError, match="unknown dataset"):
        kx.load("nope")


def test_version_comes_from_pyproject() -> None:
    toml = (Path(kx.__file__).parent.parent / "pyproject.toml").read_text()
    assert f'\nversion = "{kx.__version__}"\n' in toml
