# Basic Review Profile for goga Builds — goga-tool-basic-build

## Problem

Teams running goga builds who want a moderate, bounded review pass have no
explicit, guaranteed review profile.

Today the review behavior of a project rests on implicit platform defaults and
per-project hand-authoring: the review strategy defaults to `medium` but the
default is nowhere guaranteed, and the review iteration cap has no default at
all — an unconfigured project inherits whatever the platform resolves at run
time. Projects that want a predictable "basic" build must hand-author the
review knobs, and the optional external-review tuning section
(`build.review.additional`) invites configurations that quietly diverge from
the team's intent.

The consequence: review depth and cost vary across projects and across runs of
the same project, and a divergence from the intended profile is discovered
late — at review time or never — rather than at configuration load time. For a
team that picked a basic build profile precisely for its predictability, that
variance is the problem.

## Users

**Primary user — the goga project maintainer (external consumer).** A
developer maintaining any goga project who wants a standard, bounded review
without hand-authoring review knobs. They install `goga-tool-basic-build` into
the project environment once (via `goga install basic-build` or a `tools:`
declaration in `.goga/config.yml`), and from the first configuration-consuming
run onwards they expect the guaranteed profile. They may occasionally tune one
knob — the review iteration cap — and expect their authored value to be
respected.

**Secondary actors — project contributors and CI runners.** They run goga
commands in a project where the maintainer installed the tool. They did not
choose the tool and do not know its internals; they need identical effective
review behavior locally and in CI, and a self-explanatory error when the
authored configuration conflicts with the profile.

All users are technical (CLI and configuration-file users); the product has no
graphical interface, and none is needed.

## Goals

1. **Guaranteed basic review profile.** In every goga project where the tool
   is installed, every configuration-consuming run carries a moderate review
   strategy (`medium`) and a bounded review iteration cap (5 by default) —
   without any hand-authoring.
2. **One natural tuning knob.** The review-level iteration cap remains the
   user's single point of control over review cost: an authored
   `build.review.max_iterations` always wins over the preset, silently.
3. **Early, loud conflict surfacing.** When the authored configuration
   contradicts the basic profile — a different strategy, or any external-review
   `additional` tuning — every configuration-consuming command stops
   immediately at configuration load with a clean, actionable error. A
   divergence never passes silently into a run.
4. **Safe adoption and removal.** Adopting the tool leaves the authored
   configuration file untouched, and removing the tool returns the project to
   exactly its authored behavior.

## User Experience

**Entry point.** The maintainer installs the pip package
`goga-tool-basic-build` (`goga install basic-build`, or by declaring it under
`tools:` so that `goga install` picks it up). The tool has no command of its
own and no file to edit for its part: its entire behavior manifests at the
moment a goga command loads `.goga/config.yml`. The guarantee starts from the
first configuration-consuming run after installation.

**Primary scenario — authored configuration is silent.** The project's
`.goga/config.yml` contains no review settings (a minimal configuration of
`language` alone is enough). Every configuration-consuming goga command now
carries the effective review values `build.review.strategy: medium` and
`build.review.max_iterations: 5`. The run prints a short amendment summary to
stderr naming the tool and each applied path; `goga config` prints the
effective values. The authored file is never modified, and repeated runs
produce the identical effective configuration.

**Alternative — the maintainer tunes the cap.** The maintainer authors
`build.review.max_iterations: 8`. No error, no warning: the effective
configuration is `strategy: medium` with the cap 8 — the authored value wins
silently, and the strategy preset still applies.

**Alternative — the maintainer authors the preset strategy.** Authored
`build.review.strategy: medium` matches the profile and is accepted without
error.

**Failure — authored strategy conflicts.** The authored configuration sets
`build.review.strategy` to any value other than `medium` (including the valid
values `short` and `full`). Every configuration-consuming goga command stops
before doing anything else with a clean error naming the tool, the action, and
the path `build.review.strategy`. The error never reveals the authored value.
Nothing is applied — the tool's contribution is discarded as a whole, not
partially — and the authored file remains byte-identical. Recovery: remove the
authored strategy or uninstall the tool.

**Failure — authored `additional` section.** The authored configuration
contains the section `build.review.additional` with any contents — including an
empty mapping. Every configuration-consuming command stops the same way: a
clean error naming the tool, the action, and the path
`build.review.additional`; nothing is applied; the file is untouched. Recovery:
remove the section (a basic build does not tune external review) or uninstall
the tool. When both conflicts are present in one configuration, the strategy
conflict is the one reported — the checks run in a fixed order, so behavior is
deterministic.

