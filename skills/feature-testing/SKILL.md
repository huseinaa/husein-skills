---
name: feature-testing
description: Review a finished feature without reading it line by line. Writes the missing unit tests, runs the suite, measures coverage of the changed lines, plants bugs on purpose in the changed code (mutation testing) to prove the tests catch them, and checks complexity, function length and nesting, then fixes what fails and re-runs (up to 3 rounds). On first use in a repo it adds a block to CLAUDE.md / AGENTS.md so every agent runs it after each new feature. Use when a new feature, endpoint, page, command or logic change is finished, when the repo's CLAUDE.md or AGENTS.md says to run it, or when the user asks to test, verify or review a feature, check test quality, run mutation testing, or types /feature-testing. Not for planning, docs, copy, styling, config, renames or one-line fixes.
---

# /feature-testing

The code reviews itself. You set the rules before coding (the block in CLAUDE.md / AGENTS.md), and when the feature is done it has to pass four gates: unit tests, changed-line coverage, mutation testing, quality metrics. Passing gives strong confidence without reading every line. It is not a 100% guarantee, and the report always says so.

```
/feature-testing                 test the current changes (uncommitted + this branch vs main)
/feature-testing --base HEAD~3   test what changed since a given commit
/feature-testing report          run every gate, change nothing, just the scorecard
/feature-testing install         only add the rule block to this repo
/feature-testing uninstall       take the rule block out
```

