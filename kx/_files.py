"""Files that ship next to the package: styles/, styles/palettes/, data/."""
import glob
import os

# repo (or Kaggle dataset) root; read as _files.root at call time so tests can point it elsewhere
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(*parts: str) -> str:
    """Path under the root."""
    return os.path.join(root, *parts)


def names(folder: str, ext: str) -> list[str]:
    """Sorted base names of the <folder>/*<ext> files under the root."""
    return sorted(os.path.basename(p)[:-len(ext)] for p in glob.glob(path(folder, f"*{ext}")))
