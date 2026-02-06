import { AppShell } from "@/components/app-shell";
import { RunNowButton } from "@/components/run-now-button";
import { SectionHeader } from "@/components/section-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { WhatsAppConsent } from "@/components/whatsapp-consent";
import { getAdminTemplates, getAuditLog } from "@/lib/data";
import { LiveAdminTemplates } from "@/components/live-admin-templates";
import { LiveAuditLog } from "@/components/live-audit-log";

export default async function AdminPage() {
  const [templates, auditLog] = await Promise.all([
    getAdminTemplates(),
    getAuditLog(),
  ]);

  return (
    <AppShell
      title="Admin Control"
      description="Org settings, WhatsApp templates, cron status, and audit logs."
      actions={<RunNowButton />}
    >
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="glass-panel p-6">
          <SectionHeader title="WhatsApp Templates" description="Utility templates for proactive notifications." />
          <LiveAdminTemplates
            initialTemplates={
              templates.length
                ? templates
                : [
                    { id: "t1", name: "approval_request", status: "approved" },
                    { id: "t2", name: "daily_briefing", status: "approved" },
                    { id: "t3", name: "task_followup", status: "approved" },
                  ]
            }
          />
          <div className="mt-6 flex items-center gap-3">
            <Input placeholder="New template name" />
            <Button className="rounded-full">Add</Button>
          </div>
        </Card>

        <div className="space-y-6">
          <WhatsAppConsent />
          <Card className="glass-card p-5">
            <SectionHeader title="Cron Status" description="Scheduler every 30 minutes." />
            <div className="mt-3 text-sm text-muted-foreground">
              Last run: 30 minutes ago • Next run: in 2 minutes
            </div>
          </Card>
          <Card className="glass-card p-5">
            <SectionHeader title="Audit Log" description="Recent assistant activity." />
            <LiveAuditLog
              initialAudit={
                auditLog.length
                  ? auditLog
                  : [
                      { id: "a1", action: "scheduler.run", actor_user_id: "system" },
                      { id: "a2", action: "whatsapp.send", actor_user_id: "alex" },
                      { id: "a3", action: "approval.update", actor_user_id: "sandra" },
                    ]
              }
            />
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
