# security-audit

Turn the **12 Security Checks** reel into a source review you can run on your own web app. The skill checks access controls, checkout and payments, AI tool permissions, input and uploads, secrets, and database queries. It gives you a 12-check scorecard and prioritizes fixes with file and line references.

## Install

With Node.js installed:

```sh
npx skills add huseinaa/husein-skills --skill security-audit -g
```

If you already cloned this repo, pull the latest changes. From the repo folder, run `powershell -ExecutionPolicy Bypass -File install.ps1 security-audit` on Windows or `./install.sh security-audit` on macOS or Linux.

## Use it

Open your app's repository in Claude Code, Codex, or another agent that supports skills. Ask it to run `security-audit`, or paste this prompt:

> Use the security-audit skill to review this repository against all 12 security checks. Give me the scorecard, link each finding to the relevant source, and recommend what to fix first. Keep the audit read-only.

The audit uses the source, configuration, and test evidence available to the agent. It marks anything it cannot verify, including controls that depend on deployment settings you have not shared.
