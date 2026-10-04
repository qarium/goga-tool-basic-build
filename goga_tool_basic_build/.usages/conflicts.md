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
hook review_presets of tool basic-build failed on config.amend_config:
refused the authored configuration at build.review.strategy - remove the
authored strategy or uninstall the tool
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
