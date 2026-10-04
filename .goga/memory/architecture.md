# Project rules

## Cross-artifact naming consistency

An identifier fixed during task definition binds every artifact of the component equally: the contract declaration, the registration call, the tests, and the usage documentation all carry the same name, and an already-proposed name that fits the project's naming conventions is kept rather than replaced with a new invention.

## Package-equals-cell granularity

A self-contained tool package whose routines are always consumed together for one responsibility forms exactly one cell, with all routines living in a single implementation module re-exported through the package facade; splitting co-used routines into separate cells is too fine a granularity, and merging unrelated tools into one cell is too coarse.

## Configuration value secrecy

Every diagnostic or summary text names only the configuration location and the required resolution, never the authored value itself; tests pin this contract by asserting that the location appears in the message text and that the value does not.

## Runtime independence from the host platform

A tool package must import cleanly in an environment where the platform is absent: platform types are referenced only under static type-checking, the runtime dependency list stays empty, and the platform is required solely by the test environment.

## Declarative amendment semantics

A configuration hook buffers its fixed amendments unconditionally, whether or not authored values already exist or intermediate branches are absent, with a missing, null, or blank authored value counting as unset; precedence between authored and contributed values is owned entirely by the platform's merge layer and never re-implemented inside the hook; conflicts are checked in a fixed order for deterministic outcomes; failure occurs only through the designated error type on the defined conflicts; and nothing outside the declared leaves is ever contributed.

## Platform-owned feedback

A component with no command of its own has no output surface: it only reads, guards, buffers amendments, and raises the designated error, while all run feedback, summaries, and error reporting belong to the platform; no printing or logging happens inside the tool package.
