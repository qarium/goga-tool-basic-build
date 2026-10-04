# Package facade

The `goga_tool_basic_build` cell — the platform subscription and the single API
surface of the tool. The facade must stay import-clean: a broken import is
fatal to every goga command.

## Platform subscription

```python
from goga_tool_basic_build import register_hooks

register_hooks(hooks)  # goga calls this when a command first reaches a hook checkpoint
```

The registration subscribes exactly one hook: address `config` /
`amend_config`, name `review_presets`. No CLI entry, no install lifecycle, no
runtime import of goga — the platform types are referenced under
`TYPE_CHECKING` only.

### `register_hooks(hooks: HookRegistrar)`

Subscribe the tool's single review-presets hook to the configuration amendment
action.

- `hooks`: the goga subscription surface delivered at registration — exposes
  `subscribe(domain, action, name, hook)`
- Subscribes the hook routine `review_presets` under domain `config`, action
  `amend_config`, hook name `review_presets` — exactly one subscription,
  unconditional
- Hook name stays unique per tool per address; no configuration or file reads
  during registration; subscribes to no other domain action

### `review_presets(context: ConfigAmendment)`

The amendment hook — guard the two basic-profile conflicts in a fixed order,
then buffer the two review presets.

- `context`: the per-tool read-and-amend view over the authored configuration

Algorithm:

1. Read the authored leaf `build.review.strategy` from the configuration of
   `context`; absent branches read as absent, and a blank (empty or
   whitespace-only) value counts as unset
2. If the authored value is present and is not `medium` — raise `ValueError`
   naming the path `build.review.strategy` and the resolution (remove the
   authored strategy or uninstall the tool), never the authored value
3. Read the authored section `build.review.additional`; absent branches read
   as absent, and a YAML-null section is not a conflict
4. If the section is present with any contents — including an empty mapping —
   raise `ValueError` naming the path `build.review.additional` and the
   resolution (remove the additional section or uninstall the tool), never
   the values
5. Buffer two set amendments through `context`: `build.review.strategy` set
   to `medium`, `build.review.max_iterations` set to `5` — unconditionally,
   including when the authored configuration already carries values at those
   leaves and when intermediate branches (`build`, `build.review`) are absent

The amendments are unconditional — the deliberate reads of the configuration
are the guard leaf of step 1 and the `additional` section of step 3.
Authored-wins is owned by the merge layer and is never re-derived here: the
hook never uses a force amendment, so the presets never overwrite authored
values. The exact write footprint is the two leaf paths of step 5 and nothing
else: no other configuration paths, no tasks-pass settings, no environment
values. The hook never validates agent presence. The strategy conflict is
checked before the `additional` conflict; when both are present the strategy
one is reported. Configuration values are never printed or embedded in any
output or error message.

## The presets

| Path | Value |
|---|---|
| `build.review.strategy` | `medium` |
| `build.review.max_iterations` | `5` |

Both values are fixed constants: there is no tool-own configuration to tune
the presets with. The one effective knob belongs to the author — an authored
`build.review.max_iterations` wins over the preset silently, and an authored
`build.review.additional` section is refused. What an installed tool
guarantees in practice is documented in
[Review presets](../review-presets.md).

## Preconditions and side effects

- The hook is a pure function of the delivered context: no state, no cache, no
  clock or environment reads; identical facts produce the identical
  contribution.
- No project file is ever created or modified; the presets exist only in the
  effective in-memory configuration of each run — the authored
  `.goga/config.yml` stays byte-identical.
- Failures surface as clean command errors through the hard action; the tool's
  whole contribution is discarded — nothing partial applies. The deliberate
  failures are the strategy conflict and the `additional` conflict; a broken
  package import is the single remaining fatal case.
