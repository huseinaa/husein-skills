---
name: security-audit
description: Review a web app's source and configuration against 12 security checks. Use for a defensive security audit, a security review before launch, or the 12 Security Checks checklist for a web app or AI-powered app.
---

# Security Audit

Review the user's repository or supplied source. Trace how the app enforces each control and report what the code actually supports. Default to a read-only audit. Make targeted fixes only when the user asks for them.

## Scope and evidence

1. Identify the code and revision in scope. Locate the web and API entry points, authentication and authorization policies, database access, checkout and payment callbacks, upload handling, and AI tool registration that exist in that scope.
2. Follow the reachable server code through middleware, policies, services, and storage. Check alternate entry points, including jobs or callbacks, where they perform the same operation. Inspect relevant build or deployment configuration when it determines whether a control runs or a secret reaches the client.
3. Use source, configuration, and existing test results as evidence. Run relevant local defensive tests only when their isolation is clear. Keep the review source-based. Use ordinary validation and authorization assertions, without exploit payloads, vulnerability reproduction, or requests to live services.
4. For possible credentials, use redacted output and report the location and credential type. Avoid printing values from source, build artifacts, logs, or Git history. If the history or deployment configuration is unavailable, say what evidence is missing.

## The 12 checks

| # | Check | Evidence to look for |
|---|---|---|
| 1 | Admin access | Privileged reads and writes verify the caller's role or permission on the server. Verify the guard on each reachable admin handler and any alternate entry point. |
| 2 | Record ownership | Reads and writes enforce object-level access using the authenticated caller's permissions and tenant or ownership scope. Trace the policy or scoped lookup that applies to the requested record. |
| 3 | Private API keys | Private credentials stay in server-only code or secret storage. Inspect client imports, build-time environment exposure, public assets, and responses. Distinguish private credentials from intentionally publishable identifiers. |
| 4 | Server-side pricing | Checkout recomputes payable amounts from trusted product data and server-side discount rules. The values used to create a payment come from the server's calculation. |
| 5 | Order quantities | Purchase handlers enforce allowed whole-number quantities and bounds before inventory, totals, or fulfillment change. Check the server validation shared by cart updates and order creation. |
| 6 | Payment verification | Fulfillment depends on verified provider evidence. Check event authenticity, payment status, the expected order, amount, and currency, and idempotency when the provider retries delivery. |
| 7 | Promo limits | The server enforces the redemption rules the product promises, including relevant dates, eligibility, and per-user or global limits. Verify that concurrent requests and retries cannot double-count or exceed a limit. |
| 8 | AI tool permissions | Treat model output and retrieved content as untrusted. Verify that each tool call uses the caller's permissions, validates its arguments, and enforces approval requirements outside the model. Check the scope of data access and tool credentials. |
| 9 | Safe text rendering | Trace user-controlled text into templates and the browser. Verify context-appropriate escaping, text rendering, or a suitable sanitizer where the app intentionally supports rich HTML. |
| 10 | Upload validation | The server checks permitted file types using the content as well as the declared type, enforces size limits, and controls storage and serving. Inspect filenames, access permissions, and whether uploaded content can execute. |
| 11 | Git secrets | Inspect tracked configuration and available Git history for private credentials using redacted results. If a secret was committed, prioritize revocation or rotation and report cleanup separately. |
| 12 | Database queries | Trace user-controlled values into query calls. Check parameter binding in ORM and raw queries. Where identifiers or sort options are dynamic, verify that server-defined values determine the query structure. |

## Report

- Lead with confirmed findings ordered by impact. For each, give the check number, severity, file and line, reachable code path, affected data or behavior, and a concrete fix. Report deployment-dependent concerns as unverified when the needed evidence is missing.
- Include a scorecard for all 12 checks. Use **Pass** when there is evidence the control covers the relevant paths in scope, **Fail** for an evidenced control gap, **Not applicable** when the feature is absent from the reviewed scope, and **Not verified** when evidence is incomplete.
- State the scope, tests actually run, and any remaining verification needed. If asked to fix issues, follow the app's existing patterns and rerun the relevant local checks.

## References

- [OWASP Secure Code Review](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html)
- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [Stripe Checkout fulfillment](https://docs.stripe.com/checkout/fulfillment)
- [GitHub guidance on committed secrets](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
