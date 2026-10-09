# kx-plot

One-line matplotlib plots and themes for notebooks and scripts.

`kx` is a small, plain-Python package with `.mplstyle` themes, palettes and colourmaps. It needs nothing beyond
matplotlib, numpy and pandas and works offline, so it also runs in Kaggle competition notebooks.

![dark theme](https://raw.githubusercontent.com/vhrabar/kx-plot/main/previews/dark.png)

## Install

```bash
pip install kx-plot
```

```python
import kx; kx.use('dark')
```

### Kaggle

With internet off (competition notebooks), attach the dataset instead (**Add Input → Datasets → `vhrabar/kx-plot`**), then:

```python
import sys; sys.path.append('/kaggle/input/datasets/vhrabar/kx-plot')
import kx; kx.use('dark')
```

## Usage

```python
kx.use('light', palette='okabe', cmap='cividis')   # notebook default: theme, palette, colormap
kx.plot(x, y, z, 'scatter-grid-leg')               # spec: kind-theme-flag-...
kx.plot(x, y, 'bar-paper')                         # a theme in the spec applies to this plot only
```

| Token | Values                                                              |
|-------|---------------------------------------------------------------------|
| kind  | `line` `step` `area` `band` `scatter` `bar` `barh` `hist`           |
| theme | `dark` `light` `paper` `science` `talk` `poster` `thesis`           |
| flags | `grid` `leg` `logx` `logy` `tight`, plus `stack` `norm` (see below) |

`stack` works with `area`, `bar` and `barh`; `norm` (100% stack) with `area`.

Unknown tokens raise an error instead of being guessed. Everything is inspectable:
`kx.grammar()`, `kx.grammar('area')`, `kx.show('dark')`, `kx.source('scatter')`.

rcParams can be overridden in `kx.use` with `__` for dots: `kx.use('dark', figure__figsize=(8, 4))`.

## Palettes

Palettes for `kx.use(theme, palette=...)`, they swap only the colours; a theme's
other cycled properties (such as `paper`'s linestyles) stay.

| Name                                     | Source             |
|------------------------------------------|--------------------|
| `okabe`                                  | Okabe & Ito (2008) |
| `tolbright` `tolvibrant` `tolhc` `tolmc` | Paul Tol           |
| `petroff6` `petroff8` `petroff10`        | Petroff (2021)     |
| `tab10` `tableaucb`                      | Tableau            |
| `set2` `dark2`                           | ColorBrewer        |
| `ibm`                                    | IBM Design Colors  |

`kx.palette('okabe')` returns the hex codes. A list of colours works too: `palette=['#264653', '#e9c46a']`.

## Colourmaps

Colourmaps for `kx.use(theme, cmap=...)` colour continuous values, such as a numeric `z` in `scatter`.
Without `cmap`, the theme's own default applies.

| Name                                           | Type                             |
|------------------------------------------------|----------------------------------|
| `viridis` `magma` `plasma` `inferno` `cividis` | Sequential, perceptually uniform |
| `turbo`                                        | Sequential, rainbow              |
| `coolwarm`                                     | Diverging                        |
| `berlin` `managua` `vanimo`                    | Diverging, dark centre           |
| `twilight`                                     | Cyclic, for angles and phases    |

`kx.cmaps()` lists the ones that are available in the installed matplotlib as those implemented in matplotlib 3.10 or newer
are not vendored.


## License

Released under the MIT License. See [`LICENSE`](https://github.com/vhrabar/kx-plot/blob/main/LICENSE).

Copyright © 2026 Vedran Hrabar

Vendored palettes keep their own licences; see [`kx/styles/palettes/LICENCES.md`](https://github.com/vhrabar/kx-plot/blob/main/kx/styles/palettes/LICENCES.md).
