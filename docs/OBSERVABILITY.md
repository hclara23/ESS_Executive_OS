# Observability & Monitoring

## Uptime Probes
Use any uptime service (Pingdom, Better Uptime, UptimeRobot, etc.).

### Liveness
- Endpoint: `/api/health`
- Expected: 200 `{ status: "ok" }`
- Interval: 60s
- Timeout: 5s
- Alert after: 2 consecutive failures

### Readiness
- Endpoint: `/api/ready`
- Expected: 200 `{ status: "ready" }`
- Interval: 60s
- Timeout: 5s
- Alert after: 2 consecutive failures

## Suggested Monitoring Targets
1. `/api/health`
2. `/api/ready`
3. `/api/approvals` (optional, auth required)
4. Supabase Edge Functions

## Sentry
Set:
- `SENTRY_DSN`
- `NEXT_PUBLIC_SENTRY_DSN` (optional, for client)

Recommended alerts:
- New issue alert: any new error
- Error rate spike: >2% in 10 minutes
- Transaction latency: P95 > 2s for `/api/ready` or `/api/rag`

## Logs
Capture:
- Edge function errors
- Approval failures
- WhatsApp send failures

## Incident Runbook
1. Check uptime probes.
2. Inspect Sentry issues for error traces.
3. Validate Supabase status and Edge Functions logs.
4. If data integrity risk: disable scheduler immediately.
5. Re-deploy last known good version if needed.
