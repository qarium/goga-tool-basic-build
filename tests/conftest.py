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
        self.sets = []  # list of (path, value)
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
        StubSection(strategy=strategy, additional=additional, max_iterations=max_iterations) if review_present else None
    )
    build = StubSection(review=review) if build_present else None

    return StubAmendment(StubSection(build=build))
