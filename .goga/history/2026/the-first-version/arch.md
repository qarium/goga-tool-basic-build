# Architecture Plan — goga-tool-basic-build

## Topic

**goga-tool-basic-build** — the basic review profile hook tool.
Plan file: `.goga/history/2026/the-first-version/arch.md`

## Implementation Order

| # | Cell | Status | Reason for position |
|---|---|---|---|
| 1 | `goga_tool_basic_build` | **create anew** | The only cell of the architecture; has no `Imports` (greenfield, single-cell package) — simultaneously leaf and root, so it is designed and created first. |

All artifacts are created anew (Artifact Resolution: `create new cell`; `goga schema` was empty — `[]`). No existing CODEMANIFEST is modified.

## Artifacts

### Cell: `goga_tool_basic_build` (create)

#### CODEMANIFEST — `goga_tool_basic_build/CODEMANIFEST`

```yaml
Usages:
  conventions: .goga/usages/conventions.md
  goga-dependency: .goga/usages/cooks/goga-dependency.md
  config-amend: .goga/usages/github/goga/config/registering-hooks.md
  hook-registration: .goga/usages/github/goga/hooks/registering-hooks.md

Annotations: |
  Use `conventions` for code writing rules and testing.

  The cell is a hook-only goga tool: it exposes no command of its own; its
  entire behavior manifests through the platform's configuration amendment
  checkpoint.

  Use `goga-dependency` for the platform dependency policy: runtime
  dependencies stay empty, platform types are referenced under TYPE_CHECKING
  only, and the package facade stays import-clean without goga installed.

  Use `config-amend` for the amendment view contract the hook operates on:
  set semantics, silence markers, merge rules, and hard-action failure
  treatment.

  Value secrecy: any message the cell produces names configuration paths at
  most — never configuration values.

  The tool is silent by design: no stdout/stderr output, no logging — run
  feedback belongs to the platform.

---

"register_hooks(hooks: HookRegistrar)":
  location: registration.py
  annotations: |
    Subscribe the tool's single hook to the platform's configuration
    amendment action — the only subscription of the tool.

    `hooks`: the platform subscription surface delivered by goga when a
    command first reaches a hook checkpoint; use `hook-registration` for its
    contract.

    Algorithm:
    1. Subscribe one hook: domain "config", action "amend_config", hook name
       "review_presets", callable `review_presets`

    Requirements:
    - Exactly one subscription; no other domain action is subscribed

    Constraints:
    - Do not import goga at runtime — follow `goga-dependency`
    - Use `conventions` for code style and docstrings

"review_presets(context: ConfigAmendment)":
  location: registration.py
  annotations: |
    The tool's single amendment hook: guard the two basic-profile conflicts
    in a fixed order, then buffer the two review presets. A pure function
    over the delivered read-and-amend view — no I/O, no state.

    `context`: the read-and-amend view over the authored configuration; use
    `config-amend` for its read surface and set semantics.

    Algorithm:
    1. Read the authored build.review.strategy leaf: if it is present and
       not the value medium, raise ValueError naming the path
       build.review.strategy and the resolution (remove the authored
       strategy or uninstall the tool)
    2. Read the authored build.review.additional section: if it is present
       with any contents — including an empty mapping — raise ValueError
       naming the path build.review.additional and the resolution (remove
       the section or uninstall the tool); an absent or null section is not
       a conflict
    3. Buffer a set amendment of build.review.strategy to medium
    4. Buffer a set amendment of build.review.max_iterations to 5

    Requirements:
    - An authored strategy that is absent, null, or blank (empty or
      whitespace-only) counts as unset — no conflict
    - Both set amendments are buffered unconditionally, including when the
      authored configuration already carries values at those leaves and
      when intermediate branches (build, build.review) are absent
    - The strategy conflict is checked before the additional conflict; when
      both are present the strategy one is reported
    - Error messages name the path and the resolution only

    Constraints:
    - Authored-wins belongs to the platform merge layer — never re-derive
      it inside the hook
    - Never use a force amendment; never contribute to
      build.review.additional or any leaf beyond the two presets
    - Fail only through ValueError on the two conflicts
    - No configuration value may appear in any message
    - Follow `goga-dependency` for platform type references and
      `conventions` for code style

---

Author: Goga
CreatedAt: 04/10/26
Description: |
  The basic review profile tool: one subscription to the platform's
  configuration amendment action and one hook guarding two conflicts while
  buffering two review presets.
```

