# CAR: Cyber Assurance Record

## Purpose

This is a living security record for resilience decisions that affect the product's exposure, detection, and recovery posture.

For this project, `CAR` means **Cyber Assurance Record**. It is used to track practical engineering controls and their evidence over time.

This file is **CRA-aligned**, meaning it is written to support the ideas in the EU **Cyber Resilience Act (CRA)**, formally Regulation (EU) 2024/2847. It is not a legal determination of compliance.

## Regulatory Framing

The CRA entered into force on **10 December 2024**.

Key dates called out by the European Commission:

- **11 June 2026**: conformity-assessment body notification provisions start applying.
- **11 September 2026**: CRA reporting obligations start applying.
- **11 December 2027**: the CRA becomes fully applicable.

Relevant CRA themes for this issue:

- products should be **secure by default**
- manufacturers should reduce **known and reasonably foreseeable cybersecurity risk**
- vulnerabilities should be handled through a **defined lifecycle process**
- users and operators should receive **clear information and evidence**

## Scope of This Record

Current issue:

- The SPA catch-all route returns `200 OK` and the homepage HTML for requests such as `/.env`, `/.git/config`, and `/sitemap.xml`.
- This creates false-positive vulnerability findings, weakens crawler behavior, and reduces observability quality.

Verified local reproduction is documented in [issue_prod.md](../issue_prod.md).

## Position

The correct response is not one fix. It is a **three-layer control set**:

1. **Application-layer routing guardrails**
2. **Proxy and edge enforcement**
3. **Continuous verification and vulnerability handling**

These should be implemented together as a defense-in-depth stack.

## Solution 1: Application-Layer Routing Guardrails

### Objective

Ensure Flask does not treat sensitive probes or missing machine-readable assets as valid SPA routes.

### Control

Tighten the catch-all route in `src/routes/main_routes.py` so it only serves the SPA shell for legitimate frontend routes and explicitly rejects probe-like or asset-like paths.

### Recommended behavior

- Return `404` for dotfile paths such as `/.env`, `/.git/config`, and `/public/.env`
- Return `404` for missing system discovery assets such as `/sitemap.xml`, `/sitemap.xml.gz`, and similar metadata paths when not explicitly served
- Keep valid frontend routes such as `/admin/profile` and `/blog/my-test-article` on the SPA shell
- Preserve JSON `404` behavior for `/api/*`

### Why this matters

This is the **last line of routing truth**. Even if upstream controls fail or are bypassed, the application should still fail closed for clearly invalid paths.

### CRA alignment

- supports **secure-by-default** behavior
- reduces the impact of **reasonably foreseeable misuse**
- prevents the application from presenting a misleading success response

### Evidence

- Regression test: `test_sensitive_or_missing_metadata_paths_return_404`
- Existing SPA route tests must remain green
- Manual confirmation:

```bash
curl -I http://localhost:5010/.env
curl -I http://localhost:5010/.git/config
curl -I http://localhost:5010/sitemap.xml
```

### Acceptance criteria

- sensitive probe paths return `404`
- valid SPA routes still return `200`
- unknown API routes still return JSON `404`

## Solution 2: Proxy and Edge Enforcement

### Objective

Block obviously invalid or sensitive requests **before** they reach Flask whenever possible.

### Control

Add explicit nginx and Cloudflare controls for high-noise, high-confidence malicious or invalid request classes.

### Recommended behavior

At nginx:

- return `404` for dotfile and hidden-path probes
- add explicit handling for `robots.txt`, `sitemap.xml`, and similar files so they are either served correctly or rejected cleanly
- preserve `CF-Connecting-IP`, `X-Forwarded-For`, and related headers for logging and rate-limiting integrity

At Cloudflare:

- add WAF rules for `/.git`, `/.env`, and similar high-confidence probes
- optionally challenge or rate-limit repeated enumeration patterns

### Why this matters

This reduces load on the Flask app, narrows exposure, and stops noisy traffic as early as possible. It also improves signal quality in logs and makes incident triage easier.

### CRA alignment

- strengthens **defense in depth**
- supports **risk reduction at design and deployment time**
- improves operational resilience by reducing avoidable attack-path reachability

### Evidence

- nginx config review in `docker/nginx/nginx.conf`
- edge rule inventory in deployment notes
- logs show real client IP rather than only internal Docker addresses

### Acceptance criteria

