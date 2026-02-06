# ESS Executive OS Deployment Runbook

## Pre-flight
1. Ensure Supabase project is created.
2. Confirm `.env.local` values are available for local testing.
3. Make sure `SUPABASE_SERVICE_ROLE_KEY` is never used client-side.

## Supabase Setup
1. Apply migrations:
   - Run `supabase db push` or apply SQL files in `supabase/migrations/`.
2. Create initial auth user in Supabase.
3. Run seed:
   - Execute `supabase/seed.sql` to create org + assistants.
4. Verify storage bucket:
   - `kb-documents` exists and is not public.
5. Set Edge Function secrets in Supabase:
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_FROM`
   - `SCHEDULER_SECRET`
   - `DEFAULT_ORG_ID`
   - Optional LLM vars

## Edge Functions
Deploy:
- `scheduler-run`
- `kb-ingest`
- `whatsapp-webhook`
- `whatsapp-send-template`

Validate:
- `/functions/v1/scheduler-run` returns `ok` with `x-scheduler-secret`.
- `/functions/v1/kb-ingest` accepts authenticated upload.
- `/functions/v1/whatsapp-webhook` receives inbound messages.

## Vercel
1. Import the repo in Vercel.
2. Configure env vars from `.env.example`.
3. Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
4. Deploy and verify `/api/health` and `/api/ready`.

## Twilio WhatsApp
1. Verify WhatsApp Business sender.
2. Configure webhook:
   - `https://<app-domain>/functions/v1/whatsapp-webhook`
3. Add approved templates in Twilio and record SIDs in `jarvis.whatsapp_templates`.
4. Test opt-in using `START` and opt-out using `STOP`.

## Scheduler
1. Configure cron (GitHub Actions, Cloudflare, or Supabase scheduled function).
2. Call `scheduler-run` every 30 minutes with `x-scheduler-secret`.

## Post-deploy Validation
1. Log in with owner/admin account.
2. Confirm RLS rules restrict cross-org data.
3. Upload KB document and test retrieval with citations.
4. Queue an approval and approve via UI and WhatsApp.
5. Check audit log entries.

## Rollback
1. Revert to previous Vercel deployment.
2. Roll back migrations if necessary with `supabase db reset` (staging only).
3. Disable scheduler while investigating.
