# Design Document: `goga-tool-basic-build` — the-first-version

Complete architectural specification for implementing the contract materialized in
`goga_tool_basic_build/CODEMANIFEST`. Every fact about the platform below was verified
against the installed goga 2.0.2 (the platform the `test` extra pins) — source inspection
of `goga.hooks.tools.registration`, `goga.config.hooks.{amendments,events,overlay}`, and
`goga.config.project.loader`, plus live checks of `declared_actions()` and
`enumerate_tool_packages()`.

## Contract Changes

### Changed CODEMANIFEST Files

- `goga_tool_basic_build/CODEMANIFEST`: **new** (created by the apply-architecture stage,
  byte-exact from the reviewed architecture plan). Single cell, no `Imports`, two Routine
  types, four file-form `Usages`, global `Annotations`, footer (`Author: Goga`,
  `CreatedAt: 04/10/26`).

### New Entities

- `register_hooks` — Routine, `location: registration.py`. Facade callback the platform
  calls when a command first reaches a hook checkpoint; performs the single
  `config / amend_config` subscription.
- `review_presets` — Routine, `location: registration.py`. The single amendment hook:
  guards two authored-configuration conflicts in a fixed order, then buffers two
  apply-where-silent `set` amendments.

### Changed Entities

- None.

### Deleted Entities

- None.

### Usages and Annotations Changes

- Four `Usages` connected, all file-form, all referenced in annotations (cookbook rule
  satisfied): `conventions`, `goga-dependency`, `config-amend`, `hook-registration`.
- No `Imports` → no imported usages.

## Applied Fixes

### Fixed CODEMANIFEST Defects

- None. The Phase 3 audit found no defects: `goga lint` reports `cells: 1, errors: 0`;
  both routines are correctly Routines (single operations, no state); `location:
  registration.py` is flat with the `.py` extension matching `language: python`; all
  backtick references resolve within the document context; every connected practice is
  referenced in at least one annotation. The four-dimension consistency audit (Interface ↔
  Type, Type ↔ Mutation, Interface ↔ Interface, Annotations ↔ Entity) passed — details in
  the Code Stack Trace checkpoints below.

## Entity Interaction and Data Flow

### Interaction Diagram

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

### Data Flows

| # | Scenario | Participating entities | Data passed | Order |
|---|---|---|---|---|
| 1 | Command reaches first hook checkpoint | platform → facade → `register_hooks` | `hooks: HookRegistrar` (tool-scoped registrar) | facade import → `register_hooks` → one `subscribe` call |
| 2 | Command loads `.goga/config.yml` | platform → `review_presets` | `context`: wrapped `ConfigAmendment` over the read-only authored `ProjectConfig` | guards (strategy, then additional) → two `set` buffers → return |
| 3 | Hook returns | buffer → platform merge | `ToolAmendment(tool, amendments)` — two `PathAmendment(path, intent="set", value)` | merge resolves authored-silence per path → effective config + summary lines |
| 4 | Hook raises | `review_presets` → platform | `ValueError` (path + resolution, no value) | platform wraps: `hook review_presets of tool <tool> failed on config.amend_config: <message>`; command stops; whole contribution discarded |

### Entity Dependencies

- `register_hooks` → references `review_presets` (the subscribed callable) — intra-module,
  no import needed beyond co-location in `registration.py`.
- `review_presets` → depends on nothing inside the project; interacts with the delivered
  `context` by duck typing only.
