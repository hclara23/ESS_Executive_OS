import sys

from Features.PostgresStore import ensure_schema, sync_postgres
from dotenv import load_dotenv

load_dotenv()


def main():
    if "--setup" in sys.argv:
        ok = ensure_schema()
        print("Postgres tables are ready." if ok else "Postgres is not ready.")
        return
    if "--sync" in sys.argv:
        print(sync_postgres())
        return
    print("Usage: python tools/postgres_setup.py --setup | --sync")


if __name__ == "__main__":
    main()