#### .usages/ files

**File:** `goga_tool_basic_build/.usages/registration.md` (practice key: `registration`)

```md
# Consuming the package facade

How the goga platform — or any embedding host — consumes `goga_tool_basic_build`
as an installed tool package. For platform integrators and anyone embedding the
package; a project maintainer who only installs the tool needs nothing from
this file.

## The facade

The package root is the facade. Importing it must always succeed, with or
without goga installed — a facade that fails to import is fatal to every goga
command that enumerates tool packages:

```python
from goga_tool_basic_build import register_hooks, review_presets
```

The package carries no runtime dependency on goga: the platform types
(`HookRegistrar`, `ConfigAmendment`) are type-checking references only.

## Registering the hooks

The host calls `register_hooks(hooks: HookRegistrar)` with its subscription
surface — the platform does this when a command first reaches a hook
checkpoint. The call subscribes exactly one hook:

- domain `config`, action `amend_config`, name `review_presets`, callable
  `review_presets`.

No other domain action is subscribed, and the tool has no command of its own.

## What the hook does

`review_presets(context: ConfigAmendment)` is a pure function over the
read-and-amend view delivered at the configuration load moment. It guards the
two basic-profile conflicts — raising `ValueError` that names the configuration
path, never a value — and buffers two apply-where-silent amendments:
`build.review.strategy` = medium and `build.review.max_iterations` = 5.

The hook performs no I/O and produces no output; the amendment summary and the
hard failure reporting belong to the platform.
```

**File:** `goga_tool_basic_build/.usages/profile.md` (practice key: `profile`)

```md
# Relying on the basic review profile

What `goga_tool_basic_build` guarantees in every configuration-consuming run of
your project, and how to lean on it. For maintainers who installed the tool
(via `goga install basic-build` or a `tools:` declaration) and for contributors
who need the same effective behavior locally and in CI.

## The guarantee

Where your authored `.goga/config.yml` is silent at the review leaves, every
configuration-consuming goga command carries the effective values:

```yaml
# authored (minimal)     # effective in every run
language: python         language: python
                         build:
                           review:
                             strategy: medium
                             max_iterations: 5
```

- Absent intermediate branches (`build`, `build.review`) do not block the
  presets — a configuration of `language` alone receives the full profile.
- The run prints a short amendment summary to stderr naming the tool and each
  applied path; `goga config` prints the effective values.
- The authored file is never modified — it stays byte-identical after every
  run; the effective configuration lives in memory for the current run.
- Repeated runs with the same tools and the same file reproduce the same
  effective configuration.

## The one tuning knob

An authored `build.review.max_iterations` always wins over the preset —
silently, no warning, no error:

```yaml
build:
  review:
    max_iterations: 8   # effective cap is 8; strategy stays medium
```

An authored `build.review.strategy: medium` is likewise accepted silently. The
tool never overwrites an authored value.

## Verifying

```bash
goga config   # prints effective (amended) values; stdout stays data-clean
```

## Reversibility

Uninstalling the tool — and removing its `tools:` declaration — returns the
project to exactly its authored effective configuration; no residue remains.

## Coexistence

goga tools are mutually blind. Installing another review-preset tool alongside
this one makes the effective strategy enumeration-dependent; the guarantee
holds when this is the sole review-preset tool in the environment.
```

**File:** `goga_tool_basic_build/.usages/conflicts.md` (practice key: `conflicts`)

```md
# Resolving configuration conflicts

The two authored settings `goga_tool_basic_build` deliberately refuses, the
errors they produce, and how to recover. For maintainers and contributors whose
goga command stopped at configuration load.

## What stops the command

Both checks are hard: every configuration-consuming goga command stops before
doing anything else, the tool's whole contribution is discarded (nothing
applies partially), and the authored file stays byte-identical.

1. **Strategy conflict** — an authored `build.review.strategy` that is present
   and not `medium` (including the valid values `short` and `full`):

```yaml
build:
  review:
    strategy: short    # any value other than medium conflicts
