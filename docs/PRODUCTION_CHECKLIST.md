# Production Checklist (Go-Live)

## Ownership
- **Owner/Admin:** ESS leadership
- **Engineering:** Deployment + Supabase config
- **Ops:** Monitoring + alert response

## Pre-Launch
1. Supabase project created
2. Migrations applied
3. Seed data executed
4. Storage bucket verified
5. RLS policies validated in Supabase
6. Edge Functions deployed
7. Scheduler configured (30 min)
8. WhatsApp sender verified + templates approved
9. Environment variables set in Vercel + Supabase
10. Sentry DSN configured

## Security
1. Secrets confirmed server-only
2. Service role key not exposed in client
3. Org-based access verified
4. Approval flow enforced for high-risk actions
5. WhatsApp consent & STOP handling validated

## QA
1. Auth + login flow
2. Persona switch (admin only)
3. Domain separation (WORK/PERSONAL)
4. KB upload + retrieval + citations
5. Approvals flow + audit log
6. Scheduler run + briefings
7. WhatsApp inbound/outbound

## Monitoring
1. Uptime probes configured (`/api/health`, `/api/ready`)
2. Sentry alerts enabled
3. Logs accessible (Supabase + Vercel)

## Launch
1. Deploy to production
2. Verify readiness endpoint
3. Notify stakeholders

## Post-Launch
1. Monitor error rate + latency
2. Review audit log daily (first week)
3. Validate scheduler runs every 30 minutes
4. Check WhatsApp delivery reports
