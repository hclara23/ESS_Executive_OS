WisCore / Elio API — Local Dev Quick Reference

This file lists useful endpoints and example curl commands for local development.

Base URL

- Default local base URL: http://127.0.0.1:8001

Useful endpoints

- Health
  - GET /health
  - curl -sS http://127.0.0.1:8001/health

- API helper (returns example curl commands)
  - GET /api
  - curl -sS http://127.0.0.1:8001/api

- Public WisCore
  - POST /wiscore/rfq  (public intake — required fields: name, company, email, description, items)
  - POST /wiscore/emergency (public emergency — required fields: name, company, email, description, message)
  - POST /wiscore/assistant_public (public assistant; rate-limited)

- Protected WisCore (requires Bearer token with client: "wiscore")
  - GET /wiscore/state
  - POST /wiscore/assistant
  - PATCH /wiscore/leads/{lead_id}
  - GET /wiscore/leads/{lead_id}/quote-draft

- Development debug endpoints
  - GET /wiscore/debug/state  (available only from localhost or when ELIO_ALLOW_DEBUG=1)

Login

- POST /login
  - Body JSON: {"username": "<user>", "password": "<pw>", "client": "wiscore"}
  - Response: {"ok": true, "token": "<JWT>", "username": "..."}

Notes

- `client` claim in JWT determines tenant: "elio" (default) or "wiscore". Issuing non-default `client` is restricted to admin users or the email in `ELIO_SUPERUSER_EMAIL`.
- For local dev, use `wiscore_staff.html` which posts `client: 'wiscore'` and stores `wiscoreToken` in localStorage.
- The public assistant is deliberately lightweight and rate-limited. For production, replace the in-memory rate limiter with Redis and add CAPTCHA or API-keys for abuse prevention.
  - To enable Redis-backed rate limiting, set the `ELIO_REDIS_URL` environment variable to a redis URL (e.g. `redis://localhost:6379/0`). The server will automatically use Redis when available and fall back to an in-memory limiter.
  - Example: `ELIO_REDIS_URL=redis://127.0.0.1:6379/0 python -m uvicorn server.app:app --reload`

- Developer debug page

- GET /wiscore/debug/state  (available only from localhost or when ELIO_ALLOW_DEBUG=1)
- HTML debug page: `/wiscore_debug.html` — prettier, fetches `/wiscore/debug/state` and renders JSON for local debugging.
