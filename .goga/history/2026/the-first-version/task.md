# Implement goga-tool-basic-build — the basic review profile hook tool

## Current State

The repository is the pip package scaffold of `goga-tool-basic-build` (the project
scaffold, no product code yet):

- `pyproject.toml` is in place: setuptools + setuptools-scm, the `0.0.x` version
  line, empty runtime dependencies, a `test` extra with `pytest`, `pytest-cov`,
  `pytest-mock`, `ruff` — and no `goga` entry yet.
- `goga_tool_basic_build/__init__.py` is empty; no modules, hooks, or tests exist.
- `goga schema` is empty — the project has no cells; the architecture will be
  designed by the prototype pipeline from this document.
- `README.md` is a stub and the mkdocs navigation is empty — deliberate (out of
  scope per the ADR).
- The normative pattern is studied in full: the installed sibling
  `goga-tool-simple-build` 0.0.1 — a hook-only package with a facade re-exporting
  its contract API (`__init__.py`), a `registration.py` holding the single
  `config/amend_config` subscription, conflict guards raising `ValueError`
  without values, and platform types referenced under `TYPE_CHECKING` only.
- The platform contract is grounded in the synced usages: `config/amend_config`
  is a hard action delivering a read-and-amend view; `set` applies only where
  the authored configuration is silent; the deterministic merge owns
  authored-wins; values never appear in output.
- `.goga/usages/cooks/goga-dependency.md` was created during task formulation
  (the goga dependency policy recipe).

## Description

Implement the `goga-tool-basic-build` package — a hook-only goga tool that gives
every config-consuming run of a project the basic review profile, by mirroring
`goga-tool-simple-build` (the normative pattern per the ADR):

1. **Registration module** (`registration.py`): `register_hooks(hooks)`
   subscribes the tool's single hook (proposed name `review_presets`) to the
   `config / amend_config` address — the only subscription of the tool.
2. **The hook** (`review_presets(context)`), a pure function over the delivered
   read-and-amend view:
   - **Conflict — strategy:** an authored `build.review.strategy` that is present
     and not `medium` raises `ValueError`; the message names the path and the
     resolution, never the authored value.
   - **Conflict — `additional`:** an authored section `build.review.additional`
     with any contents — including an empty mapping — raises `ValueError` naming
     the path `build.review.additional`; an absent or YAML-null section is not a
     conflict.
   - **Fixed check order:** the strategy conflict is checked first; when both
     conflicts are present, the strategy one is reported (deterministic).
   - **Presets:** two unconditional apply-where-silent amendments —
     `build.review.strategy` set to `medium`, `build.review.max_iterations` set
     to `5`. Authored-wins is owned by the platform merge layer and is never
     re-derived inside the hook; absent intermediate branches materialize on
     their own.
   - Platform types (`HookRegistrar`, `ConfigAmendment`) are referenced under
     `TYPE_CHECKING` only — no runtime import of goga.
3. **Package facade** (`__init__.py`): re-exports the contract API through
   `__all__`; stays import-clean with or without goga installed (a facade that
   fails to import is fatal to every goga command).
4. **`pyproject.toml`:** add `goga>=2.0` to the `test` extra (runtime
   dependencies stay empty).
5. **Unit tests on duck-typed stubs** (deliberately no platform integration or
   CLI end-to-end tests — ADR decision).

### Target API examples (approved)

The facade as the platform sees it:

```python
from goga_tool_basic_build import register_hooks  # import-clean without goga

def register_hooks(hooks: HookRegistrar):
    hooks.subscribe("config", "amend_config", "review_presets", review_presets)
```

The hook contract in use form:

```python
review_presets(context)  # reads authored leaves, guards conflicts, buffers two sets
context.set("build.review.strategy", "medium")
context.set("build.review.max_iterations", 5)
```

Consumer-visible effect (authored file silent at the review leaves):

```yaml
# authored .goga/config.yml          # effective in every config-consuming run
language: python                     # build:
                                     #   review:
                                     #     strategy: medium
                                     #     max_iterations: 5
```

## Scope

**In scope:**

- `goga_tool_basic_build/registration.py` — `register_hooks` and the single
  review-presets hook with the two conflict guards and the two `set`
  amendments.
- `goga_tool_basic_build/__init__.py` — the re-exporting facade.
- `pyproject.toml` — `goga>=2.0` added to the `test` extra.
- Unit tests on duck-typed stubs covering: preset application, authored-wins
  silence (including the empty/whitespace strategy reading as unset), the
  strategy conflict, the `additional` conflict (including `additional: {}`),
  the fixed check order, the exact two-leaf write footprint, and the
  facade/registration contract.
- The goga dependency policy recipe `.goga/usages/cooks/goga-dependency.md`
  (already created during task formulation).

**Out of scope:**

- Maintainer-facing documentation: `README.md` stays a stub, the mkdocs
  navigation stays empty — a later documentation task.
- Any CLI command of the tool (it is hook-shaped).
- Any change to the goga platform itself.
- Dogfooding: this repository's own `.goga/config.yml` is not switched to the
  tool.
