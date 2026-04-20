import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def main():
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    load_dotenv(repo_root / ".env")
    host = os.getenv("ELIO_API_HOST", "0.0.0.0")
    port = int(os.getenv("ELIO_API_PORT", "8000"))
    uvicorn.run("server.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