```

2. **`additional` conflict** — an authored `build.review.additional` section
   with any contents, including an empty mapping:

```yaml
build:
  review:
    additional: {}      # any contents conflict — a basic build does not tune external review
```

When both conflicts are present in one configuration, the strategy one is
reported — the checks run in a fixed order, so the outcome is deterministic.

## The error shape

The error names the tool, the action, and the configuration path, and suggests
the resolution. It never reveals the authored value:

```text
goga-tool-basic-build: amend_config refused the authored configuration at
build.review.strategy — remove the authored strategy or uninstall the tool
```

## What is not a conflict

- An authored `build.review.max_iterations` — never conflicts; it wins over
  the preset silently.
- An authored `build.review.strategy: medium` — accepted silently.
- A blank (empty or whitespace-only) authored strategy — reads as unset; no
  conflict is raised and the strategy preset is still buffered.
- An absent or YAML-null `build.review.additional` — not a conflict.
- Any authored leaf outside the two review leaves — review roles, agents,
  environment values, any other setting — the tool neither validates nor
  touches it.

## Recovery

- Remove the conflicting authored section (the strategy leaf, or the whole
  `additional` mapping), or
- uninstall the tool and remove its `tools:` declaration — the project returns
  to exactly its authored behavior.

Command-line flags of goga commands are runtime overrides of the effective
configuration — they neither trigger nor bypass these conflicts.
```

## Dependency Map

```
                     ┌──────────────────────────────┐
                     │        goga platform         │
                     │  (external boundary; the     │
                     │   platform is not modified)  │
                     └──────────────┬───────────────┘
        enumerate goga_tool_*       │ call register_hooks(hooks)
        import facade (goga-free)   │ deliver context: ConfigAmendment
                                    ▼
               ╔══════════════════════════════════════╗
               ║  cell: goga_tool_basic_build          ║
               ║  CODEMANIFEST                         ║
               ║    routine register_hooks             ║
               ║    routine review_presets             ║
               ║  .usages/ registration | profile |    ║
               ║           conflicts                   ║
               ╚══════════════════════════════════════╝

In-project Imports: none (single-cell architecture; dependency graph = 1 node).
Circular dependencies: none possible.
```

## Verification Checklist

**After materializing the artifacts:**

- [ ] `goga lint goga_tool_basic_build/` reports 0 errors — header/body/footer order, `location: registration.py` at cell level, backtick references resolve only to usages (`conventions`, `goga-dependency`, `config-amend`, `hook-registration`), types, or signature parameters
- [ ] `goga schema` lists the cell `goga_tool_basic_build` with types `register_hooks`, `review_presets` and the three `.usages/` files (registration, profile, conflicts)

**After implementing the contract:**

- [ ] Import-clean facade: `python -c "import goga_tool_basic_build"` succeeds in an environment without goga (runtime dependencies empty; platform types under `TYPE_CHECKING` per `goga-dependency`)
- [ ] `register_hooks` subscribes exactly one hook: domain "config", action "amend_config", hook name "review_presets" — no other subscription
- [ ] On a silent configuration the hook buffers exactly two set amendments: `build.review.strategy` = medium, `build.review.max_iterations` = 5 — unconditional, absent intermediate branches included
- [ ] Authored values never warn or error at the hook level (authored cap; authored `medium`); blank/whitespace strategy reads as unset
- [ ] Strategy conflict (present and not medium) raises `ValueError` naming `build.review.strategy`; additional conflict (any contents, including `{}`) raises `ValueError` naming `build.review.additional`; absent/null additional does not; with both present the strategy error is raised (fixed order)
- [ ] No configuration value appears in any error message; write footprint is exactly the two leaves; nothing into `build.review.additional`; no force amendment anywhere
- [ ] `pytest tests/ -x` and `ruff check goga_tool_basic_build/` pass in a venv; `pyproject.toml` carries `goga>=2.0` in the `test` extra only; tests run on duck-typed stubs per `conventions`
