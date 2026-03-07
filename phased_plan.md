# Phased Plan (Modernized SPA & Production Readiness)

**Status**: 
- Phase 1-3: [DONE] Core Stability, API Contracts, and Service Layer Refactor.
- Phase 4: [DONE] Modernization (History API, UI Factory, Observer Pattern).
- Phase 5: [ACTIVE] Production Hardening & Cloudflare Integration.

---

## Phase 4 — Modernization & Reactive Patterns (COMPLETED)
**Success criteria**
- Navigation uses the Browser History API (no `#`).
- UI state is reactive (Observers) and consistent (Factories).
- Local Preflight mirrors CI behavior exactly.

**Deliverables**
- `ComponentFactory.js`: Centralized UI card/section generation.
- `AuthService.js`: Observable authentication state.
- `app.js`: History API router with link hijacking and zero-annoyance 401 refresh.
- `preflight_ci.ps1`: Added `-SmokeTest` for CI-parity local verification.

---

## Phase 5 — Production Runner & Smoke Testing
**Goal**: Transition from "CI-only" ephemeral testing to an "Always Up" Production environment with real-world verification.

**Success criteria**
- Production runner is operational and distinct from Staging.
- Push-to-Prod workflow includes a "Post-Deploy Smoke Test".
- Environment-specific config (Certs/TLS) is decoupled.

**Deliverables**
- **Production Runner**: Dedicated `runs-on: prod` runner config.
- **Config Branching**: Decouple Talisman/HTTPS settings so Prod can enforce strict HSTS while local remains flexible.
- **Smoke Suite**: A specialized `pytest -m smoke` suite that runs against the live prod URL after deploy.

**Gates**
- `scripts/preflight_ci.ps1 -SmokeTest` passes locally.
- Production runner successfully heartbeats to GitHub.
- Manual "hard-rebuild" trigger works for Staging recovery.

---

## Phase 6 — Cloudflare Zero Trust & Secure Edge
**Goal**: Secure the production endpoint behind Cloudflare without breaking the Staging/Dev environments.

**Success criteria**
- Production traffic routes through `cloudflared` tunnel.
- Staging remains direct-access (WSL) for development speed.
- Zero Trust (WARP/Access) protects Admin routes.

**Deliverables**
- `docker-compose.prod.yml`: Adds `cloudflared` container and wires it to `nginx`.
- **Tunnel Secret Management**: GitHub Secrets used to store and inject tunnel tokens only during Prod deploy.
- **TLS Termination Strategy**: Configure Nginx to accept unencrypted traffic from the tunnel while maintaining HTTPS for the public edge.

**Gates**
- Prod Smoke tests pass through the tunnel.
- Staging environment remains unaffected by Cloudflare changes.

---

## Core Pain Points & Tech Debt (Prod Blockers)

### 1. **Talisman/TLS Coupling (High Debt)**
*   **Issue**: Current `TALISMAN_FORCE_HTTPS` and cert generation logic is mixed between Staging and CI.
*   **Impact**: Cloudflare handles TLS differently (Termination at edge). Production Nginx needs a "Tunnel Mode" where it trusts the Cloudflare ingress without needing local self-signed certs.
*   **Fix**: Implement `ENV`-based Nginx profiles.

### 2. **Runner Label Pollution**
*   **Issue**: Workflows use hardcoded labels like `wsl-staging`.
*   **Impact**: Hard to spin up a Prod runner without accidentally hijacking staging jobs.
*   **Fix**: Standardize runner selection using variables (`runs-on: ${{ env.RUNNER_LABEL }}`).

### 3. **The "Admin-Only" Content Model**
*   **Issue**: Current service layer (Singletons) and UI assume one Admin is the source of all truth.
*   **Impact**: Blocking "True User Access" (Comments, Member accounts).
*   **Fix**: Refactor `ArticleService` and `ProfileService` to support **Resource Ownership** checks (owner_id).

### 4. **Rate Limit State Persistence**
*   **Issue**: Rate limits use Redis, but if Prod Redis restarts, all limits reset.
*   **Impact**: Vulnerable to brute force during maintenance windows.
*   **Fix**: Persistent Redis volume strategy for Prod.

---

## Junior Guidance & Safety Mandates
- **Production is "Always Up"**: Never use `down -v` in production workflows without an explicit database backup step.
- **Zero Trust is Prod-Only**: Do not attempt to wire WSL Staging to Cloudflare Tunnels yet; it complicates local debugging.
- **Verify before Tunneling**: Ensure the app is healthy on its local IP before enabling the Cloudflare edge.
