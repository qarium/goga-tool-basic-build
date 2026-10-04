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
