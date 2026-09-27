"""Adapter registry for tree-sitter language support."""

from __future__ import annotations

from conventionguardian.adapters.base import (
    AdapterContext,
    adapters_available,
    available_languages,
)


def get_adapters(ctx: AdapterContext) -> list:
    """Instantiate every available adapter for the given context."""
    adapters = []
    from conventionguardian.adapters.golang import GoAdapter
    from conventionguardian.adapters.jsts import JsTsAdapter
    from conventionguardian.adapters.rust import RustAdapter

    for cls in (JsTsAdapter, GoAdapter, RustAdapter):
        ad = cls.try_new(ctx)
        if ad is not None:
            adapters.append(ad)
    return adapters


__all__ = [
    "AdapterContext",
    "adapters_available",
    "available_languages",
    "get_adapters",
]
