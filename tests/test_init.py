"""Tests for the package facade: the contract API re-export."""

import subprocess
import sys
from pathlib import Path

import goga_tool_basic_build

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_facade_reexports_contract_api():
    """The facade re-exports both contract routines with identities preserved."""
    assert goga_tool_basic_build.register_hooks is goga_tool_basic_build.registration.register_hooks
    assert goga_tool_basic_build.review_presets is goga_tool_basic_build.registration.review_presets
    assert goga_tool_basic_build.__all__ == ["register_hooks", "review_presets"]
    assert callable(goga_tool_basic_build.register_hooks)
    assert callable(goga_tool_basic_build.review_presets)


def test_facade_import_requires_no_goga():
    """Importing the facade never pulls goga into sys.modules at runtime."""
    code = "import goga_tool_basic_build; import sys; sys.exit(0 if 'goga' not in sys.modules else 1)"

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
