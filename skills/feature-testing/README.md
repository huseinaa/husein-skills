# feature-testing

*Part of [husein-skills](https://github.com/huseinaa/husein-skills), all my Claude Code skills in one repo.*

A Claude Code skill that checks a finished feature for you, so you don't have to read every line the AI
wrote. When a feature is done, it has to pass four gates. If one fails, the skill fixes it and runs
everything again.

---

## What it does

1. **Writes the missing unit tests.** It lists what the feature should do (the normal case, the edge
   cases, the failure cases) and makes sure every item has a test.
2. **Runs your test suite.** Everything has to pass before it goes on.
3. **Measures coverage of the lines you changed.** It looks only at the new code, not the whole project.
   The target is 80%.
4. **Plants bugs on purpose (mutation testing).** It makes one small change at a time to your new code,
   like `<` to `<=`, `and` to `or` or a skipped line, and checks that your tests notice. A bug the
   tests miss gets a new test. The target is 70% caught.
5. **Checks code quality.** Complexity, function length and nesting depth for every function you touched.
   Anything over the limit gets refactored.
6. **Runs your repo's own checks**: the linter, TypeScript, Django checks, plus a scan for hard-coded
   secrets.
7. **Fixes and re-runs**, up to 3 rounds, then reports a scorecard.

It never deletes, skips or weakens a test to make a run pass, and never moves the targets.

The first time you run it in a repo, it adds a short block to `CLAUDE.md` / `AGENTS.md`. From then on,
every agent runs it on its own after each new feature.

```
Feature testing: discount codes at checkout
| Gate                  | Result        | Target |
| Unit tests            | 48 passed     | all    |
| Changed-line coverage | 91%           | 80%    |
| Mutation score        | 34/40 = 85%   | 70%    |
| Quality               | 0 over limits | 0      |
| Repo checks           | lint ok, tsc ok, no secrets |
```

---

## What you need

- **Claude Code** (or another agent that reads skills, like Codex).
- **Python 3.10 or newer.** The scripts use only the standard library. `coverage` is installed for you
  when a Python project needs it.
- A project with tests, or one where tests can be added: Python (pytest, Django) and JavaScript /
  TypeScript (vitest, jest).

Works on Windows, Mac and Linux. Mutation testing is built in, so nothing like mutmut needs installing
(and mutmut doesn't run on Windows anyway).

---

## Install

One line (needs [Node.js](https://nodejs.org)):

```
npx skills add huseinaa/husein-skills --skill feature-testing -g
```

Or with git, so a `git pull` updates it later:

```
git clone https://github.com/huseinaa/husein-skills.git
cd husein-skills
powershell -ExecutionPolicy Bypass -File install.ps1 feature-testing   # Windows
./install.sh feature-testing       # Mac / Linux
```

Or copy the `skills/feature-testing` folder into `~/.claude/skills/`.

---

## Use it

In Claude Code, after a feature is done:

```
/feature-testing                 test the current changes (uncommitted + this branch vs main)
/feature-testing --base HEAD~3   test what changed since a given commit
/feature-testing report          run every gate, change nothing, just the scorecard
/feature-testing install         only add the rule block to this repo
/feature-testing uninstall       take the rule block out
```

Once the rule block is in, you don't need to type anything. The agent runs it after each new feature.
Small stuff like docs, copy, styling, config, renames and one-line fixes is skipped.

---

## Good to know

- The limits live in [`config.json`](config.json): coverage 80%, mutation score 70%, up to 40 mutants,
  complexity 10, function length 50 lines, nesting 4. Change them there if your project needs different ones.
- It doesn't check how the UI looks, real third-party calls, or performance under load. The report says so.
- Save your editor before it runs. Every mutant is put back right after its test run, but unsaved changes to
  the same files can get mixed in.
- **Passing these gates gives strong confidence, not a 100% guarantee.**

---

Built by Husein Aboul Hasan, [unemployedhusein.com](https://unemployedhusein.com). MIT licensed.