- Platform types `HookRegistrar` / `ConfigAmendment` are **type-checking references only**
  (`goga-dependency` policy #3): `from __future__ import annotations` +
  `if TYPE_CHECKING:` block; zero runtime imports of goga.
- Initialization order: the platform imports the facade first — `__init__.py` must stay
  import-clean so `registration.py` is reachable; `registration.py` executes no
  third-party or goga import at runtime — its only imports are the compile-time aids
  `from __future__ import annotations` and `typing.TYPE_CHECKING` (both stdlib, both
  import-safe in a bare environment).

## Code Stack Trace

### Trace: `register_hooks`

#### Chain

1. **Input**: the platform's `HookRegistry.build_once()` enumerates installed
   `goga_tool_*` packages (verified: `enumerate_tool_packages()` returns
   `ToolPackage(module_name=...)` by prefix), imports the facade, and calls
   `register_hooks(hooks=HookRegistrar(tool=...))`. The tool identity is assigned by the
   platform from the package name — the function never names its own tool.
2. **Step**: `hooks.subscribe("config", "amend_config", "review_presets", review_presets)`
   — four positional arguments: domain, action, name, callable.
   → checkpoint: **verified** against the installed registrar:
   `HookRegistrar.subscribe(self, domain: str, action: str, name: str, hook: Callable[..., object]) -> None`;
   the address `config / amend_config` is declared with `error_class='hard'`
   (`declared_actions()` live check) → the envelope is accepted, one `Subscription`
   appended.
3. **Output**: `None`. Exactly one subscription exists: domain `"config"`, action
   `"amend_config"`, name `"review_presets"`, hook the module-level callable
   `review_presets`.

#### Checkpoint Summary

- Subscribe arity and address validity: **passed** (registrar source + declared-actions
  live check).
- Contract ↔ platform signature agreement (`hooks: HookRegistrar` receives the registrar):
  **passed**.
- Exactly-one-subscription requirement is enforceable by a stub registrar recording calls:
  **passed**.

### Trace: `review_presets`

#### Chain

1. **Input**: at the configuration load moment of a config-consuming surface, the platform
   builds `ConfigAmendment(config=_read_only_view(authored))`, wraps it, and calls
   `subscription.hook(context=proxy)` — verified in `goga.config.hooks.events`: the call
   is `hook(**build_hook_arguments(...))` and `build_hook_arguments` delivers **only the
   declared parameter names** from the offered set `{context, self}`; `review_presets`
   declares exactly `context` → called as `review_presets(context=...)`.
2. **Step**: navigate the authored model — `build = context.config.build`
   (`BuildConfig | None`; `None` when the section is absent), then
   `review = build.review if build is not None else None` (`ReviewConfig | None`).
   → checkpoint: field existence and `None`-for-absent semantics **verified** against the
   installed dataclasses: `ProjectConfig.build`, `BuildConfig.review`,
   `ReviewConfig.{strategy,max_iterations,additional}` all exist with those types; the
   navigation raises nothing on absent branches.
3. **Step**: strategy guard — `strategy = review.strategy if review is not None else None`.
   Unset ⟺ `strategy is None` or (`isinstance(strategy, str)` and
   `strategy.strip() == ""`). Present-and-not-`medium` ⟺ not unset and the normalized
   value (`strategy.strip()` for a `str`, the value itself otherwise) `!= "medium"` →
   raise `ValueError` with the strategy message (below), before any buffering.
   → checkpoint: **verified** in `goga.config.project.loader`:
   `_parse_optional_stripped_str` already normalizes an authored blank strategy to `None`
   and stores a non-empty strategy stripped — the hook's own blank/strip handling is
   therefore redundant on the real platform (defensive only) and never disagrees with it:
   a loader-delivered value is either `None` or a non-blank stripped string.
4. **Step**: additional guard — `additional = review.additional if review is not None else
   None`. Conflict ⟺ `additional is not None`.
   → checkpoint: **verified** in the loader: absent/YAML-null `additional` parses to
   `None`; a present mapping — including `additional: {}` — parses to an
   `AdditionalReviewConfig` **instance**. So `is not None` is exactly "present with any
   contents, including an empty mapping". Authored `additional` never reaches the hook as
   a raw `dict`.
5. **Step**: buffer the presets — `context.set("build.review.strategy", "medium")`, then
   `context.set("build.review.max_iterations", 5)`, unconditionally (guards did not
   raise), regardless of authored values at those leaves.
   → checkpoint: **verified** — both paths are model-known leaves of the platform's
   configuration type tree (`ReviewConfig.strategy: _scalar(str)`,
   `ReviewConfig.max_iterations: _scalar(int)`); the value types match the node types
   (`"medium"` str, `5` int) so the merge's structural validation passes; absent
   intermediate branches materialize at COMPOSE time (merge step 3), so the hook never
   pre-materializes anything. Authored-wins (a `set` on a non-silent path is dropped
   silently) belongs to the merge — verified in `merge_config_amendments`; the hook never
   re-derives it.
6. **Output**: `None`. The per-tool buffer holds exactly two
   `PathAmendment(intent="set")` entries in buffer order; the platform commits them as one
   `ToolAmendment` only after the hook returns, then merges.

#### Checkpoint Summary

- Delivery projection (`context` by declared name): **passed** (`build_hook_arguments`
  source).
- Read-surface navigation (None-able branches, no `AttributeError` path): **passed**
  (model fields verified).
- Blank-strategy semantics (loader normalization vs contract requirement): **passed** —
  consistent, hook stays defensive.
- `additional: {}` ⟺ instance ⟺ conflict; absent/null ⟺ `None` ⟺ no conflict:
  **passed** (loader source).
- Write footprint (exactly two model-known leaves, correct value types, `set` only):
  **passed** (type tree source).
- Hard-failure composition: **passed** — the platform wraps the hook's `ValueError` as
  `hook review_presets of tool <tool> failed on config.amend_config: <message>`; the
  hook's message supplies the path and the resolution, the platform supplies tool/action.

## Algorithm Design

### `register_hooks`

**Responsibility**: the tool's registration facade callback — the only subscription point.

**Algorithm:**
```
1. call hooks.subscribe with the four positional arguments:
   domain="config", action="amend_config", name="review_presets",
   hook=review_presets
   → one Subscription lands in the run registry, qualified by the
     platform-assigned tool identity
```

**Errors:**
- None raised by the function itself. An invalid envelope would be refused as data by the
  registrar (warning, registration skipped) — unreachable here: the address is declared,
  the name is a non-empty literal, the callable is the module function.

**Edge Cases:**
- Called multiple times per run: impossible (registration is never cached, one build per
  run); if it were, a repeated identical name on the same address is refused as data by
  the registrar — the function stays a single `subscribe` call regardless.

### `review_presets`

**Responsibility**: the tool's single amendment hook — conflict guard plus preset
buffering; a pure function over the delivered view (no I/O, no state, no output).

**Algorithm:**
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

**Error messages** (exact literals; ASCII hyphen, not em dash — RUF001-safe under the
project's ruff `RUF` selection; path and resolution only, never a value):

```
refused the authored configuration at build.review.strategy - remove the authored strategy or uninstall the tool

refused the authored configuration at build.review.additional - remove the additional section or uninstall the tool
```

Rendered by the platform as
`hook review_presets of tool <tool> failed on config.amend_config: <message>` — matching
the consumer-documented error shape in `.usages/conflicts.md` (tool, action, path,
resolution; no value).

**Errors:**
- `ValueError` (strategy message) → authored strategy present, non-blank, not `medium` →
  the command stops (hard action), the tool's whole contribution is discarded, the
  consumer sees the platform-composed error naming the path.
- `ValueError` (additional message) → authored `additional` present in any shape,
  including `{}` → same hard treatment.
- No other raise path exists: navigation guards every absent branch (`build`, `review`)
  with `None` checks; no attribute access on `None`; no string method on a possible
  non-string without an `isinstance` check (a non-string strategy through a duck-typed
  delivery compares `!=` and conflicts instead of crashing).

**Edge Cases:**
- `build` absent → `review` is `None` → both guards pass → both presets buffered.
- `build` present, `review` absent → same as above.
- Strategy `None` / `""` / `"   "` → unset → no conflict, presets buffered. (On the real
  platform the loader already delivered `None` for all three; the hook's blank check is
  defensive for duck-typed deliveries.)
- Strategy `"medium"` → accepted silently, presets still buffered (the merge drops the
  strategy `set` — authored-wins — which is the platform's business).
- Authored `max_iterations: 8` → never inspected, never conflicts; the cap preset is
  buffered and the merge drops it (authored-wins).
- Both conflicts present → the strategy message is raised (steps run in fixed order 2→3;
  step 3 never executes) — deterministic.
- Authored `additional: {}` → an `AdditionalReviewConfig` instance at the hook →
  conflict; authored `additional:` (YAML null) or absent key → `None` → no conflict.

## Cross-cutting Concerns

- **Error handling**: the hook fails only through `ValueError` on the two conflicts, with
  the exact literals above; every other input shape passes through silently. Error
  messages carry configuration paths and resolutions only — value secrecy is absolute
  (`Constraints` of both routines and the global `Annotations`).
- **Validation**: none beyond the two guards. Structural validation of authored values
  belongs to the platform loader (which rejects a non-string strategy, a non-mapping
  `additional`, a non-int `max_iterations` before the checkpoint); semantic whitelists
  belong to the consuming command. The hook never validates what it does not own.
- **Logging**: none. The tool is silent by design — no stdout/stderr, no logging (global
  `Annotations` override the project's general logging convention for this cell); run
  feedback (amendment summary, hard-failure reporting) belongs to the platform.
- **Caching**: none. Pure function; the platform delivers a fresh per-tool view per
  checkpoint and never caches registrations across runs.
- **Concurrency**: no shared mutable state; the platform calls hooks sequentially per
  tool; no thread-safety requirements.

## Usages Analysis

### `conventions`

- **What it provides**: mandatory Python rules — 3.10+ compatibility, relative
  intra-package imports, Google-style docstrings, blank-line block separation, pydantic
  data-model rules, and the full testing standard (structure, naming, mocks policy,
  venv execution).
- **Where used**: global `Annotations`; `Constraints` of both routines.
- **Why chosen**: project-wide code and test law; referenced wherever code style binds.
- **How exactly**: `registration.py` and `__init__.py` follow the import, docstring, and
  formatting rules; the test stack below follows the test-structure and naming rules
  (mirrored `tests/` layout, `test_<what>_<scenario>` names, duck-typed stubs, no mocks
  needed — pure logic). The pydantic/logging sections do not apply (no data models; no
  logging by explicit contract). The venv constraint is honored via `/opt/project` (see
  Additional Instructions).

### `goga-dependency`

- **What it provides**: the platform dependency policy — empty runtime dependencies,
  `goga>=2.0` only in the `test` extra, `TYPE_CHECKING`-only platform references, an
  import-clean facade, tests on duck-typed stubs.
- **Where used**: global `Annotations`; `Constraints` of both routines.
- **Why chosen**: the package must install and import anywhere while extending a platform
  it never imports at runtime.
- **How exactly**: `registration.py` opens with `from __future__ import annotations` and
  guards both platform imports under `if TYPE_CHECKING:` — verified public import paths
  on goga 2.0.2: `from goga.hooks.tools.registration import HookRegistrar` (not re-exported
  higher) and `from goga.config.hooks import ConfigAmendment` (public facade).
  `pyproject.toml` gains `"goga>=2.0"` in `[project.optional-dependencies].test`;
  `[project.dependencies]` stays `[]`.

### `config-amend`

- **What it provides**: the `config / amend_config` amendment-view contract — the
  read-and-amend surface, `set`/`force` semantics, silence markers, merge rules
  (authored-wins, force-beats-set, enumeration order), hard-action failure treatment,
  run-output rules.
- **Where used**: global `Annotations`; `review_presets` annotations.
- **Why chosen**: it is the normative contract of the single checkpoint the tool
  subscribes to.
- **How exactly**: reads go through `context.config` attribute navigation; writes are two
  `set` calls on model-known dotted leaf paths; `force` is never used; authored-wins is
  never re-derived; failure is `ValueError` only. Verified against the installed
  `ConfigAmendment.set/force` and the overlay merge.

### `hook-registration`

- **What it provides**: the facade-callback contract — `register_hooks` shape, the
  four-argument `subscribe`, hook signature projection by declared parameter names
  (`context`, `self`), registration timing, failure behavior of registration.
- **Where used**: global `Annotations`; `register_hooks` annotations.
- **Why chosen**: it defines how the tool's single subscription enters the platform.
- **How exactly**: `register_hooks(hooks)` performs one
  `hooks.subscribe("config", "amend_config", "review_presets", review_presets)`;
  `review_presets` declares exactly `context` so the delivery injects the amendment view
  by name. Verified against the installed `HookRegistrar.subscribe` and
  `build_hook_arguments`.

### Imported Usages

- None (no `Imports` in the manifest).

## `.usages/` Update

### Cell: `goga_tool_basic_build`

#### Existing Files — Consistency

- **`registration`** → `goga_tool_basic_build/.usages/registration.md`
  - Status: **current**. Describes the facade import, the single subscription
    (domain/action/name/callable match the contract), the hook's purity, the two
    conflicts, and the two buffered presets. No additions or updates needed.
- **`profile`** → `goga_tool_basic_build/.usages/profile.md`
  - Status: **current**. The guarantee (effective values where authored is silent), the
    one tuning knob (`max_iterations` authored-wins; `strategy: medium` accepted), the
    stderr summary, byte-identical authored file, reversibility, and coexistence caveat
    all match the verified platform merge behavior. No additions or updates needed.
- **`conflicts`** → `goga_tool_basic_build/.usages/conflicts.md`
  - Status: **updated** (design review). The two conflicts, fixed order, error shape (tool,
    action, path, resolution; never the value), the not-a-conflict list (authored cap,
    `medium`, blank-as-unset, absent/null `additional`, leaves outside the two review
    leaves), and recovery match the contract and the verified loader/merge semantics. The
    example error text was aligned with the byte-exact platform composition
    (`hook review_presets of tool basic-build failed on config.amend_config: <reason>`,
    ASCII hyphen), replacing the earlier consumer-facing rendering with an em dash.

#### New Files (if any)

- None — both routines are already covered by the existing three files (registration for
  the facade/subscription domain, profile for the guarantee domain, conflicts for the
  failure domain); no new functional domain appears.

## Test Stack Trace

### General Setup

All tests run on **duck-typed stubs** (`goga-dependency` policy #5) — no goga objects, no
mocks (pure logic; the conventions' mock policy keeps business-logic tests mock-free).
Shared fixtures live in `tests/conftest.py`:

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

Layout (mirrors the flat package per the conventions — root-package modules test directly
into `tests/`):

```
tests/
├── __init__.py
├── conftest.py
├── test_init.py           # facade tests
└── test_registration.py   # register_hooks + review_presets tests
```

Test modules reach the stubs by an explicit relative import — pytest injects
fixtures, never plain helper names, from `conftest.py` (import only the names the
file uses; the registrar itself arrives via the `registrar` fixture):

```python
from .conftest import StubSection, make_amendment
```

### Source File Registry

- `goga_tool_basic_build/__init__.py` — facade (tested by `test_init.py`)
- `goga_tool_basic_build/registration.py` — both routines (tested by
  `test_registration.py`)

---

### Positive Tests

#### `test_register_hooks_subscribes_single_config_amend_hook`

**Setup**: `registrar` fixture (empty `StubRegistrar`).

**Input**: `register_hooks(registrar)`.

**Trace**:
```
register_hooks(registrar)
  → registrar.subscribe("config", "amend_config", "review_presets", review_presets)
    side effect: registrar.calls = [("config", "amend_config", "review_presets", <function review_presets>)]
  → return None
```

**Assertions**:
```
len(registrar.calls) == 1
registrar.calls[0][:3] == ("config", "amend_config", "review_presets")
registrar.calls[0][3] is goga_tool_basic_build.registration.review_presets
```

**Sufficiency**: pins the contract's "exactly one subscription" requirement and the exact
address — prevents regressions where a second domain/action is subscribed, the hook name
drifts, or a wrapper/delayed callable is registered instead of the module function.

---

#### `test_review_presets_buffers_both_presets_on_absent_build`

**Setup**: `amendment = make_amendment(build_present=False)`.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → build = amendment.config.build          # None
  → review = None                            # guarded
  → strategy = None; additional = None       # both guards pass
  → amendment.set("build.review.strategy", "medium")    # buffer: [("build.review.strategy", "medium")]
  → amendment.set("build.review.max_iterations", 5)     # buffer: [.., ("build.review.max_iterations", 5)]
  → return None
```

**Assertions**:
```
amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
amendment.forces == []
```

**Sufficiency**: the core guarantee — absent intermediate branches do not block the
presets; pins exact paths, values, order, and the set-only intent.

---

#### `test_review_presets_buffers_both_presets_on_absent_review`

**Setup**: `amendment = make_amendment(review_present=False, build_present=True)`.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → build = StubSection(review=None); review = None
  → both guards pass (no review section)
  → two set buffers as above
```

**Assertions**:
```
amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
amendment.forces == []
```

**Sufficiency**: the second absence shape — `build` present with `review` absent — must
behave identically; prevents an `AttributeError`-style navigation regression on the
half-present branch.

---

#### `test_review_presets_accepts_authored_medium_strategy`

**Setup**: `amendment = make_amendment(strategy="medium")` (no additional).

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → strategy = "medium"                      # present, not blank, equals "medium"
  → no raise
  → additional = None                        # guard passes
  → two set buffers
```

**Assertions**:
```
no exception
amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
```

**Sufficiency**: authored `medium` is accepted silently and the hook still buffers both
sets — pins that authored-wins is the merge's business, never suppressed buffering at the
hook level.

---

#### `test_review_presets_buffers_presets_with_authored_max_iterations`

**Setup**: `amendment = make_amendment(max_iterations=8)` (the review stub carries
`max_iterations = 8`; strategy and additional stay None).

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → strategy None, additional None           # guards pass; max_iterations never read
  → two set buffers (the cap preset included)
```

**Assertions**:
```
no exception
("build.review.max_iterations", 5) in amendment.sets
amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
```

**Sufficiency**: the "one tuning knob" guarantee — an authored cap never conflicts and
never suppresses the buffered preset; the merge, not the hook, drops it.

---

#### `test_review_presets_write_footprint_is_exactly_two_set_amendments`

**Setup**: `amendment = make_amendment()` (silent configuration).

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → guards pass
  → exactly two set calls; zero force calls; no other channel touched
```

**Assertions**:
```
len(amendment.sets) == 2
len(amendment.forces) == 0
sorted(path for path, _ in amendment.sets) == ["build.review.max_iterations", "build.review.strategy"]
```

**Sufficiency**: the exact write footprint — prevents regressions where a `force`
appears, a third leaf (notably `build.review.additional.*`) is contributed, or a path
typo slips in; each preset value is asserted by the preceding tests.

---

### Negative Tests

#### `test_review_presets_raises_on_non_medium_strategy` (parametrized: `"short"`, `"full"`, `"quick"`)

**Setup**: `amendment = make_amendment(strategy=value)` for each param.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → strategy = value                         # present, non-blank, != "medium"
  → raise ValueError("refused the authored configuration at build.review.strategy - remove the authored strategy or uninstall the tool")
  → nothing buffered
```

**Assertions**:
```
with pytest.raises(ValueError, match="build.review.strategy"):
    review_presets(amendment)
amendment.sets == []
```

**Sufficiency**: the strategy conflict — including the platform-valid values `short` and
`full` — stops the hook before any buffering; the whole contribution is discarded (empty
buffer), matching the hard-action treatment.

---

#### `test_review_presets_error_names_path_and_resolution_without_value`

**Setup**: `amendment = make_amendment(strategy="full")`.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → raise ValueError(strategy message)
  → message contains the path and the resolution; never the authored value
```

**Assertions**:
```
with pytest.raises(ValueError, match="refused the authored configuration at build.review.strategy") as excinfo:
    review_presets(amendment)
message = str(excinfo.value)
"build.review.strategy" in message
"remove the authored strategy or uninstall the tool" in message
"full" not in message
```

**Sufficiency**: the value-secrecy invariant — the single most safety-critical property
of the tool's output; prevents a regression that leaks an authored value into a
platform-rendered error.

---

#### `test_review_presets_raises_on_populated_additional`

**Setup**: `amendment = make_amendment(additional=StubSection(agent="codex", patience=3, max_iterations=15))`.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → strategy None                            # guard passes
  → additional is StubSection(...)           # not None → conflict
  → raise ValueError("refused the authored configuration at build.review.additional - remove the additional section or uninstall the tool")
  → nothing buffered
```

**Assertions**:
```
with pytest.raises(ValueError, match="build.review.additional"):
    review_presets(amendment)
amendment.sets == []
```

**Sufficiency**: the additional conflict for a populated section — the basic profile
refuses any external-review tuning; strategy had passed, proving the second guard fires
on its own.

---

#### `test_review_presets_raises_on_empty_additional_mapping`

**Setup**: `amendment = make_amendment(additional=StubSection())` — present but empty,
mirroring the loader's `AdditionalReviewConfig()` instance for `additional: {}`.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → additional is StubSection()              # present-but-empty is still not None
  → raise ValueError (additional message)
  → nothing buffered
```

**Assertions**:
```
with pytest.raises(ValueError, match="build.review.additional"):
    review_presets(amendment)
amendment.sets == []
```

**Sufficiency**: the sharpest edge of the conflict — `additional: {}` conflicts while
absent/null does not; pins the `is not None` presence semantics against a future
"falsy-means-absent" refactor.

---

#### `test_review_presets_reports_strategy_conflict_first`

**Setup**: `amendment = make_amendment(strategy="short", additional=StubSection())`.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → strategy guard fires first ("short" != "medium")
  → raise ValueError (strategy message); the additional guard never runs
```

**Assertions**:
```
with pytest.raises(ValueError, match="build.review.strategy") as excinfo:
    review_presets(amendment)
"build.review.additional" not in str(excinfo.value)
```

**Sufficiency**: the fixed check order — deterministic error selection when both
conflicts are present; prevents a reorder that would report the additional conflict
first.

---

### Edge Case Tests

#### `test_review_presets_treats_blank_strategy_as_unset` (parametrized: `None`, `""`, `"   "`)

**Setup**: `amendment = make_amendment(strategy=value)` for each param (for `None`,
`review_present=True` with `strategy=None`).

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → strategy is None or blank → unset → no conflict
  → additional None → no conflict
  → two set buffers (the strategy preset included)
```

**Assertions**:
```
no exception
amendment.sets == [("build.review.strategy", "medium"), ("build.review.max_iterations", 5)]
```

**Sufficiency**: blank reads as unset — no conflict and the preset still buffered; on the
real platform the loader already delivered `None`, so this also pins the hook's defensive
normalization for duck-typed deliveries.

---

#### `test_review_presets_conflicts_on_non_string_strategy` (parametrized: `42`, `True`)

**Setup**: `amendment = make_amendment(strategy=value)` — a duck-typed delivery of a
non-string strategy (`StubSection(strategy=42, additional=None, ...)`); no registrar
needed.

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → build = StubSection(review=...); review = StubSection(strategy=42, ...)
  → strategy = 42
  → strategy is not None; isinstance(strategy, str) is False → not unset
  → normalized = 42 (a non-str passes through as itself); 42 != "medium" → conflict
  → raise ValueError (strategy message); nothing buffered
```

**Assertions**:
```
with pytest.raises(ValueError, match="build.review.strategy"):
    review_presets(amendment)
amendment.sets == []
```

**Sufficiency**: the invalid-type edge case mandated by `conventions` — pins that a
duck-typed non-string strategy delivery conflicts instead of crashing (`AttributeError`
on `.strip()`) or being silently accepted; guards the defensive isinstance branch the
real platform never exercises (the loader rejects a non-string strategy before the
checkpoint). `True` is the classic YAML footgun (yes/no parses as bool). Verified against
the live end-to-end simulation (stub-delivered non-string → strategy conflict, no crash).

---

#### `test_review_presets_skips_conflict_when_additional_absent_or_null`

**Setup**: `amendment = make_amendment(additional=None)` (absent and YAML-null are the
same `None` at the hook).

**Input**: `review_presets(amendment)`.

**Trace**:
```
review_presets(amendment)
  → additional is None → not a conflict
  → two set buffers
```

**Assertions**:
```
no exception
("build.review.strategy", "medium") in amendment.sets
```

**Sufficiency**: the complement of the empty-mapping test — absence must never conflict;
together with the `{}` test it pins the exact presence boundary.

---

#### `test_facade_reexports_contract_api` (in `test_init.py`)

**Setup**: none (a fresh interpreter state is not required; the facade is import-only).

**Input**: `import goga_tool_basic_build`.

**Trace**:
```
import goga_tool_basic_build
  → __init__.py executes `from .registration import register_hooks, review_presets`
  → module attributes bound; no goga import at runtime
```

**Assertions**:
```
goga_tool_basic_build.register_hooks is goga_tool_basic_build.registration.register_hooks
goga_tool_basic_build.review_presets is goga_tool_basic_build.registration.review_presets
goga_tool_basic_build.__all__ == ["register_hooks", "review_presets"]
callable(goga_tool_basic_build.register_hooks)
callable(goga_tool_basic_build.review_presets)
```

**Sufficiency**: the facade contract — the platform consumes
`from goga_tool_basic_build import register_hooks, review_presets`; a facade that fails
to re-export is fatal to every goga command enumerating tool packages.

---

#### `test_facade_import_requires_no_goga` (in `test_init.py`)

**Setup**: run in a subprocess with the project on `sys.path` (the test venv has goga
installed, so the in-process `sys.modules` check is performed in a clean child instead):

**Input**: `python -c "import goga_tool_basic_build; import sys; sys.exit(0 if 'goga' not in sys.modules else 1)"`.

**Trace**:
```
subprocess python
  → import goga_tool_basic_build
    → __init__ → registration (TYPE_CHECKING block never executes)
    → 'goga' never enters sys.modules
  → exit code 0
```

**Assertions**:
```
subprocess returncode == 0
```

**Sufficiency**: the import-safety policy end-to-end — the facade imports cleanly without
goga at runtime (`goga-dependency` #3/#4); catches a `TYPE_CHECKING` block leaking to
runtime or an accidental top-level goga import.

---

## Additional Instructions for the Implementation Agent

- **Files to create**: `goga_tool_basic_build/registration.py` (both routines per
  `location:`), `goga_tool_basic_build/__init__.py` (the facade — recreate the deleted
  empty file as the re-exporting facade below), `tests/__init__.py`, `tests/conftest.py`,
  `tests/test_registration.py`, `tests/test_init.py`.
- **Facade exact shape** (`goga_tool_basic_build/__init__.py`):

  ```python
  """The goga-tool-basic-build package facade: the contract API of the basic review profile tool."""

  from .registration import register_hooks, review_presets

  __all__ = ["register_hooks", "review_presets"]
  ```

- **`registration.py` skeleton** (order and mechanics are binding; docstrings per
  `conventions` Google style, with `Raises:` sections):

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

  Then `register_hooks(hooks: HookRegistrar) -> None` and
  `review_presets(context: ConfigAmendment) -> None` per the Algorithm Design section,
  with the two message literals built from `_STRATEGY_PATH` / the additional path —
  message text stays ASCII-only (RUF001).
- **`pyproject.toml`**: add `"goga>=2.0"` to `[project.optional-dependencies].test`;
  `[project.dependencies]` stays empty. No other metadata changes.
- **No other leaves, no `force`, no logging, no prints** — value secrecy and silence are
  contract constraints, not preferences.
- **Environment**: develop and validate in a venv **outside the project tree** at
  `/opt/project` (create if missing; install the project with the `test` extra:
  `pip install -e '.[test]'`). If `/opt` is not writable in the execution environment,
  fall back to `$HOME/.venvs/goga-tool-basic-build` — still outside the project tree;
  never create the venv inside the repository. Validation commands, in that venv, from
  the project root: `pytest tests/ -x`, `ruff check goga_tool_basic_build/`,
  `python -c "import goga_tool_basic_build"` (facade check).
- **Do not** add anything to `build.review.additional`, subscribe any other address,
  validate leaves beyond the two review leaves, or write integration tests against the
  real platform merge (duck-typed stubs only — ADR decision).
