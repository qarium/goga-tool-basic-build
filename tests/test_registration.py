"""Tests for registration: the single subscription and the amendment hook."""

import re

import goga_tool_basic_build
import pytest
from goga_tool_basic_build.registration import register_hooks, review_presets

from .conftest import StubSection, make_amendment


def test_register_hooks_subscribes_single_config_amend_hook(registrar):
    """register_hooks makes exactly one subscription at config / amend_config."""
    register_hooks(registrar)

    assert len(registrar.calls) == 1
    assert registrar.calls[0][:3] == ("config", "amend_config", "review_presets")
    assert registrar.calls[0][3] is goga_tool_basic_build.registration.review_presets


def test_review_presets_buffers_both_presets_on_absent_build():
    """An absent build branch does not block the two preset buffers."""
    amendment = make_amendment(build_present=False)

    review_presets(amendment)

    assert amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
    assert amendment.forces == []


def test_review_presets_buffers_both_presets_on_absent_review():
    """An absent review branch behaves identically to the absent build branch."""
    amendment = make_amendment(review_present=False, build_present=True)

    review_presets(amendment)

    assert amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
    assert amendment.forces == []


def test_review_presets_accepts_authored_medium_strategy():
    """An authored medium strategy is accepted silently and both presets still buffer."""
    amendment = make_amendment(strategy="medium")

    review_presets(amendment)

    assert amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]


def test_review_presets_buffers_presets_with_authored_max_iterations():
    """An authored max_iterations never conflicts and never suppresses the preset."""
    amendment = make_amendment(max_iterations=8)

    review_presets(amendment)

    assert ("build.review.max_iterations", 5) in amendment.sets
    assert amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]


def test_review_presets_write_footprint_is_exactly_two_set_amendments():
    """The write footprint is exactly two set amendments on the review leaves."""
    amendment = make_amendment()

    review_presets(amendment)

    assert len(amendment.sets) == 2
    assert len(amendment.forces) == 0
    assert sorted(path for path, _ in amendment.sets) == ["build.review.max_iterations", "build.review.strategy"]


@pytest.mark.parametrize("value", ["short", "full", "quick"])
def test_review_presets_raises_on_non_medium_strategy(value):
    """A non-medium authored strategy stops the hook before any buffering."""
    amendment = make_amendment(strategy=value)

    with pytest.raises(ValueError, match=re.escape("build.review.strategy")):
        review_presets(amendment)

    assert amendment.sets == []


def test_review_presets_error_names_path_and_resolution_without_value():
    """The strategy error names the path and the resolution - never the value."""
    amendment = make_amendment(strategy="full")

    with pytest.raises(
        ValueError, match=re.escape("refused the authored configuration at build.review.strategy")
    ) as excinfo:
        review_presets(amendment)

    message = str(excinfo.value)
    assert "build.review.strategy" in message
    assert "remove the authored strategy or uninstall the tool" in message
    assert "full" not in message


def test_review_presets_raises_on_populated_additional():
    """A populated additional section stops the hook before any buffering."""
    amendment = make_amendment(additional=StubSection(agent="codex", patience=3, max_iterations=15))

    with pytest.raises(ValueError, match=re.escape("build.review.additional")):
        review_presets(amendment)

    assert amendment.sets == []


def test_review_presets_raises_on_empty_additional_mapping():
    """A present but empty additional mapping still conflicts."""
    amendment = make_amendment(additional=StubSection())

    with pytest.raises(ValueError, match=re.escape("build.review.additional")):
        review_presets(amendment)

    assert amendment.sets == []


def test_review_presets_reports_strategy_conflict_first():
    """When both conflicts are present the strategy one is reported."""
    amendment = make_amendment(strategy="short", additional=StubSection())

    with pytest.raises(ValueError, match=re.escape("build.review.strategy")) as excinfo:
        review_presets(amendment)

    assert "build.review.additional" not in str(excinfo.value)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_review_presets_treats_blank_strategy_as_unset(value):
    """A blank strategy counts as unset - no conflict, both presets buffer."""
    amendment = make_amendment(strategy=value)

    review_presets(amendment)

    assert amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]


@pytest.mark.parametrize("value", [42, True])
def test_review_presets_conflicts_on_non_string_strategy(value):
    """A non-string strategy conflicts instead of crashing."""
    amendment = make_amendment(strategy=value)

    with pytest.raises(ValueError, match=re.escape("build.review.strategy")):
        review_presets(amendment)

    assert amendment.sets == []


def test_review_presets_skips_conflict_when_additional_absent_or_null():
    """An absent or null additional section is not a conflict."""
    amendment = make_amendment(additional=None)

    review_presets(amendment)

    assert ("build.review.strategy", "medium") in amendment.sets
