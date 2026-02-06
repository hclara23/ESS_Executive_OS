import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getApprovalsForAssistant, getAssistantByPersona, getTasksForAssistant } from "@/lib/data";
import { LivePersonaQueue } from "@/components/live-persona-queue";

export default async function SandraPage() {
  const assistant = await getAssistantByPersona("sandra");
  const [tasks, approvals] = await Promise.all([
    getTasksForAssistant(assistant?.id),
    getApprovalsForAssistant(assistant?.id),
  ]);

  return (
    <AppShell
      title="Sandra Workspace"
      description="Admin, finance, HR, and employee operations. Clear, compliant, and calm."
      actions={<Button className="rounded-full">New HR Draft</Button>}
    >
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Payroll Review" value="2 items" trend="Pending approval" />
        <StatCard label="HR Requests" value="7" trend="3 urgent" />
        <StatCard label="Finance Flags" value="4" trend="Month-end close" />
      </div>

      <Card className="glass-panel p-6">
        <SectionHeader
          title="Admin Priorities"
          description="High-trust actions awaiting verification."
        />
        <div className="mt-6">
          <LivePersonaQueue
            persona="sandra"
            initialTasks={tasks}
            initialApprovals={approvals}
          />
        </div>
      </Card>
    </AppShell>
  );
}
