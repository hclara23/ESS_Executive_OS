import json
import os
import sys


BASE = "Data"


def _write(path, data, force=False):
    if os.path.exists(path) and not force:
        print(f"Skip {path}. Use --force to overwrite.")
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {path}")


def main():
    force = "--force" in sys.argv

    integrations = {
        "gmail": {
            "connected": False,
            "client_id": "YOUR_GMAIL_CLIENT_ID",
            "client_secret": "YOUR_GMAIL_CLIENT_SECRET",
            "redirect_uri": "http://localhost:8080/",
        },
        "calendar": {
            "connected": False,
            "client_id": "YOUR_CALENDAR_CLIENT_ID",
            "client_secret": "YOUR_CALENDAR_CLIENT_SECRET",
            "redirect_uri": "http://localhost:8080/",
        },
        "quickbooks": {
            "connected": False,
            "client_id": "YOUR_QBO_CLIENT_ID",
            "client_secret": "YOUR_QBO_CLIENT_SECRET",
            "redirect_uri": "http://localhost:8080/",
        },
    }

    postgres = {"uri": "postgresql://USER:PASSWORD@HOST:5432/DBNAME", "schema": "public"}

    os.makedirs(BASE, exist_ok=True)
    _write(os.path.join(BASE, "integrations.json"), integrations, force=force)
    _write(os.path.join(BASE, "postgres_config.json"), postgres, force=force)


if __name__ == "__main__":
    main()
