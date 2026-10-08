"""
Render previews/<theme>.png for every theme: all four kinds on the bundled demo CSVs.
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

import kx  # noqa: E402


def render(theme: str, out_dir: str) -> str:
    """Draw a 2x2 grid (line, scatter, bar, hist) in `theme` and save it as PNG."""
    waves, cloud, monthly, dists = (kx.load(n) for n in ("waves", "cloud", "monthly", "dists"))
    kx.use(theme)
    w, h = plt.rcParams["figure.figsize"]
    fig, axs = plt.subplots(2, 2, figsize=(2 * w, 2 * h))
    a = iter(axs.flat)
    kx.plot(waves.x, waves.y, waves.z, "line-leg", title="line", ax=next(a))
    kx.plot(cloud.x, cloud.y, cloud.z, "scatter", title="scatter", ax=next(a))
    kx.plot(monthly.month, monthly.y2025, monthly.y2026, "bar-leg", title="bar", ax=next(a))
    kx.plot(dists.normal, dists.skewed, dists.bimodal, "hist-leg", title="hist", ax=next(a))
    fig.suptitle(theme)
    fig.tight_layout()
    path = os.path.join(out_dir, f"{theme}.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> None:
    out_dir = os.path.join(_root, "previews")
    os.makedirs(out_dir, exist_ok=True)
    for theme in kx.styles():
        print(render(theme, out_dir))


if __name__ == "__main__":
    main()
