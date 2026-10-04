"""Integration tests: the registration to amendment wiring on duck-typed stubs."""

import re

import pytest
from goga_tool_basic_build import register_hooks

from .conftest import make_amendment


def test_platform_flow_subscribes_then_hook_buffers_presets(registrar):
    """The subscribed callable is the hook that buffers, invoked as the platform invokes it."""
    register_hooks(registrar)

    assert len(registrar.calls) == 1

    domain, action, name, hook = registrar.calls[0]
    assert (domain, action, name) == ("config", "amend_config", "review_presets")

    ctx = make_amendment()
    hook(context=ctx)

    assert ctx.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
    assert ctx.forces == []


def test_platform_flow_conflict_stops_contribution_before_buffering(registrar):
    """A strategy conflict raised through the wiring discards the whole contribution."""
    register_hooks(registrar)

    assert len(registrar.calls) == 1

    hook = registrar.calls[0][3]

    ctx = make_amendment(strategy="short")

    with pytest.raises(ValueError, match=re.escape("build.review.strategy")):
        hook(context=ctx)

    assert ctx.sets == []
