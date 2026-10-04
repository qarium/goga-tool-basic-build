# goga-tool-basic-build

A [goga](https://pypi.org/project/goga/) hook tool that gives builds a basic
review pass by default: the medium review strategy plus a five-iteration review
cap, applied wherever the project author left the review knobs unwritten.

## How it works

The package registers exactly one hook — `review_presets` on the
`config / amend_config` action. At the configuration load moment the hook
contributes two set amendments:

- `build.review.strategy` set to `medium` — the basic review form;
- `build.review.max_iterations` set to `5` — the review loop cap.

The amendments are buffered unconditionally; authored-wins is owned by the
platform merge layer: an authored `build.review.max_iterations` silently wins
over the preset `5`, an authored `strategy: medium` is accepted silently, and
nothing is persisted — the authored `.goga/config.yml` stays byte-identical,
and removing the tool returns the project to exactly its authored behavior.

The deliberate reads of the authored configuration are the two conflict
guards. An authored `build.review.strategy` other than `medium` conflicts with
the tool's purpose; an authored `build.review.additional` section — any
contents, including an empty mapping — conflicts as well: a basic build does
not tune the external review. Each stops the hosting command with a clean
error naming the path — never the authored value — and removing the
conflicting authored value or uninstalling the tool resolves it. When both
conflicts are present, the strategy one is reported — the checks run in a
fixed order.

## Installation

The tool has no runtime dependencies by design — the platform types are
referenced under `TYPE_CHECKING` only, so the package facade stays
import-clean with or without goga installed. The tool is installed into the
project's goga docker image — the environment goga commands run in.

### Declare it as a project dependency

Add the tool to the project's `.goga/config.yml`:

```yaml
tools:
  basic-build: latest
```

A plain `goga install` during the image build then resolves it together with
the rest of the project's declared tools:

```dockerfile
FROM <goga-base-image>

USER root

COPY . /tmp/project
RUN cd /tmp/project && goga install && rm -rf /tmp/project

USER goga
```

### Install it by name

Install the tool by name during the image build:

```dockerfile
FROM <goga-base-image>

USER root

COPY . /tmp/project
RUN cd /tmp/project && goga install basic-build && rm -rf /tmp/project

USER goga
```

## Documentation

- [Review presets](review-presets.md) — what an installed tool guarantees: the
  presets table, authored-wins, the one tuning knob, and the deliberate
  conflicts
- [Architecture](architecture.md) — the cell map and the amendment data flow
- [API reference](api/facade.md) — the package facade contract

## Development

The project venv lives outside the repository at `/opt/goga/project`:

```bash
/opt/goga/project/bin/pip install -e '.[test]'
/opt/goga/project/bin/python -m pytest tests/
/opt/goga/project/bin/ruff check goga_tool_basic_build/ tests/
/opt/goga/project/bin/ruff format --exclude '.usages' goga_tool_basic_build/ tests/
```

The `test` extra carries the platform (`goga>=2.0`, unpinned) and the test
stack; the unpinned platform is deliberate — a platform release that changes
the amendment surface must surface as test failures, not silent drift.

`CODEMANIFEST` and `.usages/` files are read-only contracts: when
implementation and contract disagree, the implementation is what gets fixed.
