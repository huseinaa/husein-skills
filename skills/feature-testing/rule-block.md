## Feature testing (installed by /feature-testing)

Code review here starts before the code is written, and a finished feature reviews itself.

**Before coding a new feature:**
- List what it must do in plain words: the normal case, the edge cases, the failure cases.
- Write the tests with the code, not after it. Test what the code does, not how it does it. Mock only external services (APIs, payments, email).
- Keep functions small and follow the patterns already in this repo. No new dependency without saying so.

**When a new feature is finished, run `/feature-testing` before calling it done.** It runs the unit tests, measures coverage of the changed lines, plants bugs on purpose (mutation testing) to check the tests catch them, and checks complexity, function size and nesting. It fixes what fails and re-runs.

- **Counts as a feature:** a new endpoint, page, command, function or behaviour change, or a bug fix that changes logic.
- **Does not count:** planning or discussing a feature, docs, copy, styling, config, renames, one-line fixes.
- Never delete, skip or loosen a test to make it pass.
