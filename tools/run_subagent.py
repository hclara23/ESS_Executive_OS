import os

import uvicorn


if __name__ == "__main__":
    host = os.getenv("ELIO_SUBAGENT_HOST", "0.0.0.0")
    port = int(os.getenv("ELIO_SUBAGENT_PORT", "8010"))
    uvicorn.run("server.subagent:app", host=host, port=port, reload=False)
