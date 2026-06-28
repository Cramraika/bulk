"""
fleet_egress_client — opt-in adapter: route bulk's webhook egress through the
fleet-webhook-egress service instead of bulk's in-repo delivery loop.

OW-698 (capability extraction). The fleet service owns HMAC signing, durable
retry (exp-backoff + Retry-After), circuit-breaking, SSRF guard, and PG delivery
audit — so bulk no longer re-implements them. This adapter is **opt-in**: it is
active ONLY when FLEET_WEBHOOK_EGRESS_URL is set; otherwise the caller keeps
bulk's existing inline path (zero behavior change, safe cutover).

Wiring (see docs/fleet-webhook-egress-integration.md): at the row-send site in
webhook_trigger.py, branch to `enqueue()` when `is_enabled()`.

Security: the HMAC signing secret is NEVER sent by bulk — it is resolved
server-side per org by the fleet service (Infisical-rendered). bulk only holds
the service bearer token (FLEET_WEBHOOK_EGRESS_TOKEN), itself Infisical-rendered.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import requests


def is_enabled() -> bool:
    """True when the fleet egress service is configured (opt-in)."""
    return bool(os.getenv("FLEET_WEBHOOK_EGRESS_URL", "").strip())


def _base_url() -> str:
    return os.getenv("FLEET_WEBHOOK_EGRESS_URL", "").rstrip("/")


def _org() -> str:
    return os.getenv("FLEET_WEBHOOK_EGRESS_ORG", "bulk")


def _headers() -> Dict[str, str]:
    token = os.getenv("FLEET_WEBHOOK_EGRESS_TOKEN", "")
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def enqueue(
    url: str,
    payload: Dict[str, Any],
    *,
    event_type: str = "bulk.webhook.fired",
    custom_headers: Optional[Dict[str, str]] = None,
    idempotency_key: Optional[str] = None,
    max_attempts: Optional[int] = None,
    timeout: float = 10.0,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Hand a delivery job to the fleet service (it owns retry/sign/audit).

    Returns (accepted, delivery_id, error). `accepted` means the service durably
    QUEUED the job (HTTP 202/200) — final delivery happens asynchronously in the
    service; query GET /v1/deliveries/<id> for terminal status.
    """
    body: Dict[str, Any] = {
        "organization_id": _org(),
        "url": url,
        "event_type": event_type,
        "payload": payload if isinstance(payload, dict) else {"value": payload},
    }
    if custom_headers:
        body["custom_headers"] = custom_headers
    if idempotency_key:
        body["idempotency_key"] = idempotency_key
    if max_attempts:
        body["max_attempts"] = max_attempts

    try:
        resp = requests.post(
            f"{_base_url()}/v1/deliveries",
            json=body,
            headers=_headers(),
            timeout=timeout,
        )
    except requests.RequestException as e:
        return False, None, f"egress service unreachable: {e}"

    if resp.status_code in (200, 202):
        try:
            data = resp.json()
        except ValueError:
            return True, None, None
        return True, data.get("delivery_id"), None
    return False, None, f"egress service returned HTTP {resp.status_code}: {resp.text[:200]}"


def get_status(delivery_id: str, *, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """Poll a delivery's terminal status (queued/delivering/succeeded/failed/dead_letter)."""
    try:
        resp = requests.get(
            f"{_base_url()}/v1/deliveries/{delivery_id}",
            headers=_headers(),
            timeout=timeout,
        )
    except requests.RequestException:
        return None
    if resp.status_code == 200:
        try:
            return resp.json()
        except ValueError:
            return None
    return None