Scripts live in the `scripts/` folder next to this SKILL.md (the skill's base directory, wherever it was installed), called below as `$S`. Limits live in `config.json`. Never edit `config.json` to make a run pass.

## Step 0. Install the rule (first run in a repo)

```
python "$S/install_rule.py" --check
```

If it says `not installed`, run `python "$S/install_rule.py"` and tell the user in one line which file got the block (`CLAUDE.md`, `AGENTS.md` or both). It writes to whichever of the two exist, creates `CLAUDE.md` only when neither does, and refuses on a repo with no code. Re-running updates the block in place, never duplicates it.

## Step 1. Scope

```
python "$S/scope.py" [--base REF]
```

It prints JSON: each project touched (`dir`, `stack`, `runner`, `test_cmd`, the Python interpreter, changed `code` and `tests` files with line ranges), the non-code files, and `small`.

- If nothing is code (`projects` empty) or `small` is true and the change is not a logic change, say so in one line and stop. That is the "not small stuff" rule.
- If `test_cmd` is empty, the project has no test runner. Python: use pytest (`python -m pip install pytest` if missing, say so). JS/TS: add vitest as a dev dependency only after telling the user, since it changes `package.json`.
- Read the changed code files now. You need to know what the feature does to test it.

## Step 2. Behaviour contract, then the tests

Write the feature's behaviours as a short plain list, taken from the user's request or the plan: the normal case, the edge cases (empty, zero, boundary values, duplicates, very long input), and the failure cases (bad input, missing permission, the external service failing).

Every behaviour needs at least one test. Add the missing ones next to the repo's existing tests, in its style.

- Test what the code does, not how it does it. Assert on outputs, returned values, saved records, HTTP status and body.
- Mock only what leaves the process: third-party APIs, payments, email, the clock when it matters. Never mock the code under test.
- Django: use the test client and the test database. Next.js / React: test the logic and handlers; UI look is out of scope.

## Step 3. Unit tests

Run the full suite with `test_cmd` from the project's `dir`. It must be green before going on. A failure is either a bug in the feature (fix the code) or a wrong test (fix the test only if it asserts something the feature was never meant to do, and say which).

## Step 4. Coverage of the changed lines

- Python: `python -m coverage run -m pytest -q` (or `-m coverage run manage.py test`), then `python -m coverage json -o "$TMP/cov.json"`. Install `coverage` with pip if missing, one line to the user. Count only the changed line ranges from Step 1 that are executable.
- JS/TS: if the project has vitest or jest coverage set up, run it and read the changed files' lines. If not, skip coverage and say so: the mutation score in Step 5 is the stronger measure anyway.

Under `coverage_min` (80%) means untested branches: go back to Step 2 for them.

## Step 5. Mutation testing

```
python "$S/mutate.py" --cwd "<project dir>" --cmd "<test command>" <file>:<ranges> [<file>:<ranges> ...] --json "$TMP/mut.json"
```

Pass the changed `code` files with their ranges from Step 1 (for example `app/billing.py:12-40,55-61`). For speed, `--cmd` can run only the test files that exercise those modules; use the full suite if it takes under a minute.

What it does: plants one small bug at a time on the changed lines (`==` to `!=`, `<` to `<=`, `+` to `-`, `and` to `or`, `True` to `False`, drops a `not`, returns `None`/`null`, skips a statement, shifts a boundary number by 1), runs the tests, restores the file. Up to `max_mutants` (40), sampled evenly. It refuses to start if the tests are not green, and any run first restores files a crashed earlier run left mutated (`--recover` does only that).

Every **SURVIVED** line is a bug the tests did not notice. For each one, write a test that fails on the mutated line and passes on the real one. Only change the source when the survivor shows a real bug (for example the boundary really is wrong). A survivor that changes nothing observable (an equivalent mutant, such as `x >= 0` vs `x > 0` where 0 can never happen) is listed as equivalent in the report with the reason, not "fixed" by a pointless test.

Target: `mutation_min` (70%).

## Step 6. Quality metrics

```
python "$S/metrics.py" --cwd "<project dir>" <file>:<ranges> ...
```

For every function touched: cyclomatic complexity (limit 10), length (50 lines), deepest nesting (4). Python is exact; JS/TS uses the project's ESLint when installed, otherwise a marked estimate. Anything OVER gets refactored: extract helpers, return early, replace long `if/elif` chains with a lookup. Re-run the tests after every refactor.

## Step 7. The repo's own checks

Run whatever the repo already has, only for what exists: its linter (ruff, flake8, eslint), `npx tsc --noEmit` for TypeScript, `python manage.py check` for Django. Then scan the diff for hard-coded secrets: API keys, tokens, passwords, private URLs with credentials (`git diff <base> | grep -iE "sk-|api[_-]?key|secret|password|token"` and judge the hits). A secret in the code is a stop-and-tell, not a fix-and-continue.

## Step 8. Fix and re-run

When any gate fails, fix and go round again from Step 3, up to `max_fix_rounds` (3). In `report` mode, skip this step entirely and change nothing.

Hard rules, no exceptions:
- Never delete, skip, `xfail`, `.skip` or comment out a test to make the run pass.
- Never weaken an assertion (`assertEqual` to `assertTrue`, exact values to "is not None").
- Never change `config.json` or the mutation run's arguments to raise the score.
- Never change behaviour the user asked for to make a test pass.

After round 3, stop and report what is still failing. Do not loop further.

## Step 9. Report

Lead with the scorecard, then a few lines:

```
Feature testing: <feature in a few words>
| Gate                  | Result        | Target |
| Unit tests            | 48 passed     | all    |
| Changed-line coverage | 91%           | 80%    |
| Mutation score        | 34/40 = 85%   | 70%    |
| Quality               | 0 over limits | 0      |
| Repo checks           | lint ok, tsc ok, no secrets |
```

Then: tests added (count and what they cover), code fixed (real bugs the gates found, one line each), anything still failing after 3 rounds, equivalent mutants with reasons, and what was not checked (how the UI looks, real third-party calls, performance under load).

End with this line, every time: **Passing these gates gives strong confidence, not a 100% guarantee.**

## Notes

- Files are restored after every mutant, but run mutation testing with no unsaved editor changes on the same files.
- Mutation testing on Windows is built in on purpose: mutmut does not run on native Windows, and nothing here needs installing except `coverage` for Python coverage.
- On a project with several parts (for example a Django backend and a Next.js frontend), Step 1 lists each one. Run Steps 3 to 7 per project.
