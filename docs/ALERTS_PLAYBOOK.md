# Alerts Playbook

## Sentry Alerts (Recommended)
1. **New Issue**
   - Trigger: Any new issue in production
   - Action: Triage within 1 hour
2. **Error Rate Spike**
   - Trigger: >2% error rate within 10 minutes
   - Action: Check recent deploys + rollback if needed
3. **API Latency**
   - Trigger: P95 > 2s for `/api/ready` or `/api/rag` (10 min window)
   - Action: Review DB load + edge function logs
4. **Approval Failures**
   - Trigger: Error in `approval.update` or approvals API
   - Action: Notify owner/admin immediately
5. **WhatsApp Failures**
   - Trigger: `whatsapp.send` failures
   - Action: Verify Twilio templates + consent status

## Escalation Matrix
- **P1 (Service down):** Immediate escalation to owner/admin
- **P2 (Critical feature broken):** Fix within 4 hours
- **P3 (Degraded performance):** Fix within 24 hours

## Rollback Procedure
1. Revert Vercel deployment to last known good.
2. Disable scheduler (`scheduler-run`) temporarily.
3. Confirm error rate returns to baseline.

## Verification Checklist
- `/api/health` returns 200
- `/api/ready` returns 200
- Approvals flow OK
- WhatsApp send + webhook OK
