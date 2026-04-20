import os
from dotenv import load_dotenv
from Features.PostgresStore import ensure_schema
from server.store import create_user

load_dotenv()

if __name__ == "__main__":
    print("Syncing Neon Database Schema...")
    success = ensure_schema()
    if success:
        print("Success: Neon Database is synchronized and ready.")
        
        print("Seeding default users...")
        create_user("sandra", "password123")
        create_user("alex", "password123")
        create_user("morningstar", "password", is_admin=True)
        print("Success: Users seeded.")
    else:
        print("Error: Failed to synchronize Neon Database. Check ELIO_PG_URI.")
