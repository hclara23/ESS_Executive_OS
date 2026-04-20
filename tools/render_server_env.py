import argparse
import secrets
from pathlib import Path

from dotenv import dotenv_values


DEFAULT_EXCLUDES = {
    "ELIO_API_KEY",
    "SERVER",
    "SERVER_PASSWORD",
    "ELIO_SERVER_PORT",
    "ELIO_SERVER_PATH",
}


def _server_host(server_value: str) -> str:
    if not server_value:
        return ""
    candidate = server_value.split("@", 1)[-1]
    return candidate.strip()


def _default_allowed_origins(server_value: str, port: str) -> str:
    origins = [f"http://localhost:{port}", f"http://127.0.0.1:{port}"]
    host = _server_host(server_value)
    if host:
        origins.append(f"http://{host}:{port}")
    return ",".join(origins)


def _apply_defaults(values: dict):
    jwt_secret = values.get("ELIO_JWT_SECRET", "") or ""
    if len(jwt_secret) < 32:
        values["ELIO_JWT_SECRET"] = secrets.token_urlsafe(48)
    values.setdefault("ELIO_LLM_MODE", "hybrid")
    values.setdefault("ELIO_LOCAL_BASE_URL", "http://ollama:11434/v1")
    values.setdefault("ELIO_LOCAL_API_KEY", "ollama")
    values.setdefault("ELIO_SUBAGENT_ENABLED", "true")
    values.setdefault("ELIO_SUBAGENT_URL", "http://subagent:8010")
    values.setdefault("ELIO_TTS_PROVIDER", "kokoro")
    values.setdefault("ELIO_SUBAGENT_TOKEN", secrets.token_urlsafe(32))
    port = str(values.get("ELIO_API_PORT", "8000") or "8000")
    if not values.get("ELIO_ALLOWED_ORIGINS"):
        values["ELIO_ALLOWED_ORIGINS"] = _default_allowed_origins(values.get("SERVER", ""), port)
    return values


def render_server_env(source: Path, output: Path, excludes: set[str], overrides: dict[str, str] | None = None):
    values = dotenv_values(source)
    for key, value in (overrides or {}).items():
        values[key] = value
    values = _apply_defaults(values)
    lines = []
    for key, value in values.items():
        if key in excludes or value is None:
            continue
        lines.append(f"{key}={value}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Render a sanitized .env file for server deployment.")
    parser.add_argument("--source", default=".env")
    parser.add_argument("--output", required=True)
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()

    excludes = set(DEFAULT_EXCLUDES)
    excludes.update(args.exclude)
    overrides = {}
    for item in args.overrides:
        key, _, value = item.partition("=")
        if not key:
            continue
        overrides[key] = value
    render_server_env(Path(args.source), Path(args.output), excludes, overrides)


if __name__ == "__main__":
    main()
