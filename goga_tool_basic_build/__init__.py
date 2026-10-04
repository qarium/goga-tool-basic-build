"""The goga-tool-basic-build package facade: the contract API of the basic review profile tool."""

from .registration import register_hooks, review_presets

__all__ = ["register_hooks", "review_presets"]
