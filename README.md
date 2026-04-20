# ELIO | Local-First Executive Assistant

Elio is a private assistant stack for Alex and Sandra. The app now runs as a local-first system: the main API stays in control, a private subagent handles cheaper background reasoning, Ollama serves local models, and Kokoro provides on-box speech.

## Repository & Hosting

- **Git repository:** [hclara23/ESS_Executive_OS](https://github.com/hclara23/ESS_Executive_OS)
- **Frontend (Firebase):** [elioos.web.app](https://elioos.web.app) — Firebase project `elioos` (ElioOS)
- **Target app domain:** [app.electricsupplysource.co](https://app.electricsupplysource.co) (DNS/TLS cutover pending)

## What Changed

- **Unified Message Center Dashboard:** A new premium PWA view for managing multi-account emails with integrated AI Triage.
- **Multi-User Email Infrastructure:** Enhanced `MailService` with IMAP/SMTP support for HostGator (ELIO) and GoDaddy (Executives) identities.
- **Autonomous Triage Engine:** Logic to classify incoming mail, extract action items, and suggest draft replies.
- JWT-only authentication with hashed passwords and no `ELIO_API_KEY` login backdoor
- Hybrid model routing: local for repetitive work, cloud for harder reasoning
- Private subagent container for intake, mission planning, meeting parsing, and proposal drafting
- DB-backed background job queue with retryable recurring jobs
- Personality profiles and voice defaults loaded from `Data/personality.json` and `Data/personality_profiles.json`
- Runtime visibility at `GET /system/runtime`
- Health visibility at `GET /health`

## Local Stack

Primary docs:

- [Local Stack](docs/LOCAL_STACK.md)
- [Shared Server Guide](docs/SHARED_SERVER.md)
- [Unified Elio + ESS Cutover](docs/ELIO_ESS_UNIFIED_CUTOVER.md)
- [Runtime Inventory 2026-04-07](docs/CUTOVER_RUNTIME_INVENTORY_20260407.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Configuration Reference](config.md)
- [Security Notes](SECURITY.md)
- [Status Snapshot](STATUS.md)

Default service layout:

| Service | Port | Exposure | Purpose |
| --- | --- | --- | --- |
| `api` | `8000` by default | public on the server/LAN as you choose | Main Elio API and dashboard backend |
| `subagent` | `8010` | internal only | Private worker for cheap/high-volume AI tasks |
| `ollama` | `11434` | loopback only | Local LLM and embedding server |
| `postgres` | `5432` | loopback only | Local relational store if you are not using Neon |
| `xtts` | `8020` | internal only when enabled | Optional cloned-voice TTS sidecar |

## Quick Start

1. Copy `.env.example` to `.env` and fill in the secrets.
2. Start the stack: `docker compose up -d`
3. Pull the recommended local models: `powershell -ExecutionPolicy Bypass -File .\tools\bootstrap_local_models.ps1`
4. Open `http://localhost:<ELIO_API_PORT>/docs` or your hosted frontend.

The bootstrap path now prewarms the local chat, embedding, subagent, and Kokoro runtimes so the first live request is not paying the full cold-start penalty.

If host ports are already occupied, move Elio instead of stopping unrelated services:

- `ELIO_API_PORT` for the API host port
- `ELIO_OLLAMA_PORT` for the loopback Ollama port
- `ELIO_POSTGRES_PORT` for the loopback Postgres port

One-command server rollout:

- set `SERVER`, `ELIO_SERVER_PORT`, and `ELIO_SERVER_PATH` in `.env`
- run `powershell -ExecutionPolicy Bypass -File .\tools\deploy_local_server.ps1 -SyncEnv`
- add `-WithXtts` to deploy the cloned-voice sidecar and sync `voices/xtts`
- add `-SharedHost` to bind Elio to loopback and apply shared-server resource limits

Optional cloned voice:

- add `voices/xtts/<profile>/*.wav`
- run `.\.venv\Scripts\python.exe .\tools\prepare_xtts_voices.py`
- start with `docker compose -f compose.yaml -f compose.xtts.yaml up -d`
- set `ELIO_TTS_PROVIDER=remote`
- map per-user voices in `Data/personality_profiles.json`
- leave `ELIO_TTS_VOICE` unset unless you want to force one global voice for every user

## Recommended Local AI

- Local personality/reasoning: `Qwen3 8B` as the default local assistant model for 8-12 GB GPUs, with `Qwen3 14B` as an optional upgrade on larger boxes.
- Local embeddings: `nomic-embed-text`
- Local vision if needed: `qwen2.5vl:7b`
- Local speech: Kokoro ONNX is the default built-in voice path.

Optional upgrades:

- Use `Mistral Small 3.1` if you want a compact multimodal local model with strong latency on a single RTX 4090-class box.
- Use `XTTS v2` as a separate local TTS service if you want voice cloning rather than the built-in Kokoro voices.

Verification and rollout:

- [Local Stack](docs/LOCAL_STACK.md)
- [Local Server Checklist](docs/LOCAL_SERVER_CHECKLIST.md)

## Why The Private Subagent Exists

The subagent lowers cost and improves latency because Elio no longer spends premium cloud tokens on repetitive JSON work. The main API remains the orchestrator and decision-maker; the subagent stays narrow and internal.

## New Ops Tools

- `tools/run_remote_backup.ps1`
- `tools/server_backup.sh`
- `tools/server_restore.sh`
- `tools/server_ops_snapshot.ps1`
