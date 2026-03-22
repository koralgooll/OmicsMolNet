#!/usr/bin/env python3
"""
One-time Flowise bootstrap.

Flowise shows `/organization-setup` when no admin account exists yet.
This script creates the initial admin account by POSTing to:
  /api/v1/account/register

Idempotent: if the account already exists (or validation fails), exits 0 so
`docker compose up -d` remains usable.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


def _env_trim(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def main() -> int:
    required = ("FLOWISE_ADMIN_NAME", "FLOWISE_ADMIN_EMAIL", "FLOWISE_ADMIN_PASSWORD")
    if not all(_env_trim(k) for k in required):
        print(
            "[flowise-init] Missing required env vars; skipping bootstrap. "
            f"Need: {', '.join(required)}"
        )
        return 0

    api_base = (_env_trim("FLOWISE_API_BASE_URL") or "http://flowise:3000").rstrip("/")
    admin_name = _env_trim("FLOWISE_ADMIN_NAME")
    admin_email = _env_trim("FLOWISE_ADMIN_EMAIL")
    admin_password = os.environ.get("FLOWISE_ADMIN_PASSWORD", "")
    org_name = _env_trim("FLOWISE_ORG_NAME")

    payload: dict = {
        "user": {
            "name": admin_name,
            "email": admin_email,
            "credential": admin_password,
        }
    }
    # Enterprise only: server/UI add organization.name when enterprise licensed.
    if org_name:
        payload["organization"] = {"name": org_name}

    endpoint = f"{api_base}/api/v1/account/register"
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-request-from": "internal",
    }

    for attempt in range(1, 16):
        req = urllib.request.Request(
            endpoint, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                text = resp.read().decode(errors="replace")
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                text = e.read().decode(errors="replace")
            except Exception:
                text = ""
        except urllib.error.URLError as e:
            print(f"[flowise-init] attempt {attempt} failed: {e}")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"[flowise-init] attempt {attempt} failed: {e}")
            time.sleep(2)
            continue

        print(f"[flowise-init] register attempt {attempt}: HTTP {status}")

        if 200 <= status < 300:
            print("[flowise-init] bootstrap successful")
            return 0

        # Common "already created"/"validation" cases - treat as idempotent success.
        if status in (400, 409, 422):
            print(
                "[flowise-init] non-fatal response (likely already configured):",
                text or "<empty>",
            )
            return 0

        # If Flowise requires auth for this endpoint, we can't proceed without more logic.
        if status in (401, 403):
            print(
                "[flowise-init] registration endpoint rejected the request (auth required):",
                text or "<empty>",
                file=sys.stderr,
            )
            return 1

        time.sleep(2)

    print("[flowise-init] giving up after retries (non-fatal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
