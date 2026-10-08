# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **PyPI package:** `pip install kx-plot`, then `import kx`. The wheel ships the themes, palettes and demo CSVs.
- **Palettes:** Paul Tol (`tolbright`, `tolvibrant`, `tolhc`, `tolmc`), Petroff (`petroff6`, `petroff8`, `petroff10`),
  Tableau (`tab10`, `tableaucb`), ColorBrewer (`set2`, `dark2`) and `ibm`. Their licences are in
  `kx/styles/palettes/LICENCES.md`.

### Changed

- **`kx.py` is now the `kx/` package**, with the themes in `kx/styles/` and the demo CSVs in `kx/data/`.
  `kx.source()` prints every file in the package.

## [0.0.2] - 2026-10-08

### Added

- **Plot kinds**
  - `step`: like `line`, drawn as steps centred on each x.
  - `area`: filled areas, overlapping and semi-transparent by default.
    - `area-stack` stacks `z` on top of `y`, so the top edge is the total.
    - `area-norm` draws a 100% stack with a percent y axis. With `leg`, the legend goes outside on the right.
  - `band`: a `y` line with a shaded `y ± z` band in the same colour. `z` is required.
  - `scatter` with a text, bool or pandas categorical `z` draws one colour per category with a legend titled after `z`. A numeric `z` still gets a colorbar.
- **Flags**
  - `stack` and `norm`. Both work with `area` only for now.
- **Themes**
  - `science`: one journal column (3.5 in), 8 pt serif, inward ticks on all four sides, minor ticks, Paul Tol bright colours, saves at 600 dpi.
  - `talk`: slides (16:9), 18 pt sans, thick lines, Okabe-Ito colours.
  - `poster`: 12 × 9 in, 26 pt sans, very thick lines, saves at 300 dpi.
  - `thesis`: A4 text width (160 mm), Computer Modern 10/9 pt without needing LaTeX, saves as PDF when the file name has no extension.
- **Palettes**
  - Named palettes live in `styles/palettes/<name>.txt`, one hex colour per line. Any file added there is found automatically.
  - `okabe`: the Okabe-Ito palette, 8 colours that stay distinguishable for every common type of colour blindness.
  - `kx.palettes()` lists the palettes and `kx.palette(name)` returns a palette's colours.
  - `kx.use(theme, palette="okabe")` accepts a palette name as well as a list of colours.
- **Colormaps**
  - `kx.use(theme, cmap=...)` sets the colormap for continuous colour.
  - The supported matplotlib colormaps are `viridis`, `magma`, `plasma`, `inferno`, `cividis`, `turbo`, `twilight`, `coolwarm`, `berlin`, `managua` and `vanimo`.
  - `kx.cmaps()` lists only the ones the installed matplotlib has. `berlin`, `managua` and `vanimo` need matplotlib 3.10 or newer.
- **Docs**
  - `Example Usage.ipynb`: a detailed walkthrough for the public Kaggle notebook. It loads `kx` from the attached dataset.
  - `kx.grammar()` lists the palettes and colormaps as well as the kinds, themes and flags.

### Changed

- **`paper` theme, reworked for greyscale print:**
  - black, dark grey and mid grey colours, each paired with a linestyle (solid, dashed, dotted, dash-dot)
  - greyscale colormap
  - 300 dpi export with a white background
  - serif font for maths text as well
  - 110 dpi in notebooks instead of 150
- **Palettes keep the theme's other cycled properties:** they replace only the colours, so `paper` + `okabe` keeps `paper`'s linestyles.
- **`scatter` point size follows the theme's `lines.markersize`.** Points are bigger on `poster` and smaller on `science`. `dark` and `light` look the same as before.
- **Preview images:** each theme's preview is drawn at twice that theme's own figure size instead of a fixed 12×6 in, so `talk` and `poster` previews no longer overlap.
- **`previews/demo.ipynb`:** cut down to a short demo of each kind and theme. The full walkthrough is now `Example Usage.ipynb`.
- **Strict errors** also cover:
  - `stack` or `norm` on a kind that doesn't support them
  - `band` without `z`
  - `area-norm` with only one series

## [0.0.1] - 2026-10-07

### Added

- `kx.plot` with the kinds `line`, `scatter`, `bar` and `hist`
- the flags `grid`, `leg`, `logx`, `logy` and `tight`
- the themes `dark`, `light` and `paper`
- `kx.use`, `kx.show`, `kx.source`, `kx.grammar`, `kx.load` and the demo CSVs
- a workflow that publishes the dataset to Kaggle

[Unreleased]: https://github.com/vhrabar/kx-plot/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/vhrabar/kx-plot/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/vhrabar/kx-plot/releases/tag/v0.0.1
