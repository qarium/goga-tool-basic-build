# Implement goga-tool-basic-build by mirroring goga-tool-simple-build

The tool's behavior is fully pinned by the PRD (the two review presets, the two hard
conflicts, authored-wins, value secrecy, zero footprint), so the decision recorded here
is the implementation shape: `goga-tool-simple-build` is the normative pattern, to be
replicated — a hook-only package with no CLI of its own, a facade that re-exports the
registration API and stays import-clean in environments without goga, a single
subscription to the platform's `config/amend_config` checkpoint, unconditional
apply-where-silent `set` amendments (authored-wins is owned by the platform merge and
is never re-derived inside the hook), and conflict checks that raise `ValueError` with
messages naming the path and never a value. The sibling is a proven implementation of
the same product pattern, and the PRD anchors the product to it.

## Considered Options

- **Testing depth — unit tests on duck-typed stubs only.** Integration tests against
  the real platform merge (`merge_config_amendments`) and CLI end-to-end runs were
  considered and rejected: the hook is a thin, pure function over a small read-and-
  amend view, and the merge and CLI behavior are owned and covered by the platform
  itself. Deliberate: do not "upgrade" the suite to platform integration without a
  new decision.
- **goga as a `test`-extra dependency only.** `goga>=2.0` is added to the `test`
  extra (the sibling's policy) while runtime dependencies stay empty: the runtime
  import of goga is forbidden, platform types are referenced under `TYPE_CHECKING`
  only. The policy is written as a hand-made recipe at
  `.goga/usages/cooks/goga-dependency.md` (the `cooks/` subtree is never touched by
  `goga usages sync`) — creating that recipe is part of this task's deliverables.

## Consequences

- Maintainer-facing documentation is out of scope for this task: `README.md` stays a
  stub and the mkdocs navigation stays empty; both are left to a later documentation
  task.
- The repository ships the package itself (the root `pyproject.toml` already names
  `goga-tool-basic-build`); versioning follows the `0.0.x` line via setuptools-scm,
  and publishing stays a manual workflow-dispatch action.
- No dogfooding: this repository's own `.goga/config.yml` is not switched to the new
  tool — the package ships for external consumption only.
