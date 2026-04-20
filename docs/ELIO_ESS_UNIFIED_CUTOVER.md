# Elio + ESS Unified Cutover Plan

Status: `in progress`

Owner: `Alex / Elio buildout`

Last updated: `2026-04-20`

## Repository & Hosting

- **Git:** [hclara23/ESS_Executive_OS](https://github.com/hclara23/ESS_Executive_OS)
- **Frontend (Firebase interim):** [elioos.web.app](https://elioos.web.app) — project `elioos`
- **Deploy frontend:** `firebase deploy --only hosting --project elioos`

## Purpose

This document is the working cutover tracker for:

- retiring Firebase from the Elio user-facing path
- keeping `electricsupplysource.co` on HostGator and WordPress/Divi
- moving Elio and ESS into one private local-server runtime
- making ESS an internal Elio capability instead of a separate app
- expanding Elio's internal n8n automation abilities safely

Update this file in git as work is completed. Check items off rather than creating a second tracker.

Short handoff for the next session:

- [SESSION_HANDOFF_20260408_ELIO_ESS_CUTOVER.md](/C:/dev/NEMO-Personal-Virtual-Assistant-main/docs/SESSION_HANDOFF_20260408_ELIO_ESS_CUTOVER.md)

## Session Handoff Snapshot

### Achieved

- Node 2 now hosts the staged Elio API, Elio subagent, Elio Postgres, ESS API, ESS worker, ESS Postgres, ESS Redis, and ESS n8n services privately.
- Elio now serves its own `public/` frontend directly from the API image on Node 2.
- ESS runtime issues that blocked integration were patched and Elio now reads normalized ESS SEO stats successfully.
- Production WordPress connectivity from Node 2 was verified with a draft create/delete cycle.
- Node 2 now consumes Node 1 Ollama over the private LAN at `http://192.168.1.108:11434/v1`.
- Host-level Ubuntu `nginx` on Node 2 now has a working `app.electricsupplysource.co` vhost that proxies to the staged Elio app.

### Still Missing

- Public DNS for `app.electricsupplysource.co` still needs to point at the Node 2 ingress path.
- TLS for `app.electricsupplysource.co` still needs to be issued on Node 2 host `nginx`.
- Authenticated browser walkthrough on the real public app domain is still pending.
- WordPress still needs the final Elio portal page and CTA.
- Firebase rollback handling and final retirement still need to be decided after public validation.
- Old ESS-only and Firebase-era runtime cleanup has not started.

### Start Here Next Session

1. Confirm who controls DNS for `app.electricsupplysource.co` and point it at Node 2.
2. Run Certbot on Node 2 host `nginx` for `app.electricsupplysource.co`.
3. Validate the real public domain in a browser: login, dashboard, chat, SEO view, n8n status, and WordPress publish test.
4. Add the WordPress portal page or CTA on `electricsupplysource.co`.
5. Decide when to promote Node 2 from staging to primary and when to retire Firebase from rollback duty.

## Working Assumptions

- Public website: HostGator
- CMS: WordPress with Divi Builder
- Target public app entrypoint: `app.electricsupplysource.co`
- Node 1 role: GPU worker
- Node 2 role: control plane, API, queue, database, automation
- Firebase should be removed from the primary serving path
- WordPress remains the public website and content system
- n8n remains internal-only

## Known Current State

| Area | Current state |
| --- | --- |
| Website | `electricsupplysource.co` runs on HostGator with WordPress/Divi |
| Elio frontend | Elio frontend is now staged for same-origin local hosting from the API image on Node 2 |
| Elio server target | Local `.env` currently points Elio deployment at Node 1 |
| ESS runtime | ESS deploy scripts target Node 2 |
| ESS dashboard | Separate user-facing dashboard is incomplete and should not be the end-state UI |
| n8n | Present as a separate ESS automation surface today |

## Server Inventory

| Node | Hostname | User | IP | Intended role |
| --- | --- | --- | --- | --- |
| Node 1 | `graveatlas-gpu` | `botd` | `192.168.1.108` | GPU inference worker only |
| Node 2 | `botd2` | `morningstar` | `192.168.1.25` | API, n8n, Postgres, Redis, orchestration, reverse proxy |

## Guardrails

- Do not store plaintext passwords or tokens in repo docs.
- Rotate any credential that has already been pasted into chat or shell history.
- Do not delete ESS volumes, databases, or bind mounts until inventory and backups are complete.
- Do not attempt WordPress SSO during the first cutover. Start with a portal page that redirects to Elio.
- Do not expose `n8n`, model servers, Redis, Postgres, or private workers directly to the public internet.

## Target Architecture

### Public

- `https://electricsupplysource.co` stays on HostGator
- WordPress gets a portal/login page that links to `https://app.electricsupplysource.co`
- Optional future subdomains:
  - `app.electricsupplysource.co` for Elio
  - `api.electricsupplysource.co` only if a separate public API hostname is needed

### Private runtime

- Node 2 runs:
  - reverse proxy
  - Elio API
  - Elio subagent
  - ESS API
  - ESS worker
  - n8n
  - Postgres
  - Redis
- Node 1 runs:
  - Ollama or equivalent local model runtime
  - XTTS or other GPU-heavy auxiliary services if needed
  - optional background AI workers later

### Product boundary

- WordPress = public site
- Elio = only user-facing app dashboard
- ESS = internal Elio capability
- n8n = internal workflow engine behind Elio/admin controls

## Definition Of Done

- [ ] Users can start from `electricsupplysource.co` and reach Elio through a company-owned subdomain
- [ ] Firebase is no longer required for normal Elio usage
- [ ] Node 2 hosts the unified private app stack
- [ ] Node 1 only serves private GPU/model workloads
- [ ] ESS features appear inside Elio instead of as a separate app
- [ ] n8n is reachable internally and exposed in Elio only through approved admin flows
- [ ] WordPress publishing from the unified stack works against the production site
- [ ] Old ESS-only runtime and unused storage are reclaimed safely

## Phase 0 - Safety, Inventory, And Backups

Exit criteria: we know exactly what is running on both nodes and have backups before moving anything.

- [ ] Rotate any shared or exposed credentials before cutover work begins
- [x] Confirm SSH-key access works for both nodes
- [x] Record active Docker containers on Node 1
- [x] Record active Docker containers on Node 2
- [x] Record Docker volumes on Node 1
- [x] Record Docker volumes on Node 2
- [ ] Record bind-mount directories used by Elio on Node 1
- [ ] Record bind-mount directories used by ESS on Node 2
- [x] Record open host ports on both nodes
- [x] Record CPU, RAM, disk, and GPU availability on both nodes
- [x] Backup Elio database
- [ ] Backup ESS database
- [ ] Backup n8n workflows and credentials export
- [x] Backup relevant Docker compose files and `.env` files outside the repo
- [ ] Confirm WordPress JWT/plugin configuration is documented outside the repo

## Phase 1 - Finalize The Cutover Decisions

Exit criteria: the target design is locked before infrastructure is moved.

- [x] Confirm `app.electricsupplysource.co` as the Elio public entrypoint
- [ ] Confirm whether `api.electricsupplysource.co` is needed or not
- [ ] Confirm Node 2 as the unified control-plane host
- [ ] Confirm Node 1 remains GPU-only
- [x] Confirm first-release auth model is portal redirect, not SSO
- [x] Confirm WordPress remains the public marketing/content site
- [x] Confirm Elio will be the only user-facing dashboard
- [x] Confirm ESS stays as an internal service behind Elio
- [ ] Confirm database strategy for first cutover:
  - recommended first step: one Postgres engine on Node 2 with separate databases or schemas
- [x] Confirm reverse proxy choice on Node 2
  - host-level Ubuntu `nginx` is the active reverse proxy on Node 2
- [ ] Confirm backup retention path and rollback owner

## Phase 2 - Prepare Node 2 As The Unified Control Plane

Exit criteria: Node 2 is ready to host the unified stack without yet cutting traffic over.

- [x] Create the final application directory structure on Node 2
- [x] Create or confirm the shared edge network for the reverse proxy
- [ ] Move Elio deployment target from Node 1 to Node 2 in deployment config
- [x] Prepare Node 2 `.env` for unified stack use
- [x] Keep model-serving URLs pointed at Node 1 private services where needed
  - Node 2 staging now points its local-model path at `http://192.168.1.108:11434/v1`
  - Node 2 staging subagent is running locally while consuming Node 1 Ollama over the private LAN
- [ ] Confirm Node 2 firewall/router rules only expose the reverse proxy entrypoint
- [ ] Keep Postgres, Redis, n8n, subagent, and model traffic private
- [ ] Decide whether Elio and ESS will be one compose project or tightly coordinated compose projects
- [ ] Define resource limits for each service on Node 2
- [ ] Define persistent storage paths for Postgres, n8n, reports, and uploaded assets

## Phase 3 - Unify Elio And ESS Runtime

Exit criteria: Elio and ESS are running together on Node 2 in private networking and Elio can call ESS reliably.

- [x] Fix ESS runtime issues before migration:
  - DB driver/DSN correctness
  - async SQL execution patterns
  - response-shape mismatch with Elio SEO dashboard
- [x] Create a shared internal network between Elio API and ESS services
- [x] Point Elio `SEO_API_URL` at the private ESS API service on Node 2
- [x] Point Elio `N8N_URL` at the private n8n service on Node 2
- [x] Remove any stale assumptions that ESS is a separate user-facing site
- [x] Add health checks for ESS API, ESS worker, and n8n in the unified deployment
- [x] Confirm Elio can reach ESS health endpoint from inside the stack
- [x] Confirm Elio can read ESS report/stats endpoints with the expected response contract
- [x] Confirm WordPress publish/test calls still work from Node 2

## Phase 4 - Replace Firebase As The User-Facing Elio Path

Exit criteria: Firebase is no longer needed to serve the main Elio experience.

- [x] Decide whether Elio frontend is served directly by Elio API or by a local reverse proxy/static host on Node 2
  - decision: serve the existing `public/` app shell directly from the Elio API image on Node 2
- [x] Remove Firebase-only origin assumptions from the frontend/backend config
- [x] Update allowed origins to the final company-owned app domain
- [ ] Verify login, dashboard, chat, and core views at the new local-hosted path
  - current staging verification complete: `/`, `app.js`, `style.css`, `sw.js`, `/guide`, `/vendor-upload`, `/login`, `/system/runtime`, `/api/seo/stats`, and `/chat`
  - current browser verification: the rendered login shell loads correctly over the private Node 2 staging tunnel
  - remaining before checkoff: authenticated browser-level dashboard walkthrough on the actual app domain after reverse proxy/DNS is in place
- [ ] Keep Firebase live only as a temporary rollback path if needed
- [ ] Cut users over to the new app domain
- [ ] Remove Firebase from normal operations once the new path is stable

## Phase 5 - Website Portal Integration

Exit criteria: users can start at the WordPress site and reach Elio cleanly.

- [ ] Create a WordPress page or menu item for the Elio portal
- [ ] Add a clear CTA from the main website to `app.electricsupplysource.co`
- [ ] Decide whether the page is public, member-only, or role-limited in WordPress
- [ ] Add brand-consistent copy explaining that Elio is the private operations portal
- [ ] Verify the portal page works on desktop and mobile
- [ ] Verify the Elio app domain uses valid TLS and loads without mixed-content issues

## Phase 6 - Integrate ESS Into Elio UI

Exit criteria: ESS is no longer treated as a separate product UI.

- [ ] Replace the current placeholder SEO dashboard data wiring with real ESS-backed data
- [ ] Add ESS summaries to Elio views where they fit:
  - SEO health
  - opportunity queue
  - content pipeline
  - WordPress publish status
  - bilingual translation status
  - recent automation runs
- [ ] Remove any user-facing dependency on the unfinished standalone ESS dashboard
- [ ] Confirm role-based access for ESS admin actions inside Elio
- [ ] Confirm Alex/admin flows can review and trigger ESS actions safely

## Phase 7 - Expand n8n Inside Elio

Exit criteria: n8n is usable as Elio's internal workflow engine without exposing raw risk.

- [ ] Keep n8n private to the internal stack
- [ ] Define which users can access live automation controls
- [ ] Decide whether Elio shows:
  - status only
  - approved workflow launcher
  - full editor link for admins
- [ ] Add approved workflow categories for Elio:
  - SEO and publishing
  - reporting
  - notifications
  - CRM or lead routing later
  - maintenance jobs
- [ ] Log workflow launches and outcomes through Elio where possible
- [ ] Confirm admin-only controls for editor/open access

## Phase 8 - Production Validation And Cutover

Exit criteria: the new path is live and the old split topology is no longer primary.

- [ ] Validate unified stack startup from a cold boot
- [ ] Validate Elio login and JWT refresh
- [ ] Validate core dashboard views
- [ ] Validate ESS health and SEO widgets inside Elio
- [ ] Validate WordPress publish test
- [ ] Validate n8n admin access path
- [x] Validate Node 1 model connectivity from Node 2
- [ ] Validate backups after the new deployment
- [ ] Point DNS/public routing to the final Node 2 reverse proxy entrypoint
- [ ] Announce cutover complete

## Phase 9 - Reclaim Old Space And Remove Waste

Exit criteria: no abandoned ESS-only or Firebase-era runtime remains in production.

- [ ] Confirm no active production traffic depends on Firebase
- [ ] Confirm no active production traffic depends on old ESS-only entrypoints
- [ ] Inventory old ESS containers and volumes on Node 2
- [ ] Remove only unused ESS containers after verification
- [ ] Remove only unused ESS images after verification
- [ ] Archive or delete unused ESS bind-mount directories after backup
- [ ] Remove stale DNS entries and unused proxy configs
- [ ] Update documentation to reflect the new steady-state topology

## Deferred Work

Do not block the first cutover on these items.

- [ ] WordPress-to-Elio single sign-on
- [ ] Deep Divi layout automation
- [ ] Full database/schema merge between Elio and ESS
- [ ] External customer-facing automation portals
- [ ] Public exposure of n8n

## Open Questions

- [ ] Do we want one database engine with separate DBs, or one DB with separate schemas?
- [ ] Which ESS features need to be visible to Sandra vs Alex vs admin only?
- [ ] Which n8n workflows should be launchable from Elio on day one?
- [ ] Does Node 2 have enough resources to host the unified control plane comfortably after consolidation?

## Rollback Rules

- If unified Elio on Node 2 fails validation, keep the old user-facing path alive until the new path passes all Phase 8 checks.
- If WordPress publishing breaks, disable publish actions and keep dashboard read-only until fixed.
- If ESS integration causes instability, keep ESS behind a feature flag in Elio and continue serving core Elio functions.
- If Node 2 resource pressure is too high, keep more AI workloads on Node 1 and reduce Node 2 responsibilities before retrying.

## Completion Log

Use this section to record milestone dates.

- `2026-04-07`: Cutover plan created.
- `2026-04-07`: Runtime inventory captured in `docs/CUTOVER_RUNTIME_INVENTORY_20260407.md`.
- `2026-04-07`: SSH key access enabled for Node 2, `platform_edge` created on Node 2, and repo staged to `/opt/elio`.
- `2026-04-07`: Cutover backup set created at `C:\dev\cutover-backups\20260407-212519`.
- `2026-04-07`: Node 2 staging `.env` prepared and compose-managed Elio API verified healthy on `127.0.0.1:19001`.
- `2026-04-07`: `compose.shared-host.yaml` fixed so the shared-host API port overrides the base port instead of duplicating it.
- `2026-04-08`: ESS runtime code patched in repo to normalize async Postgres URLs, wrap raw SQL with SQLAlchemy `text()`, fix the worker image build path, and adapt Elio SEO stats to ESS daily-report data.
- `2026-04-08`: Minimal ESS staging stack started on Node 2 with `ess_postgres`, `ess_redis`, `ess_api`, and `ess_n8n` bound privately on loopback ports `18080` and `15678`.
- `2026-04-08`: Elio staging API on Node 2 was rebuilt with the latest SEO proxy adapter and verified against the staged ESS API at `http://ess_api:8000/health`.
- `2026-04-08`: ESS worker staged on Node 2 with heartbeat-based health checks; ESS API, worker, and n8n all report healthy under Docker Compose.
- `2026-04-08`: Authenticated Elio staging validation succeeded for `/api/seo/stats` and `/api/n8n/status`, with Elio returning the normalized `items` contract expected by the dashboard.
- `2026-04-08`: Production WordPress validation from Node 2 succeeded after correcting the exact secret transfer into `/opt/ess-ags/.env`; ESS `/api/wordpress/test` returned connected true, and a draft post create/delete cycle completed successfully.
- `2026-04-08`: Phase 4 staging changed the Elio API to serve the `public/` frontend directly; the Node 2 staging path now returns the real app shell and static assets from `127.0.0.1:19001`.
- `2026-04-08`: Local-hosted staging verification succeeded for root HTML, static assets, guide/vendor pages, login, `/system/runtime`, `/api/seo/stats`, and `/chat` using an ephemeral test account that was removed immediately after validation.
- `2026-04-08`: Node 1 Ollama was rebound to the private LAN IP, Node 2 staging was switched onto the `compose.external-models.yaml` split runtime, and Node 2 subagent mission planning was verified against Node 1 Ollama over `http://192.168.1.108:11434/v1`.
- `2026-04-08`: Host-level cutover prep found an existing Ubuntu `nginx` listener on Node 2 port `80` serving another site; an Elio `nginx` vhost for `app.electricsupplysource.co` was tested, then rolled back after it interfered with `illustriousorderilluminat.org`.
- `2026-04-08`: Browser-rendered staging verification confirmed the Elio login shell loads correctly over an SSH tunnel to the Node 2 staging app path.
- `2026-04-08`: The active Node 2 `ioi-portal` host vhost was updated to explicitly match `illustriousorderilluminat.org` and `www.illustriousorderilluminat.org` so the original site is restored cleanly.
