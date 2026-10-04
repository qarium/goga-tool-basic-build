"""The registration module: the tool's single subscription and single amendment hook."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goga.config.hooks import ConfigAmendment
    from goga.hooks.tools.registration import HookRegistrar

_STRATEGY_PATH = "build.review.strategy"
_MAX_ITERATIONS_PATH = "build.review.max_iterations"
_STRATEGY_PRESET = "medium"
_MAX_ITERATIONS_PRESET = 5


def register_hooks(hooks: HookRegistrar) -> None:
    """Subscribe the tool's single hook to the platform's configuration amendment action.

    Makes exactly one subscription: domain "config", action "amend_config", hook name
    "review_presets", callable ``review_presets`` - the only subscription of the tool.

    Args:
        hooks: The platform subscription surface delivered by goga when a command first
            reaches a hook checkpoint.
    """
    hooks.subscribe("config", "amend_config", "review_presets", review_presets)


def review_presets(context: ConfigAmendment) -> None:
    """Guard the two basic-profile conflicts, then buffer the two review presets.

    A pure function over the delivered read-and-amend view: reads the authored
    ``build.review`` leaves, refuses the two authored-configuration conflicts in a fixed
    order (strategy first, then additional), and buffers two set amendments - the
    strategy preset ``medium`` and the max_iterations preset ``5`` - unconditionally.

    Args:
        context: The read-and-amend view over the authored configuration.

    Raises:
        ValueError: The authored build.review.strategy leaf is present and not
            ``medium`` - remove the authored strategy or uninstall the tool.
        ValueError: The authored build.review.additional section is present, including
            as an empty mapping - remove the additional section or uninstall the tool.
    """
    build = context.config.build
    review = build.review if build is not None else None

    strategy = review.strategy if review is not None else None
    normalized = strategy.strip() if isinstance(strategy, str) else strategy

    if normalized is not None and normalized not in ("", _STRATEGY_PRESET):
        raise ValueError(
            f"refused the authored configuration at {_STRATEGY_PATH} - "
            "remove the authored strategy or uninstall the tool"
        )

    additional = review.additional if review is not None else None

    if additional is not None:
        raise ValueError(
            "refused the authored configuration at build.review.additional - "
            "remove the additional section or uninstall the tool"
        )

    context.set(_STRATEGY_PATH, _STRATEGY_PRESET)
    context.set(_MAX_ITERATIONS_PATH, _MAX_ITERATIONS_PRESET)
