# Architecture

The tool is a single cell — a directory with a `CODEMANIFEST` contract and
consumer-facing practices in `.usages/`. Contracts are read-only: when
implementation and contract disagree, the implementation is what gets fixed.

## Cell map

| Cell | Role |
|---|---|
| [`goga_tool_basic_build`](api/facade.md) | Package facade — the platform subscription (one hook) and the single API surface |

## Import graph

```
goga_tool_basic_build            (package facade, the hook + subscription)
```

The cell has no imports: it declares no `Imports` and depends on no other
cell. The platform types (`HookRegistrar`, `ConfigAmendment`) are referenced
under `TYPE_CHECKING` only — the facade stays import-clean with or without
goga installed.

## Amendment data flow

The amendment action fires at the configuration load moment of every
config-consuming goga surface — the host-side commands (`build`, `pipeline`,
`lint`, `contract`, `install`, `config`, `topics`, `usages status`,
`usages sync`) and the in-container entrypoints alike:

1. goga calls `register_hooks(hooks)` when a command first reaches a hook
   checkpoint.
2. The registration subscribes exactly one hook: address `config` /
   `amend_config`, name `review_presets`.
3. The platform delivers a `ConfigAmendment` context to the hook.
4. The hook reads the guard leaf `build.review.strategy` from the context's
   configuration — absent intermediate branches read as absent, and a blank
   value reads as unset.
5. An authored strategy other than `medium` raises: the platform stops the
   hosting command with a clean error naming the tool, the action, and the
   path — never the authored value — and the tool's whole contribution is
   discarded.
6. The hook reads the `build.review.additional` section — absent branches read
   as absent. When the section is present with any contents, including an
   empty mapping, the hook raises the same way: the error names the path,
   never the values.
7. Otherwise the hook buffers two set amendments through `context.set`:
   `build.review.strategy` = `medium`, `build.review.max_iterations` = `5` —
   unconditionally, whether or not authored values already exist at those
   leaves.
8. The platform merge keeps authored values per path — the presets fill only
   what the author left silent — and prints the amendment summary to stderr.
   The amended configuration exists only in-memory, for the duration of the
   run.

When both conflicts are present, the strategy one is reported — steps 4–5 run
before step 6, so the outcome is deterministic.

## Runtime properties

- The package runs inside a goga-provided interpreter: runtime dependencies
  stay empty — goga is provided by the ecosystem and is declared only in the
  test extra, unpinned above the supported line.
- The facade module stays import-clean — a broken import is fatal to every
  goga command.
- The hook is a pure function of the delivered context: no state, no cache, no
  clock or environment reads; identical facts produce the identical
  contribution.
- The read footprint is the strategy guard leaf plus the `additional` section;
  the write footprint is exactly the two leaf paths (`build.review.strategy`,
  `build.review.max_iterations`) — no other configuration path, no tasks-pass
  settings, no environment values.
- No agent validation of any kind: the missing-agent error belongs to the goga
  platform's agent value guard and inheritance.
- Failures propagate as clean command errors through the hard action — no
  internal exception handling; nothing partial applies.
- Authored-wins is owned by the platform merge layer and is never re-derived
  inside the hook; the hook never uses a force amendment — the presets never
  overwrite authored values.
