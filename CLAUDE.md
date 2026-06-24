## Claude Preamble
<!-- VERSION: 2026-06-20-v53 -->
<!-- SYNC-SOURCE: ~/.claude/conventions/universal-claudemd.md -->

**Universal laws (§1–§55) load via user-level `~/.claude/conventions/` and are ALWAYS in context** — `universal-claudemd.summary.md` (≤50-line salient view, read FIRST) → `universal-claudemd.md` (full) + `project-hygiene.md`. Do **NOT** assume their content from memory; consult + verify before asserting (§34 / §43.6 / §43.7). The `## Active Cluster Playbooks` block below names this repo's situational playbooks **read-on-demand** (§49.10): Read the named playbook when its trigger fires — never guess its contents; always-load guardrails are inline. Sync: `~/.claude/scripts/sync-preambles.py` (manual cadence; run after any source edit).

## Active Cluster Playbooks (read-on-demand — §49.10; bodies at ~/.claude/conventions/playbooks/)
<!-- BEGIN PLAYBOOKS BLOCK (managed by sync-preambles.py — read-on-demand pointers per §49.10; bodies at ~/.claude/conventions/playbooks/) -->

These cluster playbooks apply to this repo. You do NOT know their contents from memory —
**Read the named file when its trigger fires; never assume** (§49.10, §34, §43.6). Bodies are
NOT inlined and NOT @-imported; the always-load GUARDRAILs below are the only parts that must
hold without a Read.

- `commercial-bound.md` — when: license / sponsor-readiness / graph-tool-output / white-label work. GUARDRAIL: never commit/ship GitNexus (PolyForm-NC) graph output from a commercial-bound repo — CGC is the canonical graph source.
- `brand-registry.md` — when: brand / positioning / brand-canon / cross-repo brand work.

<!-- END PLAYBOOKS BLOCK -->

