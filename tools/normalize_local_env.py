import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import dotenv_values

from tools.render_server_env import _apply_defaults

DROP_KEYS = {"SERVER_PASSWORD", "ELIO_API_KEY"}


def _write_env(path: Path, values: dict):
    lines = []
    for key, value in values.items():
        if value is None:
            continue
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Normalize local .env values for the local-server Elio stack.")
    parser.add_argument("--path", default=".env")
    parser.add_argument("--api-port", default=None)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()

    path = Path(args.path)
    values = dict(dotenv_values(path))
    if args.api_port:
        values["ELIO_API_PORT"] = args.api_port
    for key in DROP_KEYS:
        values.pop(key, None)
    for item in args.overrides:
        key, _, value = item.partition("=")
        if not key:
            continue
        values[key] = value
    values = _apply_defaults(values)
    _write_env(path, values)


if __name__ == "__main__":
    main()
