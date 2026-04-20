import argparse
import json
import sys
import urllib.parse
import urllib.error
import urllib.request


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 30):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_status(url: str, headers: dict | None = None, timeout: int = 30):
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.headers


def main():
    parser = argparse.ArgumentParser(description="Smoke-test the local Elio stack.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--tts-timeout", type=int, default=300)
    parser.add_argument("--check-tts", action="store_true")
    parser.add_argument("--check-xtts", action="store_true")
    parser.add_argument("--xtts-url", default="")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    checks = [
        ("root", f"{base_url}/"),
        ("docs", f"{base_url}/docs"),
    ]

    failed = False
    runtime = None

    for name, url in checks:
        try:
            status, _ = fetch_status(url, timeout=args.timeout)
            print(f"[ok] {name}: {status}")
        except Exception as exc:
            failed = True
            print(f"[fail] {name}: {exc}")

    auth_headers = None
    if args.username and args.password:
        try:
            login_response = post_json(
                f"{base_url}/login",
                {"username": args.username, "password": args.password},
                timeout=args.timeout,
            )
            token = login_response["token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
            runtime_request = urllib.request.Request(
                f"{base_url}/system/runtime",
                headers={"Accept": "application/json", **auth_headers},
            )
            with urllib.request.urlopen(runtime_request, timeout=args.timeout) as response:
                runtime = json.loads(response.read().decode("utf-8"))
            voice = runtime.get("voice", {})
            personality = runtime.get("personality", {})
            print(
                "[ok] runtime: "
                f"llm_mode={runtime['llm']['mode']} "
                f"voice={voice.get('provider')} "
                f"default_voice={voice.get('default_voice')} "
                f"profile={personality.get('profile')} "
                f"tone={personality.get('tone')}"
            )
        except Exception as exc:
            failed = True
            print(f"[fail] auth/runtime: {exc}")
    else:
        print("[info] runtime auth checks skipped; provide --username and --password to verify /system/runtime.")

    if args.check_tts:
        if not auth_headers:
            failed = True
            print("[fail] tts: --check-tts requires --username and --password.")
        else:
            try:
                tts_url = f"{base_url}/tts?text={urllib.parse.quote('Elio smoke test')}"
                status, headers = fetch_status(tts_url, headers=auth_headers, timeout=max(args.timeout, args.tts_timeout))
                print(f"[ok] tts: {status} {headers.get_content_type()}")
            except Exception as exc:
                failed = True
                print(f"[fail] tts: {exc}")

    if args.check_xtts:
        if args.xtts_url:
            try:
                data = fetch_json(args.xtts_url)
                print(f"[ok] xtts: model={data.get('model')} speaker_dir={data.get('speaker_dir')}")
            except Exception as exc:
                failed = True
                print(f"[fail] xtts: {exc}")
        elif runtime and runtime.get("voice", {}).get("provider") == "remote":
            print(
                "[ok] xtts: "
                f"provider={runtime['voice'].get('provider')} "
                f"remote_url={runtime['voice'].get('remote_url')} "
                f"default_voice={runtime['voice'].get('default_voice')}"
            )
        else:
            failed = True
            print("[fail] xtts: provide --username/--password for runtime checks or pass --xtts-url explicitly.")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
