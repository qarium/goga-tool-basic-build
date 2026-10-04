# Project rules

## Byte-exact output documentation

Consumer-facing documentation quotes machine-produced output exactly as the system composes it, with no prettified re-rendering, so the documented text can be found verbatim in real logs.

## Uniform lint coverage

All code, including files the primary validation command never touches, must satisfy the project's static-analysis configuration; exception assertions in tests always carry narrow match anchors rather than bare type checks.

## Out-of-tree environment placement

Development and validation environments live outside the repository tree, with a pre-approved fallback location used when the preferred path is unwritable; failure of the primary path never leads to improvisation or to placing artifacts inside the source tree.

## Fixture-versus-helper import discipline

Test frameworks auto-inject fixtures only; plain helper functions and factories must be imported explicitly in each module that uses them, and imports are restricted to what the module actually references.

## Internal consistency of design artifacts

Pseudocode must be correct under a literal reading of the language, and prose claims must never contradict the code skeletons presented alongside them.

## Design-test executability

Every test specified in a design must be writable exactly as specified: shared test factories expose the parameters the specified tests require, and gaps are closed by extending the factory rather than leaving construction details to the implementer's improvisation.

## Claim-to-test pinning

Every behavioral claim made in a design is pinned by a named test, including defensive paths unreachable on the real platform, which are exercised through test doubles so that later simplification refactors cannot silently break the documented behavior.
