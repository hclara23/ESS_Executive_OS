# Security

## Current Auth Model

- Web/API sessions use JWTs signed by `ELIO_JWT_SECRET`
- Secret-at-rest encryption derives from `ELIO_DATA_KEY` when set, otherwise from `ELIO_JWT_SECRET`
- Passwords are stored hashed with PBKDF2
- Device-token fallback remains for device registration flows only
- The old raw `ELIO_API_KEY` web-login path is removed

## Secrets

- Keep `.env` local only
- Do not store server passwords in plaintext `.env` entries
- Use SSH keys for the server
- Use a long random `ELIO_SUBAGENT_TOKEN` for API-to-subagent calls
- Set `ELIO_DATA_KEY` if you want a dedicated encryption root for stored operational secrets

## Network Exposure

Expose only the main API unless you have a strong reason to do otherwise.

- `ELIO_API_PORT`: okay to expose behind your preferred reverse proxy
- `8010`: internal only
- `8020`: internal only
- `11434`: loopback only
- `5432`: loopback only

## Data Access Controls

- Non-admin users cannot read or mutate another user's audit, brain, insight, lesson, or todo data
- Report downloads are limited to the `reports/` directory
- Knowledge document deletes reject path traversal

## Local AI Notes

Local models lower cost and reduce third-party exposure, but they do not remove the need for normal security discipline.

- keep Ollama private
- keep the subagent narrow and tool-limited
- treat local model outputs as untrusted until validated by application logic
