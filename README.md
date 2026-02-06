# ESS Executive OS

Production-ready dual-persona executive assistant for Electric Supply Source (ESS). Two personas, strict domain boundaries, RAG knowledge base with citations, approvals, WhatsApp lane, and a 24/7 scheduler with policy enforcement.

## Stack
- Next.js (App Router) + TypeScript
- Tailwind CSS + shadcn/ui
- Framer Motion
- Zustand
- Supabase (Auth + Postgres + Storage + Edge Functions)
- Twilio WhatsApp Business API

## Setup
1. Install dependencies:
```bash
npm install
```

2. Copy env:
```bash
cp .env.example .env.local
```

3. Configure Supabase:
- Create a Supabase project.
- Apply migrations in `supabase/migrations`.
- Run `supabase/seed.sql` after creating your first auth user.
- Create storage bucket `kb-documents` (migration already does this).
 - Set `DEFAULT_ORG_ID` in Edge Functions env for WhatsApp opt-in via START.

4. Deploy Edge Functions:
- `supabase/functions/scheduler-run`
- `supabase/functions/kb-ingest`
- `supabase/functions/whatsapp-webhook`
- `supabase/functions/whatsapp-send-template`

5. Run the app:
```bash
npm run dev
```

## Scheduler
Trigger `scheduler-run` every 30 minutes using:
- GitHub Actions cron
- Cloudflare Cron Trigger
- Supabase scheduled functions (if available)

Use `SCHEDULER_SECRET` and send it as `x-scheduler-secret`.

## WhatsApp
Set:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- `DEFAULT_ORG_ID` (for START opt-ins via webhook)

Inbound webhook:
```
/functions/v1/whatsapp-webhook
```

Outbound templates:
```
/functions/v1/whatsapp-send-template
```

Templates are managed in `jarvis.whatsapp_templates` and linked by name.

## Optional LLM + Embeddings
Set any external LLM/embedding endpoint if you want vector retrieval or LLM planning:
- `OPTIONAL_LLM_API_KEY`
- `OPTIONAL_LLM_EMBEDDING_URL`
- `OPTIONAL_LLM_PLANNER_URL`
- `OPTIONAL_LLM_MODEL`

If unset, the system stays in deterministic mode and uses keyword search.

## Tests
```bash
npm run test
```

## CI
GitHub Actions workflow runs lint and typecheck on push/PR.

## Deployment
### Vercel
1. Import the repo into Vercel.
2. Set environment variables from `.env.example`.
3. Deploy.

### Supabase (CI)
Add repository secrets:
- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_PROJECT_ID`
- `SUPABASE_DB_PASSWORD`

The workflow in `.github/workflows/supabase-deploy.yml` applies migrations and deploys Edge Functions on push to `main`.

## Observability
Sentry is pre-wired for client, server, and edge. Set:
- `SENTRY_DSN`
- `NEXT_PUBLIC_SENTRY_DSN` (optional)

## Health Checks
- `/api/health` for liveness
- `/api/ready` for readiness

## Key Routes
- `/` Command Center
- `/alex` Alex workspace
- `/sandra` Sandra workspace
- `/chat` Chat with persona switch
- `/briefing` Morning briefing
- `/night` Night shift log
- `/tasks` Tasks
- `/approvals` Approvals queue
- `/kb` Knowledge base
- `/memory` Memory manager
- `/settings` Persona settings
- `/admin` Admin controls

## Security Notes
- All secrets remain server-side.
- RLS is enabled for all tables.
- Approvals and WhatsApp consent are owner/admin-only.
- Audit log captures assistant runs and outbound messaging.
