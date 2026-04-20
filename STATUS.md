# ELIO Status

## Current Version

`4.0.0` | Unified Communications Edition

## Active Architecture

- Main API: `server.app`
- Message Center: `server.mail_service`
- Private subagent: `server.subagent`
- LLM routing layer: `server.ai_provider`
- Voice provider layer: `server.voice_provider`
- Job queue and scheduler: `server.jobs`
- Personality profiles: `Data/personality.json` + `Data/personality_profiles.json`

## Components

- **Message Center:** Unified Inbox/Sent/History dashboard with AI Triage (IMAP/SMTP).
- **Executive Boards:** Custom dashboards for Sandra (Finance) and Alex (Engineering).
- **Knowledge Library:** PDF-backed semantic RAG engine.
- **Bidding Hub V2:** Autonomous proposal scouting and profit modeling.
- **Meeting Hub:** Live transcription and action item extraction.

## Ports

- `8000` default main API host port, override with `ELIO_API_PORT`
- `8010` private subagent
- `11434` Ollama
- `5432` Postgres
- `8020` optional XTTS voice-clone service

## Security Posture

- JWT required for web auth
- Passwords hashed with PBKDF2
- Cross-user reads and todo mutations restricted unless admin
- Reports locked to the `reports/` directory
- Private subagent protected by shared token and internal exposure only
- `.env` ignored by git

## Default Model Strategy

- Local-first for intake, missions, meetings, proposals, embeddings
- Cloud-first for primary reasoning, self-audit, code generation, and vision
- All task routing is env-configurable

## Default Voice Strategy

- Kokoro ONNX local TTS
- Profile-driven default voice selection
- Per-user XTTS cloned voices supported through profile user overrides
- Optional remote/local TTS service support via `ELIO_TTS_PROVIDER=remote`
- Optional XTTS sidecar via `compose.xtts.yaml`

## Ops Shortcuts

- Start stack: `docker compose up -d`
- Pull local models: `powershell -ExecutionPolicy Bypass -File .\tools\bootstrap_local_models.ps1`
- Inspect runtime: `GET /system/runtime`
- Check health: `GET /health`
- Remote runtime snapshot: `python .\tools\remote_runtime_snapshot.py --base-url http://localhost:<ELIO_API_PORT>`
- Remote backup: `powershell -ExecutionPolicy Bypass -File .\tools\run_remote_backup.ps1 -Download`
