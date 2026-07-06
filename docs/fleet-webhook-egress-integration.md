# Integration: route bulk egress through fleet-webhook-egress (OW-698)

**Status:** WIRED on `main` 2026-07-06 — the opt-in branch is APPLIED at the send-site (`make_request`, before the retry loop) and the fleet service is deployed + live (`vagary-core/services/webhook-egress`, `fleet-webhook-egress:0.1.0` on compute-1). Inert until `FLEET_WEBHOOK_EGRESS_URL` is set; bulk is decommissioned so there is no live cutover to run — the wire is code-complete, opt-in, and degrade-safe (enqueue failure falls through to the inline path).

## Why

bulk re-implemented resilient webhook egress (HMAC, exp-backoff/Retry-After, rate-limit, resume) that already exists, more maturely, in vagary-voice's `webhook-service/delivery-engine.ts`. Per the cross-repo capability census (`platform-docs/docs/audits/2026-06-29-cross-repo-capability-census.md`), that capability was extracted into the standalone **fleet-webhook-egress** HTTP service (`vagary-voice/fleet-webhook-egress/`, design `platform-docs/docs/specs/2026-06-29-fleet-webhook-egress-extraction.md`). bulk is the **anchor consumer**: it should hand delivery jobs to the service instead of re-running egress itself.

The fleet is polyglot (bulk = Python, the service = Node), so leverage is **HTTP-service consumption, not library import** — exactly what `fleet_egress_client.py` does.

## What this branch adds

- `fleet_egress_client.py` — opt-in adapter. `enqueue(url, payload, …)` POSTs a durable delivery job to the service; `get_status(id)` polls terminal status.

## Opt-in wiring (zero behavior change when unset)

The adapter is active **only when `FLEET_WEBHOOK_EGRESS_URL` is set**. When unset, bulk keeps its existing inline delivery path verbatim. This makes the cutover reversible and safe.

At the row-send site in `webhook_trigger.py` (the `http_session.request(...)` call around L1460–1484), branch first:

```python
import fleet_egress_client

# inside the per-row send, before the inline http_session.request(...) path:
if fleet_egress_client.is_enabled():
    accepted, delivery_id, err = fleet_egress_client.enqueue(
        url,
        payload if isinstance(payload, dict) else {"value": payload},
        event_type="bulk.webhook.fired",
        custom_headers=headers or None,
        idempotency_key=f"{job_id}:{row_index}",   # dedup across resume/replay
    )
    if accepted:
        # the service now owns retry/sign/audit; record the queued result and move on
        results_tracker.record({
            "url": url, "method": method_u, "status": "queued",
            "status_code": 202, "delivery_id": delivery_id,
            "timestamp": datetime.now().isoformat(),
        })
        return 0
    # on enqueue failure, fall through to the existing inline path (degrade-safe)
```

(APPLIED 2026-07-06 in `make_request()` just before the retry loop — the fleet service owns retry, so
the offload happens once, not per-attempt. The in-scope idempotency key is a content hash of
`method:url:payload` — `make_request` has no `job_id`/`row_index`, and the hash dedups identical rows on
resume/replay just the same. Verified: `python3 -m py_compile` OK; `is_enabled()` False when the env var is
unset (zero behavior change) / True when set.)

## Config (Infisical-rendered at deploy)

| Env | Meaning |
|---|---|
| `FLEET_WEBHOOK_EGRESS_URL` | tailnet base URL of the service, e.g. `http://100.64.0.2:3011` (unset = adapter off) |
| `FLEET_WEBHOOK_EGRESS_TOKEN` | service bearer token |
| `FLEET_WEBHOOK_EGRESS_ORG` | tenant scope (default `bulk`) |

bulk never sends the HMAC signing secret — the service resolves it server-side per org.

## Cutover

Per the spec §8 / §54: provision creds → deploy the service (tailnet-bound) → set the three env vars on bulk → deploy bulk → health-check → only then retire bulk's inline egress. Serialized, one repo at a time.
