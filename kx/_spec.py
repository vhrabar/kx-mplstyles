"""Spec grammar (kind-theme-flag-flag-...) and the registry of kinds."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ._theme import styles

COMMON_FLAGS = {"grid", "leg", "logx", "logy", "tight"}     # handled by kx.plot for every kind


@dataclass(frozen=True)
class Kind:
    """A plot kind: draw(ax, x, y, z, flags) plus what kx.plot checks before drawing."""
    name: str
    draw: Callable[..., None]
    flags: frozenset[str]                       # kind-specific flags, on top of COMMON_FLAGS
    needs_y: bool
    check: Callable[[Any, Any, set[str]], None] | None     # check(y, z, flags) raises on bad input
    takes_by: bool = False                      # draw also gets by= (group labels for x)


KINDS: dict[str, Kind] = {}


def kind(name: str, flags: tuple[str, ...] = (), needs_y: bool = True,
         check: Callable[[Any, Any, set[str]], None] | None = None, takes_by: bool = False) -> Callable:
    """Decorator that registers a draw function as kind `name`."""
    def register(draw: Callable[..., None]) -> Callable[..., None]:
        if name in KINDS or name in COMMON_FLAGS or "-" in name:
            raise ValueError(f"kind name {name!r} is taken or has a '-'")
        KINDS[name] = Kind(name, draw, frozenset(flags), needs_y, check, takes_by)
        return draw
    return register


def all_flags() -> set[str]:
    """Common flags and every kind-specific flag."""
    return COMMON_FLAGS.union(*(k.flags for k in KINDS.values()))


def parse(spec: str) -> tuple[str, str | None, set[str]]:
    """Split 'kind-theme-flag-...' into (kind, theme, flags). Strict: no guessing."""
    toks = spec.split("-")
    themes, flags = set(styles()), all_flags()
    unknown = [t for t in toks if t not in KINDS.keys() | flags | themes]
    if unknown:
        raise ValueError(f"unknown tokens: {unknown}. Run kx.grammar() to see valid ones.")
    kinds = [t for t in toks if t in KINDS]
    picked = [t for t in toks if t in themes]
    if len(kinds) > 1:
        raise ValueError(f"spec {spec!r} has more than one kind: {kinds}")
    if len(picked) > 1:
        raise ValueError(f"spec {spec!r} has more than one theme: {picked}")
    kind = (kinds or ["line"])[0]
    for flag in sorted(set(toks) & (flags - COMMON_FLAGS - KINDS[kind].flags)):
        owners = sorted(k.name for k in KINDS.values() if flag in k.flags)
        raise ValueError(f"flag {flag!r} only works with kind {owners}, not {kind!r}")
    return kind, (picked or [None])[0], set(toks) & flags