- Integration tests against the real platform merge or CLI end-to-end runs.
- Anything beyond the two review leaves: agent presence, review roles,
  tasks-pass (`build` root) settings, environment values, strategy whitelist
  enforcement, any mapping into `build.review.additional.*`.
- Cell/CODEMANIFEST design — owned by the prototype pipeline that consumes this
  document.

## Acceptance Criteria

- `python -c "import goga_tool_basic_build"` succeeds in an environment without
  goga (import-clean facade; runtime deps empty).
- `register_hooks` subscribes exactly one hook to `config / amend_config` with a
  hook name unique per tool per address; no other domain action is subscribed.
- On a stubbed silent configuration the hook buffers exactly two amendments:
  `build.review.strategy = "medium"` and `build.review.max_iterations = 5` —
  unconditionally, including when intermediate branches are absent.
- An authored `build.review.max_iterations` produces no error and no warning;
  the authored `strategy: medium` is accepted silently (stub-level: the hook
  still buffers both `set` calls — authored-wins belongs to the merge layer).
- An authored empty or whitespace-only `build.review.strategy` counts as unset
  (the platform's value normalization): no conflict is raised and the strategy
  preset is still buffered.
- An authored strategy other than `medium` (including the valid `short` and
  `full`) makes the hook raise `ValueError` whose message names
  `build.review.strategy` and never contains the authored value.
- An authored `build.review.additional` of any shape — including `{}` — makes
  the hook raise `ValueError` naming `build.review.additional`; absent or
  YAML-null `additional` does not.
- With both conflicts present, the raised error is the strategy one (fixed
  order, deterministic).
- The hook contributes nothing to `build.review.additional` and to any leaf
  beyond the two presets (exact write footprint).
- `pyproject.toml` test extra contains `goga>=2.0`; runtime `dependencies` stay
  empty.
- `pytest tests/ -x` and `ruff check goga_tool_basic_build/` pass in a
  virtualenv.

## Stack

- **Frameworks:** none — a pure-Python hook-only package.
- **Libraries:** none at runtime; `goga>=2.0` in the `test` extra only (types
  under `TYPE_CHECKING`); pytest / pytest-cov / pytest-mock / ruff as test
  tooling.
- **Infrastructure:** none; distribution as the pip package
  `goga-tool-basic-build` via setuptools + setuptools-scm (`0.0.x` line),
  publishing stays a manual workflow-dispatch action.

## External Dependencies

| Component | Usage file | Status |
|-----------|------------|--------|
| goga platform — config amendment contract | `.goga/usages/github/goga/config/registering-hooks.md` | existing (synced) |
| goga platform — hook registration contract | `.goga/usages/github/goga/hooks/registering-hooks.md` | existing (synced) |
| goga platform — amendment checkpoint delivery | `.goga/usages/github/goga/config/hooks/checkpoints.md` | existing (synced) |
| goga dependency policy | `.goga/usages/cooks/goga-dependency.md` | created |

Synced usage files are managed by `goga usages sync` — reference them read-only, never create or update them in the task.

## Risks and Constraints

- **Value secrecy:** no configuration value may ever appear in an error message,
  a summary, or informational output — paths only.
- **Hard-action semantics:** the first failing tool stops the command and its
  whole contribution is discarded; the hook must fail only through `ValueError`
  on the two conflicts.
- **Import safety:** the runtime import of goga is forbidden; a facade import
  failure is fatal to goga commands.
- **Compatibility:** the tool targets goga 2.0.x — the first line with the
  configuration amendment domain; strategy values are fixed by the platform
  consumer (`full` | `medium` | `short`).
- **Testing boundary:** unit tests on duck-typed stubs only — do not upgrade the
  suite to platform integration without a new decision (ADR).
- **Coexistence caveat:** tools are mutually blind; alongside another
  review-preset tool the strategy becomes enumeration-dependent — a documented
  adoption condition, not engineered around.
- **Usages drift note:** the `github/goga` freshness check (`goga usages
  status`) failed in the sandboxed environment (network); the local synced
  state is complete and was used.

## Scope Estimate

Single task — no decomposition. One registration module plus a facade, one
subscription, one hook; all parts deliver together and have no standalone value.
The document stays on the current topic (`2026/the-first-version`) and is the
input for `goga-prototype`.

## Existing Architecture

No cells exist (`goga schema` is empty); no integration points inside the
project. The package itself — one cell with a facade and a registration module —
will be designed by the prototype pipeline from this document, following the
sibling `goga-tool-simple-build` as the normative shape.

## Notes

- Input artifacts: the PRD (`.goga/history/2026/the-first-version/prd.md`) pins
  the behavior; the ADR (`.goga/history/2026/the-first-version/adr.md`) pins the
  implementation shape, the testing depth, and the dependency policy.
- The hook name `review_presets` is a proposal — final naming belongs to the
  prototype stage.
- The code-example set in the Description was approved by the user during
  formulation.
- Maintainer documentation is deliberately deferred; no dogfooding.
