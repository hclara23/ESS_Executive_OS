from Features.PostgresStore import ensure_schema, sync_postgres


def main():
    ok = ensure_schema()
    print("Postgres tables are ready." if ok else "Postgres is not ready.")
    print(sync_postgres())


if __name__ == "__main__":
    main()
