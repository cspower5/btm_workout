#!/usr/bin/env python3
"""
Safe Render env var merger.

Usage:
  export RENDER_API_KEY=your_render_api_key
  python3 scripts/render_merge_env.py --service-id srv-xxxx --key ADMIN_PREVIEW_TOKEN --value <token> [--secure]

The script will:
 - fetch existing env vars for the service (tries /env-vars endpoint first, falls back to service object)
 - back them up to a timestamped JSON file locally
 - merge or add the provided key/value (secure flag preserved if set)
 - PATCH the service with the merged `envVars` array

WARNING: The Render API replaces envVars when PATCHing the `envVars` array. This script attempts to preserve all existing vars by fetching and merging first.
Run this locally and keep your RENDER_API_KEY secret.
"""

import argparse
import json
import os
import sys
import time
from urllib import request, error


API_BASE = "https://api.render.com/v1"


def get_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def http_get(url, headers):
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req) as resp:
        return resp.read().decode()


def http_patch(url, headers, data_bytes):
    req = request.Request(url, data=data_bytes, headers=headers, method="PATCH")
    with request.urlopen(req) as resp:
        return resp.read().decode()


def fetch_env_vars(api_key, service_id):
    headers = get_headers(api_key)
    # Try v1/services/{id}/env-vars first (preferred)
    url_env = f"{API_BASE}/services/{service_id}/env-vars"
    try:
        body = http_get(url_env, headers)
        return json.loads(body)
    except error.HTTPError as e:
        # fallback to fetching the service object
        if e.code not in (404,):
            raise
    except Exception:
        # any non-HTTP issue - fall through to try service object
        pass

    url_service = f"{API_BASE}/services/{service_id}"
    body = http_get(url_service, headers)
    obj = json.loads(body)
    # service objects may include envVars at top-level or in serviceDetails; try both
    envs = obj.get("envVars")
    if envs is None:
        # attempt serviceDetails.envVars
        sd = obj.get("serviceDetails") or {}
        envs = sd.get("envVars")
    # Ensure we return a list
    return envs or []


def merge_env_vars(existing, key, value, secure):
    merged = []
    seen = set()
    # keep existing, replace if key matches
    for item in existing:
        k = item.get("key")
        if k == key:
            # replace with provided value and secure
            merged.append({"key": key, "value": value, "secure": bool(secure)})
            seen.add(key)
        else:
            merged.append(item)
            seen.add(k)

    if key not in seen:
        merged.append({"key": key, "value": value, "secure": bool(secure)})

    return merged


def backup_envs(envs, service_id):
    ts = time.strftime("%Y%m%dT%H%M%SZ")
    fname = f"render_env_backup_{service_id}_{ts}.json"
    with open(fname, "w") as f:
        json.dump(envs, f, indent=2)
    return fname


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--service-id", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    p.add_argument(
        "--secure", action="store_true", help="Mark new/updated var as secure"
    )
    p.add_argument(
        "--api-key",
        default=os.getenv("RENDER_API_KEY"),
        help="Render API key (or set RENDER_API_KEY env var)",
    )
    args = p.parse_args()

    if not args.api_key:
        print(
            "Missing Render API key. Set RENDER_API_KEY or pass --api-key.",
            file=sys.stderr,
        )
        sys.exit(2)

    service_id = args.service_id
    api_key = args.api_key

    print("Fetching current env vars...")
    existing = fetch_env_vars(api_key, service_id)
    print(f"Found {len(existing)} existing env vars")

    backup_file = backup_envs(existing, service_id)
    print(f"Backed up current env vars to {backup_file}")

    merged = merge_env_vars(existing, args.key, args.value, args.secure)

    payload = {"envVars": merged}
    data = json.dumps(payload).encode()

    patch_url = f"{API_BASE}/services/{service_id}"
    print(
        "Patching service with merged envVars (this will replace envVars array on the service)..."
    )
    resp = http_patch(patch_url, get_headers(api_key), data)
    print("Patch response:")
    print(resp)


if __name__ == "__main__":
    main()