**Feedback.** The user-visible surfaces are: the per-run amendment summary on
stderr (tool, path, applied operation — never values), the effective values
printed by `goga config`, and the conflict errors described above. When no
amendment applies, nothing is printed. Command-line flags of goga commands
(such as the review-patience override) are runtime overrides of the effective
configuration, not part of the authored file — they neither trigger nor bypass
the conflicts.

**Consequences and recovery.** The tool modifies nothing on disk and performs
no destructive action. Uninstalling it (and removing its `tools:` declaration)
returns the project to exactly its authored behavior; no residue remains.

**Coexistence caveat.** goga tools are mutually blind: each reads only the
authored configuration, and when two tools contribute the same path the later
one in enumeration order wins. Installing another review-preset tool (such as
`goga-tool-simple-build`) alongside this one therefore yields an
enumeration-dependent strategy, and the guarantee of this tool holds only when
it is the sole review-preset tool in the environment. The tool does not detect
or warn about other tools; this is a documented adoption condition, not a
feature.

## Requirements

**Activation**

1. Once `goga-tool-basic-build` is installed in the environment of a goga
   project, every goga command that loads `.goga/config.yml` must carry the
   basic review profile defined below. The behavior applies from the first
   such run after installation, without reinstallation or project changes.
2. The tool must expose no command of its own: all of its behavior manifests
   through the configuration load of goga commands.

**Basic review profile**

3. Where the authored configuration is silent at `build.review.strategy`, the
   effective value must be `medium`.
4. Where the authored configuration is silent at
   `build.review.max_iterations`, the effective value must be `5`.
5. Absent intermediate branches (`build`, `build.review`) must not prevent the
   presets: a configuration of `language` alone must receive the full profile.
6. Determinism: the same installed tools and the same authored file must
   always produce the same effective configuration.

**Authored values**

7. An authored `build.review.max_iterations` must win over the preset value of
   5, silently — no warning, no error — while the strategy preset still
   applies.
8. An authored `build.review.strategy` of exactly `medium` must be accepted
   without error.
9. The tool must never overwrite an authored value: its contributions apply
   only where the authored configuration is silent. (An authored empty or
   whitespace-only strategy string counts as unset, per the platform's
   value normalization — the preset applies.)

**Conflict: strategy**

10. If the authored `build.review.strategy` is present and is not `medium`,
    every configuration-consuming goga command must stop with a clean error
    naming the tool, the action, and the path `build.review.strategy`, and
    suggesting the resolution (remove the authored strategy or uninstall the
    tool).
11. The error must not reveal the authored value; the tool's entire
    contribution must be discarded (nothing partial applies); the authored
    file must remain byte-identical.

**Conflict: `additional` section**

12. If the authored configuration contains the section
    `build.review.additional` — with any contents, including an empty mapping
    (`{}`) — every configuration-consuming command must stop with a clean
    error naming the tool, the action, and the path
    `build.review.additional`, and suggesting the resolution (remove the
    section or uninstall the tool). The same no-leak, no-partial-apply,
    no-modification guarantees as requirement 11 apply.
13. An absent or YAML-null `additional` is not a conflict.

**Check order**

14. When both conflicts are present in one authored configuration, the
    strategy conflict must be the one reported; the outcome must be
    deterministic.

**Feedback**

15. When presets are applied, the run must print a short amendment summary to
    stderr — one line per applied contribution: tool, path, operation. When
    nothing applies, nothing must be printed.
16. Configuration values must never appear in the amendment summary, in
    informational output, or in any error message. Paths may be named; values
    may not.
17. `goga config` must print the effective (amended) values with data-clean
    stdout.

**Footprint**

18. The authored `.goga/config.yml` must never be modified by the tool — it
    stays byte-identical after every run.
19. Removing the tool from the environment must return the project to exactly
    its authored effective configuration.

**Non-goals of the behavior**

20. The tool must not validate, warn about, or alter anything beyond the two
    conflicts and the two preset leaves: no agent-presence checks, no review
    roles validation, no strategy whitelist enforcement (the platform owns
    those), no touching of tasks-pass (`build` root) settings, environment
    values, or any other leaf.
21. The tool must not map the review-level iteration cap into
    `build.review.additional.max_iterations`; it contributes nothing to the
    `additional` branch.

## Constraints

- **Platform extension point.** The tool extends goga only through the
  configuration amendment checkpoint of the goga platform; goga itself is not
  modified. The checkpoint fires when a command loads `.goga/config.yml`,
  after the authored file is loaded and before any consumer reads it, and it
  is a hard action: the first failing tool stops the command and that tool's
  whole contribution is discarded.
