# Plan: `the-first-version` — basic review profile tool, first implementation

## Purpose

Implement the contract materialized in `goga_tool_basic_build/CODEMANIFEST` — the first
version of the `goga-tool-basic-build` package: a hook-only goga tool that subscribes one
`config / amend_config` hook (`review_presets`) guarding two authored-configuration
conflicts and buffering two apply-where-silent review presets.

After implementation the package provides:

- `goga_tool_basic_build/registration.py` with both contract routines
  (`register_hooks`, `review_presets`) per `location:`;
- an import-clean facade `goga_tool_basic_build/__init__.py` re-exporting exactly the
  contract API (currently deleted in git — must be recreated);
- a complete test stack (16 designed tests + 2 stub-only integration tests) on
  duck-typed platform stubs — no goga objects, no mocks;
- `pyproject.toml` with `goga>=2.0` pinned in the `test` extra only
  (`[project.dependencies]` stays `[]`).

The most important gaps between contract and code: both routines are missing
(`registration.py` does not exist), the facade is deleted, the entire test stack is
missing, and the test extra lacks the `goga` parity pin.

Implementation strategy: one infrastructure task (environment + packaging + shared test
scaffolding), one TDD coding task for the module and facade (both routines share
`location: registration.py` and are wired together — one subscription referencing one
callable), one integration task for the registration → amendment wiring on stubs. The
workflow inside every coding task is structured around the **REPL cycle** (see Mandatory
Rules M4): evaluate interactively against stubs → migrate verified code into the source
file → re-evaluate from the migrated file in a fresh subprocess.

Every platform fact used below was verified against the installed goga 2.0.2 during the
design stage (source inspection + live simulation, 8/8 scenarios matched).

## Context

### Contract Surface

Single cell: `goga_tool_basic_build`. No `Imports`. Two Routine types. Four file-form
`Usages` (`conventions`, `goga-dependency`, `config-amend`, `hook-registration`), all
referenced in annotations. Footer: `Author: Goga`, `CreatedAt: 04/10/26`.
`goga lint`: cells 1, errors 0.