## License classification: free-OSS (MIT)
`bulk` is a sponsor-ready public OSS utility (MIT) — matches the `pulseboard-desktop` posture, NOT commercial-bound (corrects OW-614's framing per `commercial-bound.md` line 39-43, which lists bulk under sponsor-ready-public not commercial-bound). The §50.2 cgc-over-gitnexus guard still applies: any redistributed graph derivative MUST come from CGC (`codegraphcontext`, MIT), never GitNexus (PolyForm-NC). This in-repo line is the routing signal §50.2 wants.

---

# bulk — CLAUDE.md v2

**Date:** 2026-04-28 (S11B authoring)
**Supersedes:** v1 (commit-sha pending S11C verification)
**Tier:** C (Stable / Maintenance)

## Identity & Role

`bulk` is a **production-grade CSV-driven bulk webhook/API firing engine** with adaptive throttling, checkpoint/resume, watchdog auto-processing, REST status API, and SQLite job tracking. Single-file Python app (~191 KB). Public Cramraika org repo, MIT. Renamed from `bulk_api_trigger` → `bulk` 2026-04-19. Supersedes archived `webhook_trigger`. Vagary Labs brand: **OSS Utilities** (sponsor-ready).

<!-- Coolify-DB live-truth as of platform-docs ENTRY #316-T20260512T140000Z (Wave 5-D Substrate Drift Compound, W5-D-CROSS-REPO-PRS subagent) — no `bulk` app present in Coolify (queried `applications` table via SSH fallback to vagary-core-1 since coolify MCP `localhost:3000` unreachable from this Mac session). Confirms DECOMMISSIONED. §53 R2 recurrence path-(a) preventive root-cause per spec `~/.claude/specs/R2-claudemd-coolifydb-drift-rootcause.md` + memory rule `feedback_claudemd_coolify_db_truth_sync.md`. Repo retained as historical artefact; bulk functionality absorbed into vagary-platform notifications-fanout module (A1 refactor commits `3ae5553` + `3f337a7`). -->

## Coverage Today (post-PCN-S6/S7/S11A; DECOMMISSIONED 2026-05-12)

Per matrix row `bulk` (T = decommissioned tombstone; standalone runtime retired):

```
Mail | DNS | RP | Orch | Obs | Backup | Sup | Sec | Tun | Err | Wflw | Spec
 NA  | NA  | NA | NA   | NA  | NA     | T   | NA  | NA  | NA  | NA   | NA
```

- **Production status: DECOMMISSIONED** — no Coolify app present (verified ENTRY #316 Coolify-DB query); all runtime dimensions therefore NA.
- TOMBSTONE (T): Sup dimension only — repo retained on GitHub as historical artefact; absorbed by `vagary-platform` notifications-fanout module.
- Prior matrix row (pre-decommission, retained for historical context only): `U | U | U | U | T | U | T | U | NA | T | NA | NA`.

## What's Wired

- **Production:** **DECOMMISSIONED.** No Coolify app exists (live verification via Coolify-DB query: zero `bulk*` rows in `applications` table). The prior claim "Coolify on Main (Dockerfile build pack)" was drift; the Coolify deployment was retired when `vagary-platform` absorbed bulk's notifications-fanout responsibility (A1 refactor commits `3ae5553` + `3f337a7`). See `vagary-platform/CLAUDE.md` § Dependency Graph for the absorbed module's live home.
- **Historical references (no longer live):** ~~GlitchTip project `bulk-api`; DSN via Coolify env~~ — N/A post-decommission; ~~Loki Promtail Docker SD container `bulk-api-trigger`~~ — N/A; ~~REST endpoints~~ — N/A (the application is no longer running anywhere).
- **CI:** GitHub Actions — lint (flake8 E9,F63,F7) + pip-audit + Docker build. **GREEN** — retained for any future reactivation but no images currently pushed to a live registry.
- **CodeQL** weekly + on PR (Python, security-and-quality) — repo-level scanning preserved.
- **Renovate** weekly Sun 22:00 UTC — dependency hygiene preserved on the artefact.

## Stack

- **Runtime:** Python 3.11 (single-file `webhook_trigger.py`; filename retained for internal-API stability)
- **HTTP:** requests + urllib3 + certifi
- **UX:** tqdm
- **Config:** PyYAML + .env
- **Filesystem monitoring:** watchdog
- **Observability:** sentry-sdk → GlitchTip
- **DB:** SQLite (job history, resume markers, file dedup)
- **Packaging:** Docker (`python:3.11-slim`) + docker-compose; health on `:8000/health`

## Roadmap (post-S11A)

### Cluster 2 — GlitchTip DSN migration to relay
- T (DSN flip pending S11C); route via `glitchtip-relay` on Vagary (port 9095) instead of direct GlitchTip ingest.

### Cluster 3 — Cosign per-repo CI fanout
- T (post host_page PR #50 merge); workflow template at `vps_host/.github/workflow-templates/cosign-sign-image.yml`.

### Phase 9.2 — observability hardening (Cluster 4)
- Already exposes `/metrics` Prom-scrape-ready endpoint
- Add Loki label propagation
- Grafana dashboard

### Existing roadmap (carried forward)
- Uptime Kuma monitor on `/health` (no dedicated monitor yet).
- Infisical workspace `bulk-api-trigger` — switch from Coolify env vars to Agent-delivered env file.
- Staging environment (`staging-bulk.chinmayramraika.in`).
- Single-file refactor audit (~191 KB monolith; defer until concrete maintenance pain).
- Repo file rename `webhook_trigger.py` → `bulk.py` (breaking; defer to next major version).
- Adapter shelves (Salesforce / HubSpot / LeadSquared) if sponsor demand materializes.

## ADR Compliance

- **ADR-038 personal-scope:** ✓ — Cramraika org public; MIT.
- **ADR-033 Renovate canonical:** ✓ — `renovate.json` weekly Sun 22:00 UTC.
- **ADR-041 Trivy gate:** T — pending Cosign fanout post-PR-#50.
- **SOC2 risk-register cross-ref:** Sec/Sup track risks.

## Cross-references

- `platform-docs/05-architecture/part-B-service-appendices/products/bulk.md` (or automation tier)
- `vagary-platform/CLAUDE.md` § Dependency Graph (bulk being absorbed as platform notifications-fanout module; A1 refactor at commits `3ae5553` + `3f337a7`; standalone Coolify app keeps running until retirement workstream opens)
- `~/.claude/conventions/universal-claudemd.md` §41 brand architecture (OSS Utilities)

## Migration from v1

**Major v1 → v2 changes:**
1. Per-project-service-matrix row added (notably USED for Mail — surprising-cell flag per CX-MATRIX: only repo currently using transactional SMTP).
2. Cluster 2 GlitchTip relay migration queued S11C.
3. Cluster 3 Cosign CI fanout queued post-PR-#50.
4. Cluster 4 observability hardening flagged Phase 9.2.
5. Renamed-from-webhook_trigger trajectory cited (archived 2026-04-19).
6. Absorption trajectory by vagary-platform noted (A1 refactor done; standalone keeps running).

---

## VPS Service Navigation

`bulk` is **DECOMMISSIONED** (no Coolify app — verified ENTRY #316 Coolify-DB query; notifications-fanout absorbed by `vagary-platform`). It currently consumes no live dual-VPS service. This stub is retained so a future revival session has the navigation pattern; canonical service playbooks live in `platform-docs/02-governance/service-playbooks/`.

| Service | State | If revived |
|---|---|---|
| **Infisical** (secrets) | No active project — `bulk` is OSS; credentials are downstream-user-supplied (W12: nothing to onboard) | Create a `bulk` Infisical project per `service-playbooks/substrate/infisical.md` §6 wiring guide + §9.5 |
| **Coolify** (orchestration) | Decommissioned — no app row in Coolify-DB | Register via Coolify API per `service-playbooks/substrate/coolify.md` §5 |
| **Observability** | n/a — no running deployment | `service-playbooks/observability/*.md` |
