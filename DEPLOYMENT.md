# Deployment Guide

## 1. Preferred Topology

Elio is now designed to run best on a private local server with this service layout:

- `api` on container port `8000`, exposed on host port `ELIO_API_PORT` (`8000` by default)
- `subagent` on port `8010` internally only
- `ollama` on port `11434` loopback only by default, or private-LAN bound only when a separate control-plane host must reach it
- `postgres` on port `5432` loopback only
- `xtts` on port `8020` loopback only by default when the cloned-voice overlay is enabled

If you still want a hosted frontend, the browser should talk only to the API. Do not expose the subagent, Ollama, or Postgres publicly.

## 2. Local Server Deployment

### Step 1: Prepare Environment

1. Copy `.env.example` to `.env`
2. Set:
   - `ELIO_API_PORT` if `8000` is already taken on the host
   - `ELIO_OLLAMA_BIND_IP` if Ollama must be reachable from a private control-plane host
   - `ELIO_OLLAMA_PORT` if `11434` is already taken on the host
   - `ELIO_POSTGRES_PORT` if `5432` is already taken on the host
   - `ELIO_JWT_SECRET`
   - `ELIO_PG_URI`
   - `ELIO_SUBAGENT_TOKEN`
   - `OPENAI_API_KEY` if you want hybrid/cloud escalation
3. Choose your mode:
   - `ELIO_LLM_MODE=hybrid` for local-first with cloud escalation
   - `ELIO_LLM_MODE=local` for fully local operation

### Step 2: Start Services

```powershell
docker compose up -d
```

If this host is the control plane and local models live on a different private node, start with the external-models override so Compose does not try to run a local Ollama service:

```powershell
docker compose -f compose.yaml -f compose.shared-host.yaml -f compose.external-models.yaml up -d
```

### Step 2A: Deploy straight to the local server

If you have SSH-key access configured:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\deploy_local_server.ps1 -SyncEnv
```

That path renders a sanitized server `.env` before upload and excludes workstation-only keys like `SERVER`, `SERVER_PASSWORD`, `ELIO_SERVER_PORT`, and `ELIO_SERVER_PATH`.

Optional flags:

- `-WithXtts`
- `-SharedHost`
- `-ApiPort <port>`
- `-OllamaPort <port>`
- `-PostgresPort <port>`
- `-SkipModelBootstrap`
- `-SkipSeed`
- `-SkipPrewarm`
- `-SyncVoices`

For cloned voice support:

```powershell
docker compose -f compose.yaml -f compose.xtts.yaml up -d
```

If XTTS must be reachable from a separate private control-plane host, bind it to the GPU node's private LAN IP with:

```text
ELIO_XTTS_BIND_IP=<private-lan-ip>
ELIO_XTTS_PORT=8020
```

### Step 3: Pull Recommended Local Models

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\bootstrap_local_models.ps1
```

That script pulls:

- `qwen3:8b`
- `nomic-embed-text`
- `qwen2.5vl:7b`

Add `-IncludeLargeChatModel` only if the server has enough GPU memory for `qwen3:14b`.

After startup, the bootstrap path also runs `tools/prewarm_local_stack.py` inside the API container unless `-SkipPrewarm` is set.

### Step 4: Verify Runtime

```text
GET http://localhost:<ELIO_API_PORT>/system/runtime
GET http://localhost:<ELIO_API_PORT>/docs
```

### Step 5: Backups and Ops

Create a remote backup:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_remote_backup.ps1 -Download
```

Collect a server snapshot:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\server_ops_snapshot.ps1
```

## 3. Voice Deployment

### Default

Elio ships with Kokoro ONNX in the main container. Set:

```text
ELIO_TTS_PROVIDER=kokoro
```

### Optional cloned voice

The repo now includes an optional XTTS sidecar. To use it:

1. Place reference WAV files under `voices/xtts/<profile>/`
2. Prepare normalized XTTS refs:

```powershell
.\.venv\Scripts\python.exe .\tools\prepare_xtts_voices.py
```

3. Start the stack with `compose.xtts.yaml`
4. Set:

```text
ELIO_TTS_PROVIDER=remote
ELIO_REMOTE_TTS_URL=http://xtts:8020/synthesize
```

Per-user cloned voices are selected from `Data/personality_profiles.json` user overrides. Leave `ELIO_TTS_VOICE` unset for the normal multi-user setup. Only set it if you intentionally want one global forced voice for every user.

If the server has a supported GPU, set `ELIO_XTTS_USE_GPU=true`. Otherwise leave it on CPU and expect slower generation.

## 4. Hosted Frontend

The frontend is currently deployed to Firebase Hosting, project `elioos`:

- **Live URL:** [elioos.web.app](https://elioos.web.app)
- **Deploy:** `firebase deploy --only hosting --project elioos`
- **Target domain (post-cutover):** [app.electricsupplysource.co](https://app.electricsupplysource.co)

If hosting separately, set `ELIO_ALLOWED_ORIGINS` to the frontend origin, point the frontend at the API only, and keep `subagent`, `ollama`, and `postgres` private.

## 5. Cloud Run

Cloud Run is still viable for the API, but the new local-first design means the best cost profile comes from running the API, subagent, and local model server together on your own box.

If you deploy the API remotely:

- keep `ELIO_ROUTE_BRAIN=cloud` if low latency to OpenAI matters
- use a private local Ollama/vLLM node only if the API can reach it securely over VPN or a private tunnel

## 6. Database

You can keep using Neon or move fully local.

### Neon

- keep `ELIO_PG_URI` pointed at Neon
- ensure `pgvector` is enabled if knowledge search is in use

### Local Postgres

Use the compose `postgres` service and set:

```text
ELIO_PG_URI=postgresql://elio:elio@postgres:5432/elio
```

## 7. Operational Rules

- expose only `ELIO_API_PORT` unless you have a very specific reason not to
- if `8000` is occupied, move Elio with `ELIO_API_PORT` rather than stopping unrelated services blindly
- keep `5432` loopback-bound
- keep `11434` loopback-bound unless a separate private control-plane host must reach it
- never expose `8010` publicly
- never bind `11434` or `8020` to a public interface; if you need cross-node access, bind only to the GPU host's private LAN IP
- use SSH keys for the server; do not keep plaintext server passwords in `.env`
- keep `.env` local and uncommitted
- prefer `compose.shared-host.yaml` when the box is shared with other applications

## 8. Multi-User Email Setup

V4.0 introduces a Unified Message Center. To enable this for multiple users:

1. **System Email (ELIO):** Set the following environment variables in your `.env`:
   - `ELIO_MAIL_ADDRESS`: elio@electricsupplysource.co
   - `ELIO_MAIL_PASSWORD`: (HostGator password)
   - `ELIO_MAIL_SMTP_SERVER`: (mail.electricsupplysource.co)
   - `ELIO_MAIL_SMTP_PORT`: 465
   - `ELIO_MAIL_IMAP_SERVER`: (mail.electricsupplysource.co)
   - `ELIO_MAIL_IMAP_PORT`: 993

2. **User Emails (GoDaddy):** Users should add their GoDaddy credentials to the `elio_email_config` table. You can use a direct SQL insert or wait for the upcoming Settings UI:
   ```sql
   INSERT INTO elio_email_config (user_profile_id, email, password, smtp_server, smtp_port, imap_server, imap_port)
   VALUES ('user-uuid', 'Alexsanchez@electricsupplysource.com', '...', 'smtpout.secureserver.net', 465, 'imap.secureserver.net', 993);
   ```

3. **Triage Persistence:** Ensure the `elio_email_triage` table exists (created automatically by `server.store` on first run) to track processed messages.
