import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import dotenv_values


def fetch(url: str):
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def post(url: str, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_with_headers(url: str, headers: dict[str, str]):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Fetch a runtime snapshot from an Elio API.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    env_values = {}
    env_path = Path(args.env_file)
    if env_path.exists():
        env_values = dotenv_values(env_path)
    username = args.username or env_values.get("ELIO_ADMIN_USER") or os.getenv("ELIO_ADMIN_USER", "")
    password = args.password or env_values.get("ELIO_ADMIN_PASS") or os.getenv("ELIO_ADMIN_PASS", "")

    try:
        root_data = fetch(f"{base_url}/")
    except Exception as exc:
        print(f"Failed to reach API root: {exc}", file=sys.stderr)
        sys.exit(1)

    payload = {"root": root_data}
    if username and password:
        try:
            login = post(f"{base_url}/login", {"username": username, "password": password})
            token = login["token"]
            payload["runtime"] = fetch_with_headers(
                f"{base_url}/system/runtime",
                {"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
        except Exception as exc:
            payload["runtime_error"] = str(exc)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
