# goga dependency policy

For every contributor of `goga-tool-basic-build`: how this package depends on
the goga platform while staying importable in environments where goga is not
installed. The package is a goga hook tool — it extends the platform, it never
imports it at runtime.

## The policy

1. Runtime dependencies stay empty. Never add `goga` to `[project.dependencies]`
   — installing this tool must not pull the platform.
2. `goga>=2.0` lives only in the `test` extra of `pyproject.toml`, alongside
   the test tooling. `2.0` is the first line with the configuration amendment
   domain — the extension point this tool subscribes to.
3. Runtime import of goga is forbidden. Platform types (`HookRegistrar`,
   `ConfigAmendment`) are referenced under `if TYPE_CHECKING:` only, with
   `from __future__ import annotations` at the module top.
4. The package facade stays import-clean with or without goga: a facade that
   fails to import is fatal to every goga command that enumerates tool
   packages. `python -c "import goga_tool_basic_build"` must succeed in a bare
   environment.
5. Tests run against duck-typed stubs of the platform surfaces, not against
   the real goga objects; the test-extra goga pins the platform version the
   stubs mirror and keeps the parity check available.

## Why

A tool package is enumerated and imported by goga at every hook checkpoint;
meanwhile the same package must install cleanly into any environment a
consumer uses. The only import-safe direction is: the platform imports the
tool, never the reverse.