- probe paths can be blocked at nginx even if Flask routing regresses later
- logs retain real client context
- legitimate frontend and API traffic is unaffected

## Solution 3: Continuous Verification and Vulnerability Handling

### Objective

Treat this as a repeatable resilience control, not a one-off patch.

### Control

Institutionalize the behavior with tests, runbooks, and evidence so regressions are caught early and handled consistently.

### Recommended behavior

- keep the new regression test in `tests/integration/api/test_routes.py`
- add a small smoke probe set for sensitive and metadata paths
- keep issue evidence in version control
- document owner, review date, and rollout status in this file
- ensure production logs capture the true external client IP when Cloudflare headers are present
- define a response path for future routing/security regressions:
  - reproduce locally
  - add failing regression test
  - patch
  - verify baseline suite
  - record evidence here

### Why this matters

The CRA is not only about shipping secure code. It is also about maintaining a **vulnerability handling process** and keeping evidence that the process exists and works.

### CRA alignment

- supports **vulnerability handling over the product lifecycle**
- supports **documentation and operator information**
- improves readiness for **incident reporting and corrective action**

### Evidence

- current baseline command:

```bash
docker compose --env-file .env --env-file .env.vars exec -T web /app/.venv/bin/pytest tests/ -m "not e2e"
```

- baseline without the new regression test:

```bash
docker compose --env-file .env --env-file .env.vars exec -T web /app/.venv/bin/pytest tests/ -m "not e2e" -k "not sensitive_or_missing_metadata_paths_return_404"
```

### Acceptance criteria

- regression is permanently covered by tests
- security-sensitive route behavior is part of normal verification
- future incidents can point to a documented corrective-action record

## Solution 5: CI/CD Observability and Host Audit

### Objective

Increase visibility into deployment health and host-level environment drift (e.g., Raspberry Pi state).

### Control

Standardized health verification using the `health-check` composite action and pre-deployment host state snapshots.

### Why this matters

A "brittle" deployment where failures are opaque increases recovery time and hides underlying infrastructure issues (e.g., full SD cards or network isolation).

### CRA Alignment

- improves **incident detection** via structured timing (Time-to-Healthy)
- supports **operator information** with clear "State Snapshots" of the production host
- ensures **traceability of deployment failures**

### Evidence

- `health-check` action: `.github/actions/health-check/action.yml`
- "Pre-deployment Pi State" diagnostic step in `production-deploy.yml`
- TTH (Time-to-Healthy) metrics in Job Summaries

## Recommended Rollout Order

1. Ship **Solution 1** first to remove the immediate incorrect `200` behavior.
2. Ship **Solution 2** next so nginx and Cloudflare reject high-confidence probe traffic earlier.
3. Apply **Solution 5** to stabilize the pipeline diagnostics and provide the evidence needed for long-term CRA compliance.
4. Keep **Solution 3** in place permanently so the control survives refactors and deployment drift.

## Living Record

| Date | Item | Status | Evidence |
| :--- | :--- | :--- | :--- |
| 2026-05-22 | Local bug reproduction for SPA catch-all on `/.env`, `/.git/config`, `/sitemap.xml` | Confirmed | [issue_prod.md](../issue_prod.md) |
| 2026-05-22 | Regression test `test_sensitive_or_missing_metadata_paths_return_404` added | Confirmed | `tests/integration/api/test_routes.py` |
| 2026-05-22 | Non-E2E baseline excluding the new regression test | Passing | `160 passed, 6 skipped, 30 deselected` |
| 2026-05-26 | Integrated `health-check` action for standardized observability | Completed | `.github/actions/health-check/` |
| 2026-05-30 | Implemented Pre-deployment Pi State Snapshot for host audit | Completed | `production-deploy.yml` |

## Review Cadence

- Review this file whenever a security-routing issue is opened or closed.
- Add a new row to the Living Record for each corrective action, test addition, or production verification.
- Re-check CRA references when legal or deployment obligations change.

## References

- EUR-Lex legal text: <https://eur-lex.europa.eu/eli/reg/2024/2847/oj/eng>
- European Commission CRA summary: <https://digital-strategy.ec.europa.eu/en/policies/cra-summary>
- European Commission CRA reporting obligations: <https://digital-strategy.ec.europa.eu/en/policies/cra-reporting>
- European Commission implementation timeline: <https://digital-strategy.ec.europa.eu/en/factpages/cyber-resilience-act-implementation>
