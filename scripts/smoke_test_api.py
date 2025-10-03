#!/usr/bin/env python3
"""
scripts/smoke_test_api.py

Small smoke-test script for the BTM Workout API.

It performs the following steps against a target base URL (default http://127.0.0.1:5000):
  - POST /api/v1/insert_exercise with a unique test exercise
  - GET /api/v1/exercise/<name> to verify retrieval
  - DELETE /api/v1/delete_exercise/<name> to clean up
  - GET again to ensure the exercise is gone

The script refuses to run against the production Render host by default
('btm-workout.onrender.com') unless --allow-prod is provided.

Exit codes:
  0 - success
  1 - failure (prints diagnostic information)

Usage:
  python3 scripts/smoke_test_api.py
  python3 scripts/smoke_test_api.py --base-url http://127.0.0.1:5000
  python3 scripts/smoke_test_api.py --base-url https://btm-workout.onrender.com --allow-prod

"""
import argparse
import sys
import time
import random
import string

try:
    import requests
except Exception:
    print(
        "Error: the 'requests' package is required. Install with: pip install requests"
    )
    sys.exit(1)


PROD_HOSTS = ["btm-workout.onrender.com", "btm-workout.onrender.com/"]


def random_suffix(n=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def main():
    parser = argparse.ArgumentParser(description="Smoke test the BTM Workout API")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:5000",
        help="Base URL of the API (default http://127.0.0.1:5000)",
    )
    parser.add_argument(
        "--allow-prod",
        action="store_true",
        help="Allow running against production hosts (unsafe)",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="HTTP request timeout in seconds"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Do not delete the inserted test document (for manual inspection)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform requests but don't write (best-effort) - note: server may still record requests",
    )

    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    # Safety: refuse to run against known production host unless explicitly allowed
    for ph in PROD_HOSTS:
        if ph in base and not args.allow_prod:
            print(
                f"Refusing to run against production host '{ph}' without --allow-prod."
            )
            print(
                "If you really want to run against production, pass --allow-prod explicitly."
            )
            sys.exit(2)

    # Compose endpoints
    insert_url = f"{base}/api/v1/insert_exercise"
    get_url_template = f"{base}/api/v1/exercise/{{name}}"
    delete_url_template = f"{base}/api/v1/delete_exercise/{{name}}"

    suffix = random_suffix()
    test_name = f"smoke-test-{int(time.time())}-{suffix}"

    payload = {
        "exercise_name": test_name,
        "body_part": "smoke-test-bodypart",
        "equipment": "smoke-test-equipment",
        "target": "smoke-test-target",
        "instructions": ["Do this.", "Do that."],
        "difficulty": "Beginner",
    }

    print("[1/4] INSERT", insert_url)
    try:
        if args.dry_run:
            print("Dry-run: skipping insert request")
            r = None
        else:
            r = requests.post(insert_url, json=payload, timeout=args.timeout)
    except Exception as e:
        print("Insert request failed:", e)
        sys.exit(1)

    if not args.dry_run and r.status_code not in (200, 201):
        print(f"Insert failed: status={r.status_code}, body={r.text}")
        sys.exit(1)

    if not args.dry_run:
        print("Insert succeeded:", r.json())
    else:
        print("Insert dry-run completed (no write performed).")

    # GET
    get_url = get_url_template.format(name=test_name)
    print("[2/4] GET", get_url)
    try:
        r = requests.get(get_url, timeout=args.timeout)
    except Exception as e:
        print("Get request failed:", e)
        sys.exit(1)

    if r.status_code != 200:
        print(f"Get failed: status={r.status_code}, body={r.text}")
        sys.exit(1)

    got = r.json()
    # Quick sanity checks
    if got.get("exercise_name") != test_name:
        print("Returned exercise doesn't match inserted name:", got)
        sys.exit(1)

    print("Get succeeded. Document:", got)

    # DELETE
    delete_url = delete_url_template.format(name=test_name)
    if args.no_cleanup:
        print(
            "--no-cleanup provided; skipping delete step. You must remove the test doc manually."
        )
    else:
        print("[3/4] DELETE", delete_url)
        try:
            if args.dry_run:
                print("Dry-run: skipping delete request")
                r = None
            else:
                r = requests.delete(delete_url, timeout=args.timeout)
        except Exception as e:
            print("Delete request failed:", e)
            sys.exit(1)

        if not args.dry_run and r.status_code not in (200, 202):
            print(f"Delete failed: status={r.status_code}, body={r.text}")
            sys.exit(1)

        if not args.dry_run:
            print("Delete succeeded:", r.json())
        else:
            print("Delete dry-run completed (no delete performed).")

    # Final GET should return 404
    print("[4/4] GET (should be 404)", get_url)
    try:
        r = requests.get(get_url, timeout=args.timeout)
    except Exception as e:
        print("Final get request failed:", e)
        sys.exit(1)

    if r.status_code == 404:
        print("Final GET returned 404 as expected. Smoke test PASSED.")
        sys.exit(0)
    else:
        print(f"Final GET unexpected status={r.status_code}, body={r.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()