**Entity: `register_hooks`**
- Type: Routine (module-level function; snake_case per Python cell rules)
- Signature: `register_hooks(hooks: HookRegistrar)` — returns nothing (omit output)
- Declared `location`: `registration.py` (flat, same level as `CODEMANIFEST`)
- Facade obligation: importable from `goga_tool_basic_build` (via `__all__`)
- Mutations: none
- Imported dependencies: none at runtime — `HookRegistrar` is a `TYPE_CHECKING`-only
  reference (`goga-dependency` policy #3)
- Annotation cascade (global → type level):
  - Global: use `conventions` for code and tests; the cell is hook-only — no command of
    its own; use `goga-dependency` for the platform dependency policy; use
    `config-amend` for the amendment-view contract; **value secrecy** — any message the
    cell produces names configuration paths at most, never values; **the tool is silent
    by design** — no stdout/stderr, no logging.
  - Type level (verbatim from CODEMANIFEST):
    > Subscribe the tool's single hook to the platform's configuration amendment
    > action — the only subscription of the tool.
    >
    > `hooks`: the platform subscription surface delivered by goga when a command first
    > reaches a hook checkpoint; use `hook-registration` for its contract.
    >
    > Algorithm:
    > 1. Subscribe one hook: domain "config", action "amend_config", hook name
    >    "review_presets", callable `review_presets`
    >
    > Requirements:
    > - Exactly one subscription; no other domain action is subscribed
    >
    > Constraints:
    > - Do not import goga at runtime — follow `goga-dependency`
    > - Use `conventions` for code style and docstrings
- Semantic requirements: one `hooks.subscribe("config", "amend_config", "review_presets",
  review_presets)` call — four positional arguments (domain, action, name, callable);
  returns `None`; never names its own tool (the platform assigns tool identity from the
  package name).

**Entity: `review_presets`**
- Type: Routine (module-level function; snake_case per Python cell rules)
- Signature: `review_presets(context: ConfigAmendment)` — returns nothing
- Declared `location`: `registration.py` (same file as `register_hooks`)
- Facade obligation: importable from `goga_tool_basic_build` (via `__all__`)
- Mutations: none
- Imported dependencies: none at runtime — `ConfigAmendment` is a `TYPE_CHECKING`-only
  reference; the delivered `context` is consumed by duck typing only
- Annotation cascade (global → type level):
  - Global: as above (value secrecy; silence; `conventions`; `goga-dependency`).
  - Type level (verbatim from CODEMANIFEST):
    > The tool's single amendment hook: guard the two basic-profile conflicts in a fixed
    > order, then buffer the two review presets. A pure function over the delivered
    > read-and-amend view — no I/O, no state.
    >
    > `context`: the read-and-amend view over the authored configuration; use
    > `config-amend` for its read surface and set semantics.
    >
    > Algorithm:
    > 1. Read the authored build.review.strategy leaf: if it is present and not the
    >    value medium, raise ValueError naming the path build.review.strategy and the
    >    resolution (remove the authored strategy or uninstall the tool)
    > 2. Read the authored build.review.additional section: if it is present with any
    >    contents — including an empty mapping — raise ValueError naming the path
    >    build.review.additional and the resolution (remove the section or uninstall the
    >    tool); an absent or null section is not a conflict
    > 3. Buffer a set amendment of build.review.strategy to medium
    > 4. Buffer a set amendment of build.review.max_iterations to 5
    >
    > Requirements:
    > - An authored strategy that is absent, null, or blank (empty or whitespace-only)
    >   counts as unset — no conflict
    > - Both set amendments are buffered unconditionally, including when the authored
    >   configuration already carries values at those leaves and when intermediate
    >   branches (build, build.review) are absent
    > - The strategy conflict is checked before the additional conflict; when both are
    >   present the strategy one is reported
    > - Error messages name the path and the resolution only
    >
    > Constraints:
    > - Authored-wins belongs to the platform merge layer — never re-derive it inside
    >   the hook
    > - Never use a force amendment; never contribute to build.review.additional or any
    >   leaf beyond the two presets
    > - Fail only through ValueError on the two conflicts
    > - No configuration value may appear in any message
    > - Follow `goga-dependency` for platform type references and `conventions` for code
    >   style

### Re-exports

No DSL re-export blocks (`->Name: {}`) exist in the CODEMANIFEST and there are no
`Imports`. The facade obligation arises from the Python cell rule instead:
`__init__.py` must expose the full contract API through `__all__` — only identifiers in
`__all__` constitute the facade. Exact facade shape (binding, from the design):

```python
"""The goga-tool-basic-build package facade: the contract API of the basic review profile tool."""

from .registration import register_hooks, review_presets

__all__ = ["register_hooks", "review_presets"]
```

### Platform Interaction (verbatim from the design document)

Interaction diagram:

```
                goga platform (external boundary, goga 2.0.x)
                HookRegistry.build_once()
                  │ 1. enumerate goga_tool_* packages
                  │ 2. import goga_tool_basic_build  (facade; goga-free)
                  │ 3. call register_hooks(hooks=HookRegistrar(tool="basic-build"))
                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ cell: goga_tool_basic_build                                       │
│                                                                   │
│   __init__.py (facade) ─── re-export ───► registration.py        │
│                                            │                     │
│      register_hooks(hooks) ────────────────┘                     │
│           │ hooks.subscribe("config", "amend_config",            │
│           │               "review_presets", review_presets)      │
│           ▼                                                       │
│      review_presets(context)   ◄── later, at the config load     │
│           │                        moment of a consuming command │
│           │ 1. read context.config.build.review                  │
│           │ 2. guard strategy conflict   → ValueError (hard)     │
│           │ 3. guard additional conflict → ValueError (hard)     │
│           │ 4. context.set("build.review.strategy", "medium")    │
│           │ 5. context.set("build.review.max_iterations", 5)     │
│           ▼                                                       │
│      per-tool buffer ── commit as one unit ───► platform merge   │
│                                        (authored-wins, summary)  │
└──────────────────────────────────────────────────────────────────┘
```

Data flows:

| # | Scenario | Participating entities | Data passed | Order |
|---|----------|------------------------|-------------|-------|
| 1 | Command reaches first hook checkpoint | platform → facade → `register_hooks` | `hooks: HookRegistrar` (tool-scoped registrar) | facade import → `register_hooks` → one `subscribe` call |
| 2 | Command loads `.goga/config.yml` | platform → `review_presets` | `context`: wrapped `ConfigAmendment` over the read-only authored `ProjectConfig` | guards (strategy, then additional) → two `set` buffers → return |
| 3 | Hook returns | buffer → platform merge | `ToolAmendment(tool, amendments)` — two `PathAmendment(path, intent="set", value)` | merge resolves authored-silence per path → effective config + summary lines |
| 4 | Hook raises | `review_presets` → platform | `ValueError` (path + resolution, no value) | platform wraps: `hook review_presets of tool <tool> failed on config.amend_config: <message>`; command stops; whole contribution discarded |

Entity dependencies:

- `register_hooks` → references `review_presets` (the subscribed callable) — intra-module,
  no import needed beyond co-location in `registration.py`.
- `review_presets` → depends on nothing inside the project; interacts with the delivered
  `context` by duck typing only.
- Platform types `HookRegistrar` / `ConfigAmendment` are **type-checking references
  only** (`goga-dependency` policy #3): `from __future__ import annotations` +
  `if TYPE_CHECKING:` block; zero runtime imports of goga.
- Initialization order: the platform imports the facade first — `__init__.py` must stay
  import-clean so `registration.py` is reachable; `registration.py` executes no
  third-party or goga import at runtime — its only imports are the compile-time aids
  `from __future__ import annotations` and `typing.TYPE_CHECKING` (both stdlib, both
  import-safe in a bare environment).

Verified platform facts (goga 2.0.2 — carried from the design's code stack trace):

- `HookRegistrar.subscribe(self, domain: str, action: str, name: str, hook: Callable[..., object]) -> None`
  — four positional arguments; the address `config / amend_config` is declared with
  `error_class='hard'`.
- The platform calls the facade callback positionally: `callback(registrar)`.
- Hook invocation is `hook(**build_hook_arguments(...))`; `build_hook_arguments` delivers
  **only the declared parameter names** from the offered set `{context, self}`;
  `review_presets` declares exactly `context` → called as `review_presets(context=...)`.
- Loader normalization: an authored blank strategy is already `None` on the real platform
  and a non-empty strategy is stored stripped; absent/YAML-null `additional` parses to
  `None`; a present mapping — including `additional: {}` — parses to an
  `AdditionalReviewConfig` instance. The hook's own blank/strip handling is defensive
  for duck-typed deliveries and never disagrees with the loader.
- Model navigation: `ProjectConfig.build`, `BuildConfig.review`,
  `ReviewConfig.{strategy,max_iterations,additional}` all exist; absent branches are
  `None` — navigation must guard every absent branch.
- Merge: authored-wins (a `set` on a non-silent path is dropped silently) belongs to the
  platform; the hook never re-derives it. Absent intermediate branches materialize at
  COMPOSE time — the hook never pre-materializes anything.
- Hard-failure composition (byte-exact):
  `hook review_presets of tool <tool> failed on config.amend_config: <message>` — the
  hook's message supplies the path and the resolution, the platform supplies tool/action.
- Public import paths for the `TYPE_CHECKING` block:
  `from goga.hooks.tools.registration import HookRegistrar` (not re-exported higher) and
  `from goga.config.hooks import ConfigAmendment` (public facade).

### Usages Context

- **`conventions`** (`.goga/usages/conventions.md`) — mandatory Python rules: 3.10+
  compatibility, relative intra-package imports, Google-style docstrings, blank-line
  block separation, pydantic data-model rules, and the full testing standard (structure,
  naming, mocks policy, venv execution). Relevance: project-wide code and test law; the
  authoritative source of this plan's Mandatory Rules section. The pydantic section does
  not apply (no data models in this cell) and the logging section is overridden by the
  cell contract (silent by design — no logging).
- **`goga-dependency`** (`.goga/usages/cooks/goga-dependency.md`) — the platform
  dependency policy: runtime dependencies empty, `goga>=2.0` only in the `test` extra,
  `TYPE_CHECKING`-only platform references, import-clean facade, tests on duck-typed
  stubs. Relevance: governs `pyproject.toml` edits and the import structure of
  `registration.py`.
- **`config-amend`** (`.goga/usages/github/goga/config/registering-hooks.md`) — the
  `config / amend_config` amendment-view contract: read-and-amend surface, `set`/`force`
  semantics, silence markers, merge rules (authored-wins, force-beats-set, enumeration
  order), hard-action failure treatment, run-output rules. Relevance: normative contract
  of the single checkpoint the tool subscribes to; `review_presets` reads through
  `context.config` and writes two `set` calls on model-known dotted leaf paths; `force`
  is never used.
- **`hook-registration`** (`.goga/usages/github/goga/hooks/registering-hooks.md`) — the
  facade-callback contract: `register_hooks` shape, the four-argument `subscribe`, hook
  signature projection by declared parameter names (`context`, `self`), registration
  timing (never cached — package edits apply from the next run), failure behavior of
  registration. Relevance: defines how the tool's single subscription enters the
  platform.

### Imported Usages

None — the manifest has no `Imports`.

### Local Usages

All three cell-level usage files already exist and were verified current at the design
review; the design plans **no new files**:

- `goga_tool_basic_build/.usages/registration.md` — facade-consumption domain. Status:
  current. Related entities: both routines. Verification only (Task 3).
- `goga_tool_basic_build/.usages/profile.md` — the guarantee / tuning-knob domain.
  Status: current. Related entities: `review_presets`. Verification only (Task 3).
- `goga_tool_basic_build/.usages/conflicts.md` — the two conflicts, fixed order, error
  shape (tool, action, path, resolution; never the value), not-a-conflict list,
  recovery. Status: updated at design review (error example aligned with the byte-exact
  platform composition, ASCII hyphen). Related entities: `review_presets`.
  Verification only (Task 3).

### External Dependencies

- `goga>=2.0` — **test extra only** (parity pin for the platform the stubs mirror);
  forbidden in `[project.dependencies]`.
- `pytest>=8.0`, `pytest-cov>=5.0`, `pytest-mock>=3.10`, `ruff>=0.15.0` — already in the
  `test` extra; pytest runs the stack, ruff lints and formats (project-convention
  toolchain). pytest-mock is not used (pure logic — no mocks).
- No runtime dependencies at all: `[project.dependencies]` stays `[]`.

## Facts

- The cell is a single Python package `goga_tool_basic_build` with `CODEMANIFEST`
  (read-only contract), no `Imports`, two Routines in one `location` (`registration.py`),
  and three existing `.usages/` files.
- `goga lint` reports `cells: 1 errors: 0`; `goga config language` → `python`.
- `goga_tool_basic_build/__init__.py` is currently **deleted** in git (`D` in
  `git status`) — the facade must be recreated with the exact shape above.
- `tests/` does not exist — the entire test stack is new.
- `pyproject.toml`: `dependencies = []`; `test` extra lacks `goga`; ruff configured with
  `target-version = "py310"`, `line-length = 120`, select set `E,W,F,I,N,UP,B,SIM,PL,
  PLR,C4,DTZ,PT,ARG,RUF,PTH,C90`, mccabe `max-complexity = 10`, per-file-ignores for
  `tests/**` (`S101`, `ARG001`, `ARG002`, `PLR2004`, `RUF001`); `[tool.ruff.format]`:
  double quotes, space indent, magic trailing comma, LF; pytest `testpaths = ["tests"]`,
  `addopts = "-v --tb=short"`; coverage source `goga_tool_basic_build`, branch mode.
- Interpreter available: Python 3.12.15 (`/opt/goga/bin/python3`); the code must stay
  compatible with Python 3.10+ (project convention, ruff `py310` target).
- `/opt` is **not writable** in this environment (verified during design review) — the
  sanctioned venv fallback is `$HOME/.venvs/goga-tool-basic-build` (see Mandatory Rules
  M5).
- Error message literals are ASCII-only (hyphen, not em dash) — RUF001-safe under the
  project's `RUF` selection.
- The designed test code (conftest stubs, all 16 tests) was already checked for ruff
  compliance with the project configuration at design review (PT011 `match=` anchors
  present; parametrize forms clean).

## Gap Analysis

- Missing contract entities: `register_hooks` and `review_presets`
  (`goga_tool_basic_build/registration.py` does not exist).
- Missing facade exposure: `goga_tool_basic_build/__init__.py` deleted; nothing re-exports
  the contract API.
- Packaging gap: `goga>=2.0` missing from `[project.optional-dependencies].test`
  (violates `goga-dependency` policy #2 until added).
- Test coverage gaps: 100% — no `tests/` directory, no conftest stubs, no tests for
  either routine or the facade.
- Incorrect `location` placement: none — `registration.py` is flat next to CODEMANIFEST,
  as declared.
- API mismatches / behavioral mismatches: none — there is no prior implementation.
- Existing code that can be reused: `CODEMANIFEST` (read-only source of truth), the three
  `.usages/` files (current), and the design document's verbatim artifacts — the exact
  facade shape, the binding `registration.py` skeleton, the conftest stub code, and all
  16 test specifications transferred into Task 2.
- Missing visibility in workspace or git: `tests/` and the restored `__init__.py` /
  `registration.py` will be new files; `.goga/history/`, `.goga/usages/cooks/`,
  `goga_tool_basic_build/.usages/`, `goga_tool_basic_build/CODEMANIFEST` are untracked in
  git (pre-existing state; not this plan's concern to commit).

## Mandatory Rules

Extracted from the project convention (`.goga/usages/conventions.md`, the connected
`conventions` usage) and the project toolchain configuration (`pyproject.toml`). These
rules are **mandatory for every task in this plan** and override convenience. Where a
rule conflicts with the CODEMANIFEST contract, the contract wins (conventions' own
precedence: contract → facade obligations → project conventions → language idioms).

### M1. Coding style (strictly per project convention)

- Python 3.10+ compatibility only; `pyproject.toml` is the single configuration source.
- Imports: **relative imports for all intra-package references**
  (`from .registration import register_hooks, review_presets` in the facade;
  `from .conftest import ...` in test modules — pytest injects fixtures, not plain
  helpers); absolute imports only for stdlib and third-party. Absolute imports of the
  project's own package inside the package are forbidden.
- Type hints are mandatory (Python cell rule). Allowed signature forms: `str`, `int`,
  `float`, `bool`, `list[T]`, `dict[str, T]`, `T | None`. Forbidden: `*args`, `**kwargs`,
  unparametrized `dict`/`list`.
- Naming: `snake_case` for functions and methods (both routines are functions).
- Docstrings: **Google style, mandatory** for all public functions; the first line is
  required, starts with a capital letter, ends with a period; include `Args` when the
  function accepts parameters, `Returns` when it returns a value, and `Raises` for the
  `ValueError` conflicts (both routines document their parameter; `review_presets`
  documents both `ValueError` raises).
- Code formatting inside function/method bodies: logical blocks are separated by **one
  blank line** — variable initialization apart from conditionals/loops; data preparation
  apart from processing; processing apart from the return.
- Dependencies: every third-party library in `pyproject.toml` with a minimum version
  (`goga>=2.0` in the `test` extra).
- Data models: the pydantic section of the convention **does not apply** — this cell has
  no data models (do not invent any).
- Logging: the convention's logging rules are **overridden by the cell contract** — the
  tool is silent by design: no stdout/stderr, no logging, no prints. Run feedback
  belongs to the platform.
- Value secrecy: no configuration value may appear in any message — paths and
  resolutions only.
- Error messages: the two exact ASCII literals from the design (see Task 2), built from
  the module constants; never a value.

### M2. Test writing (strictly per project convention)

- Tools: pytest (running), ruff (linting and formatting test code), pytest-cov
  (coverage). All test libraries live in `[project.optional-dependencies].test`.
- All test code is Python 3.10+ compatible and runs inside the task venv.
- Test structure mirrors the source structure directly; root-package modules test
  directly into `tests/`:
  `goga_tool_basic_build/registration.py` → `tests/test_registration.py`;
  `goga_tool_basic_build/__init__.py` → `tests/test_init.py`; integration tests directly
  in `tests/` (`tests/test_integration.py`).
- Every test directory contains `__init__.py`; shared fixtures in `tests/conftest.py`.
- Naming: files `test_<module>.py`; functions `test_<what>_<scenario>`
  (e.g. `test_review_presets_buffers_both_presets_on_absent_build`); self-documenting
  names, minimal comments.
- Test types: unit tests for every public function (main scenario and typical data);
  edge cases for empty inputs (`None`, `""`, whitespace-only), boundary values, invalid
  types, and expected exceptions via `pytest.raises`; integration tests only for
  cross-entity interaction — on duck-typed stubs, never against the real platform merge
  (ADR decision).
- Boundary tests use `@pytest.mark.parametrize` with a table of values including each
  boundary.
- Mocks: pure logic is tested **without mocks** — duck-typed stubs instead; mock only at
  external boundaries (none here; the facade subprocess check runs a real `python -c`).
- `pytest.raises(ValueError)` must always carry `match=` (active `PT` selection —
  PT011).
- TDD ordering inside each coding task: contract tests first (expected to fail), then
  implementation, then logic tests.

### M3. Lint and format enforcement (all development stages and local commits)

- Lint command (project select set, `py310`, line-length 120, mccabe 10):
  `ruff check goga_tool_basic_build/ tests/` — must exit 0.
- Formatter (project-convention formatter — `ruff format`): double quotes, LF line
  endings, magic trailing comma, space indent. Apply
  `ruff format goga_tool_basic_build/ tests/` whenever files are created or edited; use
  `ruff format --check goga_tool_basic_build/ tests/` as the commit gate. If formatting
  changed any file, re-run the full test suite before proceeding.
- Enforcement points (mandatory, in order):
  1. after every source migration step in the REPL cycle (lint the migrated file);
  2. at the end of every task (STEP 7 — lint checkbox);
  3. before every local commit — the **commit gate**: `ruff format --check
     goga_tool_basic_build/ tests/` AND `ruff check goga_tool_basic_build/ tests/` AND
     `pytest tests/ -x` all green; a local commit with a red gate is a rule violation;
  4. in the final validation of the whole plan (see Validation Commands).
- Local commits happen only at task boundaries (after STEP 8), never mid-task.

### M4. REPL cycle (the workflow core of every coding task)

Development proceeds in short evaluate → migrate → re-evaluate loops:

- **R1 — Continuous interactive evaluation**: every piece of behavior (guard logic,
  buffering, wiring) is first exercised in a live Python interpreter in the task venv
  against the duck-typed stubs; observe the actual values, buffers, and raised messages
  before codifying them in source or assertions. The REPL is where behavior is
  discovered; the tests are where it is pinned.
- **R2 — Hot reloading**: after every source edit, re-execute the evaluation in a fresh
  REPL subprocess (`python -c '...'` / `python -i`) so the migrated file is re-imported
  from disk; never trust a stale interpreter session. This mirrors the platform
  semantics — registration is never cached and package edits apply from the next run.
  In a long-lived session, `importlib.reload` of the package modules is the accepted
  alternative; fresh subprocesses are preferred.
- **R3 — Migration to source files**: code proven in the REPL is migrated verbatim into
  the target `location` file; behavior may live only in source files — the REPL session
  is scratch and is never committed. The source file is the single source of truth.
- **R4 — REPL checkpoints are explicit**: every coding task below contains checkboxed
  REPL checkpoints (evaluate → migrate → re-evaluate from the migrated file). Do not
  skip them by writing files first and evaluating later.

### M5. Environment (venv rules)

- Execute all code within a virtualenv — create it if missing (project convention).
- The venv lives **outside the project tree**: primary `/opt/project`; if `/opt` is not
  writable in the execution environment (it is not, in this one — verified), fall back
  to `$HOME/.venvs/goga-tool-basic-build`. Never create the venv inside the repository.
- Install the project editable with the test extra inside that venv:
  `pip install -e '.[test]'` (after Task 1 adds `goga>=2.0` to the extra).
- All validation commands run from the project root in that venv.

### M6. Contract and documentation constraints

- `CODEMANIFEST` files are **read-only** contract definitions. If implementation does
  not match the contract, fix the implementation — never fix the contract.
- `.usages/` files are consumer documentation: no new files are planned; the three
  existing files are verified for currency in Task 3 and edited only if implementation
  reality contradicts them (it must not — implementation follows the design they
  describe).
- Do not add anything to `build.review.additional`, subscribe any other address,
  validate leaves beyond the two review leaves, or write integration tests against the
  real platform merge (duck-typed stubs only — ADR decision).
- No `force` amendments, no logging, no prints, no third-party or goga imports at
  runtime.

---

## Tasks

> **Package ordering rule**: coding tasks for each package are completed before starting
> the next. Within each coding task, contract tests are written first (TDD workflow).
> Every task follows the **Mandatory Rules** (M1–M6); the workflow inside coding tasks
> is structured around the REPL cycle (M4).

### Task 1: Development environment, packaging metadata, and shared test scaffolding (infrastructure)

This task prepares everything the TDD coding task needs: the task venv (outside the
project tree, per M5), the `goga>=2.0` parity pin in the `test` extra (per
`goga-dependency` policy #2 — `[project.dependencies]` stays `[]`), the `tests/`
skeleton (`__init__.py` per M2 rule "every test directory contains an `__init__.py`"),
and the shared duck-typed stubs in `tests/conftest.py`. The stubs are the test-side
mirror of the two platform surfaces (`HookRegistrar`, `ConfigAmendment`) and the
authored config navigation — they are transferred verbatim from the design and already
ruff-checked against the project configuration. After this task, `pytest` collects the
conftest cleanly and the venv can import the (still missing) package target.

**Usages relevant to this task:**
- `conventions`: venv execution rule, test structure rules (M2), `__init__.py` per test
  directory, shared fixtures in `tests/conftest.py`, test libraries in the `test` extra.
- `goga-dependency`: policy #2 — `goga>=2.0` lives only in the `test` extra; policy #5 —
  tests run against duck-typed stubs of the platform surfaces.

**CRITICAL: `CODEMANIFEST` files — read-only contract definitions. Do NOT modify them. If implementation does not match the contract, fix the implementation — never fix the contract.**

- [x] Create the task venv outside the project tree (M5): try `/opt/project`; `/opt` is
  not writable in this environment, so use `$HOME/.venvs/goga-tool-basic-build`
  (`python3 -m venv "$HOME/.venvs/goga-tool-basic-build"`); never inside the repository
- [x] Edit `pyproject.toml`: add `"goga>=2.0"` to `[project.optional-dependencies].test`
  (keep `pytest>=8.0`, `pytest-cov>=5.0`, `pytest-mock>=3.10`, `ruff>=0.15.0`; keep
  `[project.dependencies]` empty; no other metadata changes)
- [x] Install editable with the test extra in the venv:
  `pip install -e '.[test]'` (from the project root, venv active)
- [x] Create `tests/__init__.py` (empty file — makes `tests` a package so later
  `from .conftest import ...` relative imports resolve)
- [x] Create `tests/conftest.py` with exactly this content (verbatim from the design —
  duck-typed stubs, the `registrar` fixture, and the `make_amendment` factory whose
  `additional` semantics mirror the loader: `None` means absent/YAML-null, any non-None
  value means present):

```python
"""Shared duck-typed stubs of the platform surfaces."""

import pytest


class StubRegistrar:
    """Duck-typed HookRegistrar: records subscribe calls."""

    def __init__(self):
        self.calls = []  # list of (domain, action, name, hook)

    def subscribe(self, domain, action, name, hook):
        self.calls.append((domain, action, name, hook))


class StubAmendment:
    """Duck-typed ConfigAmendment: authored config plus amendment buffers."""

    def __init__(self, config):
        self.config = config
        self.sets = []    # list of (path, value)
        self.forces = []  # list of (path, value)

    def set(self, path, value):
        self.sets.append((path, value))

    def force(self, path, value):
        self.forces.append((path, value))


class StubSection:
    """Duck-typed config section: attributes only, None by default."""

    def __init__(self, **fields):
        self.__dict__.update(fields)


@pytest.fixture
def registrar():
    return StubRegistrar()


def make_amendment(strategy=None, additional=None, max_iterations=None, review_present=True, build_present=True):
    """Build a StubAmendment over an authored config of the given review leaves.

    `additional` semantics mirror the loader: None means absent/YAML-null;
    any non-None value (including the empty stub section) means present.
    """
    review = (
        StubSection(strategy=strategy, additional=additional, max_iterations=max_iterations)
        if review_present
        else None
    )
    build = StubSection(review=review) if build_present else None

    return StubAmendment(StubSection(build=build))
```

- [x] **REPL checkpoint (R1)**: in the venv, evaluate the scaffolding interactively
  before relying on it — e.g.
  `python -c "from tests.conftest import StubRegistrar, StubAmendment, StubSection, make_amendment; a = make_amendment(strategy='short'); print(a.config.build.review.strategy, a.sets, a.forces)"`
  → must print `short [] []`; also `make_amendment(build_present=False).config.build`
  → `None`. Confirm the stubs import and behave, then leave them untouched (R3 — they
  already are the migrated artifact)
- [x] Verify collection: `pytest tests/ --collect-only` — expects "no tests ran" with
  exit code 5 (no tests collected yet — this is correct at this stage) and **no
  collection errors**; also `python -c "from tests.conftest import StubRegistrar, StubAmendment, StubSection, make_amendment"`
  exits 0
- [x] Lint and format the new files (M3):
  `ruff check tests/` → 0 findings; `ruff format tests/` (apply; then re-run
  `ruff check tests/`)
- [x] **Commit checkpoint (only if committing locally)**: commit gate green —
  `ruff format --check tests/`, `ruff check tests/`, `pytest tests/ -x` (exit 5 with no
  errors is the expected pre-Task-2 state; note it in the commit message if needed)

### Task 2: Implement `registration.py` (both routines) and the package facade (TDD coding)

This task implements the entire contract surface: both Routines share
`location: registration.py` and are wired together (`register_hooks` subscribes the
module-level callable `review_presets`), so they are implemented as one unit together
with the facade `__init__.py` that re-exports them (the facade import fails until
`registration.py` exists). The implementation follows the binding skeleton and the
Algorithm Design below, transferred verbatim from the design document. Platform types
are `TYPE_CHECKING`-only references; the delivered objects are consumed by duck typing.
Follow the REPL cycle (M4) throughout: prototype against the Task 1 stubs, migrate into
`registration.py`, re-evaluate from the migrated file in a fresh subprocess.

**`registration.py` skeleton (order and mechanics are binding; then both functions per
the Algorithm Design; docstrings per M1 Google style with `Raises:` sections; message
literals built from the path constants; ASCII-only messages):**

```python
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
```

**`register_hooks` algorithm:**

```
1. call hooks.subscribe with the four positional arguments:
   domain="config", action="amend_config", name="review_presets",
   hook=review_presets
   → one Subscription lands in the run registry, qualified by the
     platform-assigned tool identity
```

Errors: none raised by the function itself. Edge cases: called multiple times per run is
impossible (registration is never cached, one build per run); the function stays a single
`subscribe` call regardless.

**`review_presets` algorithm:**

```
1. build := context.config.build ; review := build.review unless build is None
   → the authored review section or None
2. strategy := review.strategy unless review is None
   IF strategy is None OR (isinstance(strategy, str) AND strategy.strip() == ""):
       → unset: no conflict, fall through to step 3
   ELSE IF (strategy.strip() if isinstance(strategy, str) else strategy) != "medium":
       → raise ValueError (strategy message); nothing buffered
3. additional := review.additional unless review is None
   IF additional is not None:
       → raise ValueError (additional message); nothing buffered
4. context.set("build.review.strategy", "medium")
   → one buffered set amendment
5. context.set("build.review.max_iterations", 5)
   → one buffered set amendment; return None
```

**Error message literals (exact; ASCII hyphen; path and resolution only, never a value):**

```
refused the authored configuration at build.review.strategy - remove the authored strategy or uninstall the tool

refused the authored configuration at build.review.additional - remove the additional section or uninstall the tool
```

Rendered by the platform as
`hook review_presets of tool <tool> failed on config.amend_config: <message>`.

**Edge cases the implementation must honor:** `build` absent → both presets buffered;
`build` present with `review` absent → same; strategy `None`/`""`/`"   "` → unset;
strategy `"medium"` → accepted silently, presets still buffered; authored
`max_iterations` never inspected; both conflicts present → strategy message (fixed
order); `additional: {}` (an instance) conflicts while absent/null (`None`) does not; a
non-string strategy conflicts instead of crashing (`isinstance` guard before any
`.strip()`).

**Usages relevant to this task:**
- `conventions`: coding style and docstring rules (M1), test structure/naming/mocks
  policy (M2), venv execution (M5).
- `goga-dependency`: policies #3 (`TYPE_CHECKING`-only platform references,
  `from __future__ import annotations`), #4 (import-clean facade), #5 (tests on
  duck-typed stubs).
- `config-amend`: reads via `context.config` attribute navigation; writes are two `set`
  calls on model-known dotted leaf paths; `force` never used; authored-wins never
  re-derived; failure is `ValueError` only.
- `hook-registration`: the four-argument `subscribe`; `review_presets` declares exactly
  `context` so the platform delivers the amendment view by name
  (`review_presets(context=...)`).

**CRITICAL: `CODEMANIFEST` files — read-only contract definitions. Do NOT modify them. If implementation does not match the contract, fix the implementation — never fix the contract.**

- [ ] **STEP 0 (DECLARATION)**: declare this task ("Task 2 — registration.py + facade")
  before writing any code
- [ ] **STEP 1 (CONTRACT TESTS)**: write the contract-tier tests — expected to FAIL at
  this stage (`registration.py` and the facade do not exist yet):
  - Create `tests/test_init.py` with the two facade tests (full specifications in the
    logic-test list below — they are contract tests by nature: facade accessibility and
    API shape): `test_facade_reexports_contract_api` and
    `test_facade_import_requires_no_goga` (the latter runs
    `python -c "import goga_tool_basic_build; import sys; sys.exit(0 if 'goga' not in sys.modules else 1)"`
    in a subprocess with the project on `sys.path`)
  - Create `tests/test_registration.py` with the contract-envelope test
    `test_register_hooks_subscribes_single_config_amend_hook` (specification below — it
    pins the exactly-one-subscription requirement, the exact address, and the module
    callable identity)
  - Import mechanics per M2: `from .conftest import StubSection, make_amendment` where
    needed (the registrar arrives via the `registrar` fixture); import the target as
    `from goga_tool_basic_build.registration import register_hooks, review_presets`
  - Confirm they fail for the right reason (import error of the missing module/facade)
- [ ] **STEP 2 (IMPLEMENTATION — REPL cycle)**:
  - **REPL evaluate (R1)**: in the venv, from the project root, interactively prototype
    both functions (e.g. `python -i` with the stub classes pasted/imported) and run the
    eight algorithm scenarios against `make_amendment(...)` stubs: absent build; absent
    review; blank strategies (`None`, `""`, `"   "`); `"medium"`; non-medium
    (`"short"`, `"full"`, `"quick"`); non-string (`42`, `True`); populated and empty
    `additional`; authored `max_iterations=8`. Observe the buffers and the exact raised
    messages before writing files
  - **Migrate (R3)**: create `goga_tool_basic_build/registration.py` — the binding
    skeleton above, then `register_hooks(hooks: HookRegistrar) -> None` and
    `review_presets(context: ConfigAmendment) -> None` per the Algorithm Design, with
    the two message literals built from `_STRATEGY_PATH` / the additional path; Google
    docstrings with `Raises:`; one-blank-line block separation; no other imports beyond
    the two compile-time aids
  - **Migrate (R3)**: create `goga_tool_basic_build/__init__.py` — the exact facade
    shape from the Context section (module docstring, the relative re-export,
    `__all__ = ["register_hooks", "review_presets"]`)
  - **Hot-reload verify (R2)**: in a fresh subprocess, re-import from disk and
    re-evaluate two scenarios (one buffering, one conflict):
    `python -c "from goga_tool_basic_build import register_hooks, review_presets; from tests.conftest import make_amendment; a = make_amendment(); review_presets(a); print(a.sets, a.forces)"`
    → `[('build.review.strategy', 'medium'), ('build.review.max_iterations', 5)] []`
  - Lint the migrated files immediately (M3 point 1): `ruff check goga_tool_basic_build/`
    and `ruff format goga_tool_basic_build/`
- [ ] **STEP 3 (INTERFACE VERIFICATION)**: run the STEP 1 contract tests —
  `pytest tests/test_init.py tests/test_registration.py -v` — the three contract tests
  must all pass now
- [ ] **STEP 4 (LOGIC TESTS)**: complete `tests/test_registration.py` with the remaining
  thirteen designed tests (specifications below — transfer assertions exactly,
  including `match=` anchors per PT011)
- [ ] **STEP 5 (DEBUGGING — REPL-assisted)**: run `pytest tests/ -x`; for any failure,
  reproduce it interactively in the REPL (R1/R2), fix the **implementation** (never the
  tests) until the full suite is green
- [ ] **STEP 6 (CONTRACT RE-VERIFICATION)**: verify all contract obligations hold —
  facade importable (`python -c "import goga_tool_basic_build"`), API shape
  (`python -c "from goga_tool_basic_build import register_hooks, review_presets"`),
  exactly one subscription at `config / amend_config`, `set`-only write footprint on the
  two model-known leaves, `ValueError`-only failures with path+resolution messages
- [ ] **STEP 7 (LINT)**: `ruff check goga_tool_basic_build/ tests/` → 0 findings;
  `ruff format goga_tool_basic_build/ tests/` (apply); if formatting changed any file,
  re-run `pytest tests/ -x`
- [ ] **STEP 8 (COMPLETION)**: mark this task's checkboxes complete
- [ ] **Commit checkpoint (only if committing locally)**: commit gate green (M3):
  `ruff format --check goga_tool_basic_build/ tests/` + `ruff check goga_tool_basic_build/ tests/`
  + `pytest tests/ -x`
- **→ REVIEW → APPROVAL → NEXT TASK**

**Designed test specifications (16 tests — verbatim from the design document; the three
marked [contract] are written in STEP 1, the rest in STEP 4):**

Positive:

1. [contract] `test_register_hooks_subscribes_single_config_amend_hook` —
   Setup: `registrar` fixture (empty `StubRegistrar`). Input: `register_hooks(registrar)`.
   Assertions:
   ```python
   len(registrar.calls) == 1
   registrar.calls[0][:3] == ("config", "amend_config", "review_presets")
   registrar.calls[0][3] is goga_tool_basic_build.registration.review_presets
   ```
   Sufficiency: pins "exactly one subscription" and the exact address — prevents a
   second domain/action, hook-name drift, or a wrapper callable being registered.
2. `test_review_presets_buffers_both_presets_on_absent_build` —
   Setup: `amendment = make_amendment(build_present=False)`. Input:
   `review_presets(amendment)`. Assertions:
   ```python
   amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
   amendment.forces == []
   ```
   Sufficiency: the core guarantee — absent intermediate branches do not block the
   presets; pins exact paths, values, order, set-only intent.
3. `test_review_presets_buffers_both_presets_on_absent_review` —
   Setup: `amendment = make_amendment(review_present=False, build_present=True)`.
   Assertions: same as test 2. Sufficiency: the half-present branch must behave
   identically; prevents an `AttributeError`-style navigation regression.
4. `test_review_presets_accepts_authored_medium_strategy` —
   Setup: `amendment = make_amendment(strategy="medium")`. Assertions: no exception;
   `amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]`.
   Sufficiency: authored `medium` accepted silently, buffering never suppressed at the
   hook level.
5. `test_review_presets_buffers_presets_with_authored_max_iterations` —
   Setup: `amendment = make_amendment(max_iterations=8)`. Assertions: no exception;
   `("build.review.max_iterations", 5) in amendment.sets`; full `sets` list as above.
   Sufficiency: the one tuning knob — an authored cap never conflicts and never
   suppresses the buffered preset.
6. `test_review_presets_write_footprint_is_exactly_two_set_amendments` —
   Setup: `amendment = make_amendment()`. Assertions:
   ```python
   len(amendment.sets) == 2
   len(amendment.forces) == 0
   sorted(path for path, _ in amendment.sets) == ["build.review.max_iterations", "build.review.strategy"]
   ```
   Sufficiency: the exact write footprint — no `force`, no third leaf, no path typo.

Negative:

7. `test_review_presets_raises_on_non_medium_strategy` — parametrized
   (`@pytest.mark.parametrize`) over `"short"`, `"full"`, `"quick"`; setup
   `make_amendment(strategy=value)`. Assertions:
   ```python
   with pytest.raises(ValueError, match="build.review.strategy"):
       review_presets(amendment)
   amendment.sets == []
   ```
   Sufficiency: the strategy conflict — including platform-valid `short`/`full` — stops
   the hook before any buffering; the whole contribution is discarded.
8. `test_review_presets_error_names_path_and_resolution_without_value` —
   Setup: `make_amendment(strategy="full")`. Assertions:
   ```python
   with pytest.raises(ValueError, match="refused the authored configuration at build.review.strategy") as excinfo:
       review_presets(amendment)
   message = str(excinfo.value)
   "build.review.strategy" in message
   "remove the authored strategy or uninstall the tool" in message
   "full" not in message
   ```
   Sufficiency: the value-secrecy invariant — the most safety-critical property of the
   tool's output.
9. `test_review_presets_raises_on_populated_additional` —
   Setup: `make_amendment(additional=StubSection(agent="codex", patience=3, max_iterations=15))`.
   Assertions:
   ```python
   with pytest.raises(ValueError, match="build.review.additional"):
       review_presets(amendment)
   amendment.sets == []
   ```
   Sufficiency: the additional conflict for a populated section; strategy had passed,
   proving the second guard fires on its own.
10. `test_review_presets_raises_on_empty_additional_mapping` —
    Setup: `make_amendment(additional=StubSection())` (present but empty — mirrors the
    loader's `AdditionalReviewConfig()` for `additional: {}`). Assertions: same shape as
    test 9 (`match="build.review.additional"`, empty buffer). Sufficiency: the sharpest
    edge — `additional: {}` conflicts while absent/null does not; pins the `is not None`
    presence semantics against a "falsy-means-absent" refactor.
11. `test_review_presets_reports_strategy_conflict_first` —
    Setup: `make_amendment(strategy="short", additional=StubSection())`. Assertions:
    ```python
    with pytest.raises(ValueError, match="build.review.strategy") as excinfo:
        review_presets(amendment)
    "build.review.additional" not in str(excinfo.value)
    ```
    Sufficiency: the fixed check order — deterministic error selection when both
    conflicts are present.

Edge cases:

12. `test_review_presets_treats_blank_strategy_as_unset` — parametrized over `None`,
    `""`, `"   "`; setup `make_amendment(strategy=value)`. Assertions: no exception;
    `amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]`.
    Sufficiency: blank reads as unset; pins the defensive normalization for duck-typed
    deliveries.
13. `test_review_presets_conflicts_on_non_string_strategy` — parametrized over `42`,
    `True`; setup `make_amendment(strategy=value)`. Assertions:
    ```python
    with pytest.raises(ValueError, match="build.review.strategy"):
        review_presets(amendment)
    amendment.sets == []
    ```
    Sufficiency: a duck-typed non-string strategy conflicts instead of crashing
    (`AttributeError` on `.strip()`) or being silently accepted; `True` is the classic
    YAML footgun. Verified against the live end-to-end simulation.
14. `test_review_presets_skips_conflict_when_additional_absent_or_null` —
    Setup: `make_amendment(additional=None)`. Assertions: no exception;
    `("build.review.strategy", "medium") in amendment.sets`. Sufficiency: the complement
    of the empty-mapping test — together they pin the exact presence boundary.
15. [contract] `test_facade_reexports_contract_api` (in `tests/test_init.py`) —
    Input: `import goga_tool_basic_build`. Assertions:
    ```python
    goga_tool_basic_build.register_hooks is goga_tool_basic_build.registration.register_hooks
    goga_tool_basic_build.review_presets is goga_tool_basic_build.registration.review_presets
    goga_tool_basic_build.__all__ == ["register_hooks", "review_presets"]
    callable(goga_tool_basic_build.register_hooks)
    callable(goga_tool_basic_build.review_presets)
    ```
    Sufficiency: the facade contract — the platform consumes
    `from goga_tool_basic_build import register_hooks, review_presets`; a facade that
    fails to re-export is fatal to every goga command enumerating tool packages.
16. [contract] `test_facade_import_requires_no_goga` (in `tests/test_init.py`) —
    Input: subprocess
    `python -c "import goga_tool_basic_build; import sys; sys.exit(0 if 'goga' not in sys.modules else 1)"`
    with the project on `sys.path` (the test venv has goga installed, so the check runs
    in a clean child). Assertions: `subprocess returncode == 0`. Sufficiency: the
    import-safety policy end-to-end — catches a `TYPE_CHECKING` block leaking to runtime
    or an accidental top-level goga import.

### Task 3: Integration tests for the registration → amendment wiring (integration tests)

Cross-entity scenario on duck-typed stubs only (ADR decision — never the real platform
merge): the two routines interact through the platform's two-step flow (design data-flow
scenarios 1 and 2). The unit tests verify each routine in isolation; this task pins the
**wiring**: the callable that `register_hooks` subscribes is the hook that buffers, and
it is invoked the way the platform invokes it — the registrar callback positionally
(`register_hooks(registrar)`, verified platform fact) and the hook by declared parameter
name (`hook(context=...)` — `build_hook_arguments` delivers only declared names from
`{context, self}`). Also verifies the three consumer-facing `.usages/` files remain
current against the implemented reality.

**Usages relevant to this task:**
- `conventions`: integration tests placed directly in `tests/` (M2 structure rule 3);
  naming `test_<what>_<scenario>`; pure logic without mocks.
- `goga-dependency`: policy #5 — tests on duck-typed stubs, not real goga objects.
- `hook-registration`: the callback and delivery contracts exercised by the wiring
  (positional registrar call; declared-name keyword delivery).
- `config-amend`: the amendment-view behavior observed through the wiring (two `set`
  buffers; hard `ValueError` before any buffering).
- Local usages `registration`, `profile`, `conflicts`: consumer documentation verified
  for currency against the implemented behavior.

**CRITICAL: `CODEMANIFEST` files — read-only contract definitions. Do NOT modify them. If implementation does not match the contract, fix the implementation — never fix the contract.**

- [ ] **REPL checkpoint (R1→R3)**: in the venv, evaluate the wiring interactively
  before writing assertions —
  `python -c "from goga_tool_basic_build import register_hooks; from tests.conftest import StubRegistrar, make_amendment; r = StubRegistrar(); register_hooks(r); (d, a, n, hook) = r.calls[0]; ctx = make_amendment(); hook(context=ctx); print(r.calls[0][:3], ctx.sets, ctx.forces)"`
  → `('config', 'amend_config', 'review_presets') [('build.review.strategy', 'medium'), ('build.review.max_iterations', 5)] []`
- [ ] Create `tests/test_integration.py` (directly in `tests/`, per M2) importing the
  stubs via `from .conftest import make_amendment` and the facade API via
  `from goga_tool_basic_build import register_hooks`; use the `registrar` fixture
- [ ] Test cross-entity interaction — happy path
  `test_platform_flow_subscribes_then_hook_buffers_presets`: build a `StubRegistrar`,
  call `register_hooks(registrar)` positionally; assert exactly one subscription
  `("config", "amend_config", "review_presets")`; then invoke the recorded callable the
  way the platform does — `hook(context=make_amendment())` (declared-name keyword) —
  and assert `ctx.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]`
  and `ctx.forces == []`
- [ ] Test cross-entity interaction — conflict path
  `test_platform_flow_conflict_stops_contribution_before_buffering`: same wiring, but
  `ctx = make_amendment(strategy="short")`; assert
  `pytest.raises(ValueError, match="build.review.strategy")` around `hook(context=ctx)`
  and `ctx.sets == []` (the whole contribution is discarded — nothing applies
  partially)
- [ ] Run validation: `pytest tests/test_integration.py -v` — both tests pass; then the
  whole suite `pytest tests/ -x` — all 18 test functions green (23 items with
  parametrization)
- [ ] Verify local usages currency: read `goga_tool_basic_build/.usages/registration.md`,
  `profile.md`, `conflicts.md` and confirm every claim matches the implemented behavior
  (single subscription address and name; purity; two buffered presets with values
  `medium` / `5`; the two conflicts with fixed order and error shape naming tool,
  action, path, resolution — never a value; the not-a-conflict list; authored-wins
  knob). All three were verified current at design review — expect **no edits**; if any
  contradiction is found, fix is limited to the usage file's wording (consumer
  documentation), never to the contract or the implementation
- [ ] Lint and format: `ruff check tests/` → 0 findings; `ruff format tests/` (apply);
  re-run `pytest tests/ -x` if formatting changed anything
- [ ] **Commit checkpoint (only if committing locally)**: commit gate green (M3):
  `ruff format --check goga_tool_basic_build/ tests/` + `ruff check goga_tool_basic_build/ tests/`
  + `pytest tests/ -x`
- **→ REVIEW → APPROVAL → NEXT TASK**

---

## Validation Commands

All commands run from the project root inside the task venv (M5 — outside the project
tree; in this environment `$HOME/.venvs/goga-tool-basic-build`).

- `pytest tests/ -x`: Run all tests (18 test functions: 16 designed + 2 integration;
  pytest reports 23 items due to parametrize expansion in three tests)
- `pytest tests/test_registration.py -v`: Run the routine test module (14 tests)
- `pytest tests/test_init.py -v`: Run the facade test module (2 tests)
- `pytest tests/test_integration.py -v`: Run the integration test module (2 tests)
- `ruff check goga_tool_basic_build/ tests/`: Lint check with the project select set
  (E,W,F,I,N,UP,B,SIM,PL,PLR,C4,DTZ,PT,ARG,RUF,PTH,C90; py310; line-length 120)
- `ruff format --check goga_tool_basic_build/ tests/`: Formatter gate (double quotes,
  LF, magic trailing comma) — the local-commit gate together with lint and tests
- `python -c "import goga_tool_basic_build"`: Facade check — bare import must succeed
  (import-clean without goga at runtime)
- `python -c "from goga_tool_basic_build import register_hooks, review_presets"`: Facade
  API shape — both contract names importable from the package root
- `python -c "import goga_tool_basic_build; import sys; sys.exit(0 if 'goga' not in sys.modules else 1)"`:
  Runtime goga-independence of the facade (also covered by `test_facade_import_requires_no_goga`)
- `goga lint`: Contract integrity of the untouched CODEMANIFEST — must stay
  `cells: 1 errors: 0`

---

## Completion Criteria

- [ ] Every contract entity is implemented in the correct `location` —
      `register_hooks` and `review_presets` in `goga_tool_basic_build/registration.py`
- [ ] Every contract entity is accessible from the facade —
      `goga_tool_basic_build.__all__ == ["register_hooks", "review_presets"]`, identities
      preserved
- [ ] Properties and methods match the declared API (both Routines: signatures
      `register_hooks(hooks)` / `review_presets(context)`, no return value)
- [ ] Descriptions are reflected in behavior — the algorithm, requirements, and
      constraints from the CODEMANIFEST annotations hold (guards in fixed order; two
      unconditional `set` buffers; `ValueError`-only failures; value secrecy; silence)
- [ ] Contract dependencies are met — platform types referenced under `TYPE_CHECKING`
      only; zero runtime goga imports; `[project.dependencies]` empty; `goga>=2.0` in
      the `test` extra
- [ ] Re-exports are accessible from the facade (Python cell facade rule via `__all__`)
- [ ] Every coding task followed the TDD workflow (contract tests → code → verification
      → logic tests → debugging → re-verification → lint)
- [ ] Contract tests and logic tests cover facade, API, and behavior within each coding
      task; all 16 designed test scenarios are implemented exactly as specified
- [ ] Integration tests exist for the cross-entity wiring (2 stub-only tests; no
      real-platform integration — ADR decision)
- [ ] No package boundary was expanded — no new cells, no new interfaces beyond the
      contract, internal decomposition only
- [ ] `CODEMANIFEST` files were not modified (contract is read-only; `goga lint` still
      reports `cells: 1 errors: 0`)
- [ ] All validation commands pass
- [ ] Every Usages entry is mentioned in at least one task (`conventions`,
      `goga-dependency`, `config-amend`, `hook-registration`; local usages `registration`,
      `profile`, `conflicts` verified in Task 3)
- [ ] The Mandatory Rules were followed throughout: coding style per M1, test rules per
      M2, lint/format enforced at every stage and before every local commit (M3), the
      REPL cycle (evaluate → migrate → re-evaluate) executed inside every coding task
      (M4), all execution in the out-of-tree venv (M5), contract/documentation
      constraints respected (M6)
