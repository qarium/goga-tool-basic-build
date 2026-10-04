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
