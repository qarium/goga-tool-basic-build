# Review presets — what an installed tool guarantees

For project maintainers who install `goga-tool-basic-build` into a goga project
and want to know what the review pass of `goga build` will look like. The tool
is hook-only: there is no command to run and no file to edit for its part —
the presets apply from the first config-consuming goga run after installation.

## What you get

With the tool installed, every goga run that loads `.goga/config.yml` receives
two review presets:

| Path | Value |
|---|---|
| `build.review.strategy` | `medium` |
| `build.review.max_iterations` | `5` |

Absent intermediate branches (`build`, `build.review`) materialize on their
own — a minimal configuration of `language` alone is enough.

## Relying on the effective values

A minimal authored configuration:

```yaml
language: python
```

Effective review configuration in every run:

```yaml
build:
  review:
    strategy: medium
    max_iterations: 5
```

## Seeing what was applied

Every run that applies presets prints the platform's amendment summary to
stderr — the tool name and one line per applied amendment (path, `set`):

```text
config amendments: 2 applied
- basic-build set build.review.strategy
- basic-build set build.review.max_iterations
```

Check the effective values after a run with `goga config` — it prints the
amended values. When nothing is applied (every leaf already authored), nothing
is printed. Configuration values never appear in any informational output.

## Authoring your own values

The iteration cap is the one tuning knob: an authored
`build.review.max_iterations` always wins over the preset — silently, no
warning, no error — while the strategy preset still applies:

```yaml
build:
  review:
    max_iterations: 8   # authored — wins over the preset 5
```

Effective: `strategy: medium`, `max_iterations: 8`. An authored
`build.review.strategy: medium` is likewise accepted silently; any other
authored strategy is a conflict (below). There is no `additional` knob to
tune — a basic build does not configure the external review, and authoring
that section stops the command.

## The deliberate conflicts

Authoring `build.review.strategy` with a value other than `medium` conflicts
with the tool's purpose. Every config-consuming goga command stops with a
clean error naming the tool, the action, and the path — the authored value is
never printed, nothing is applied:

```text
hook review_presets of tool basic-build failed on config.amend_config:
refused the authored configuration at build.review.strategy - remove the
authored strategy or uninstall the tool
```

```yaml
build:
  review:
    strategy: short   # conflict — every goga command stops
```

A blank authored strategy (empty or whitespace-only) reads as unset — no
conflict, the preset still applies. Remove the authored strategy or uninstall
the tool to resolve the conflict.

An authored `build.review.additional` section conflicts as well — any
contents, including an empty mapping:

```yaml
build:
  review:
    additional: {}     # conflict — every goga command stops
```

The command stops the same way; the error names the path
`build.review.additional` and never the values. Remove the section or
uninstall the tool.

When both conflicts are present in one configuration, the strategy one is
reported — the checks run in a fixed order, so the outcome is deterministic.

## Side effects and reversibility

- The authored `.goga/config.yml` is never modified — it stays byte-identical;
  the presets live only in the effective in-memory configuration of each run.
- Repeated runs reproduce the same effective configuration.
- Removing the tool from the environment — and removing its `tools:`
  declaration — returns the project to exactly its authored behavior; no
  residue remains.
- The tool never validates agent presence and never touches agent values — a
  configuration with no review agent loads without any error from the tool.
- Command-line flags of goga commands are runtime overrides of the effective
  configuration — they neither trigger nor bypass the conflicts.

## Coexistence

goga tools are mutually blind. Installing another review-preset tool alongside
this one makes the effective values enumeration-dependent; the guarantee holds
when this is the sole review-preset tool in the environment.

The contract behind these guarantees is documented in the
[API reference](api/facade.md).