- **Authored-wins merge semantics.** Contributions apply only where the
  authored configuration is silent; the tool cannot and must not override
  authored values (the override form is excluded by the tool's contract).
- **Value secrecy.** goga never prints configuration values; all tool output,
  including errors, names paths at most.
- **Tool discovery and identity.** Tools are discovered as installed
  `goga_tool_*` packages; identity is assigned from the package name — the
  package never names itself. A package facade that fails to import is fatal
  to commands, so the package must remain importable without goga present at
  import time.
- **Mutual blindness.** Tools cannot see each other's contributions; the
  coexistence caveat in the User Experience section is a platform property and
  cannot be engineered around by the tool.
- **Compatibility.** The product targets goga 2.0.x (the first line with the
  configuration amendment domain); the tool requires a goga environment that
  provides that domain.
- **Distribution identity.** The product is the pip package
  `goga-tool-basic-build`, installable into a goga project environment via
  `goga install basic-build` or a `tools:` declaration, and shipped for
  external consumption by any goga project.
- **Fixed value domain.** Review strategy values are fixed by the platform
  consumer (`full` | `medium` | `short`, default `medium`); the presets must
  stay within that domain.

## Scope

### In Scope

- The `goga-tool-basic-build` package as a distributable goga tool: its
  configuration-contribution behavior — the two review presets
  (`strategy: medium`, `max_iterations: 5`), the authored-wins rule for the
  iteration cap, the two hard conflicts with their clean errors, the run
  feedback, and the zero-footprint guarantees.
- Distribution as a pip package consumable by any external goga project via
  `goga install basic-build` / `tools:` declaration.
- The maintainer-facing contract documentation shipped with the package: what
  the tool guarantees, how to rely on the effective values, how to author the
  one tuning knob, the deliberate conflicts, and the reversibility and
  coexistence notes (following the pattern established by the sibling tool
  `goga-tool-simple-build`).

### Out of Scope

- Any change to the goga platform itself.
- Any CLI command of the tool (it is hook-shaped: no command, nothing to run).
- Presets, mapping, or validation of anything beyond the two review leaves:
  agent presence, review roles, environment values, base ref, session knobs,
  tasks-pass (`build` root) settings, external-review settings.
- Mapping the review-level iteration cap into `additional.max_iterations`
  (sibling-tool behavior; here the `additional` section is forbidden).
- Detection, warning, or configuration of coexistence with other
  review-preset tools — documented as an adoption condition only.
- Dogfooding: this repository's own `.goga/config.yml` is not switched to the
  new tool. The package ships for external consumption, and the project must
  not use itself.

## Success Criteria

All criteria are observable through `goga config` output, run output (stderr),
command exit behavior, and the authored file's bytes.

1. **Profile guarantee.** In a goga project whose `.goga/config.yml` contains
   no review settings (minimal `language:` alone), with the tool installed,
   `goga config` reports effective `build.review.strategy: medium` and
   `build.review.max_iterations: 5`, and a configuration-consuming run prints
   an amendment summary naming the tool and each applied path.
2. **Determinism and footprint.** Repeated runs in the same environment
   produce the identical effective configuration, and the authored file is
   byte-identical before and after the runs.
3. **Authored cap wins.** With an authored `build.review.max_iterations`, the
   effective cap is the authored value (not 5), the strategy is `medium`, and
   no error or warning appears. An authored `strategy: medium` is likewise
   accepted silently.
4. **Strategy conflict.** With an authored `strategy` other than `medium`,
   every configuration-consuming command stops with a clean error naming the
   tool, the action, and `build.review.strategy`; the authored value does not
   appear in the error; nothing is applied; the file is unchanged; removing
   the authored strategy (or uninstalling the tool) restores working runs.
5. **`additional` conflict.** With any authored `build.review.additional`
   section — including an empty mapping — commands stop with a clean error
   naming `build.review.additional`, with the same no-leak, no-partial-apply,
   no-modification guarantees; with `additional` absent or YAML-null, no error
   appears.
6. **Reversibility.** After uninstalling the tool, the project's effective
   configuration equals its authored configuration exactly.
7. **Scope integrity.** The tool neither blocks nor warns about anything
   beyond the two conflicts: a configuration with no review agent, with
   review roles, or with any other review leaf loads without any error from
   the tool; the tool exposes no command of its own.
8. **External installability.** Installing the package into a fresh goga
   project environment activates the guarantee from the first
   configuration-consuming run.
