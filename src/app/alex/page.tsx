import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { mockTasks } from "@/lib/mock-data";
import { getApprovalsForAssistant, getAssistantByPersona, getTasksForAssistant } from "@/lib/data";
import { LivePersonaQueue } from "@/components/live-persona-queue";

export default async function AlexPage() {
  const assistant = await getAssistantByPersona("alex");
  const [tasks, approvals] = await Promise.all([
    getTasksForAssistant(assistant?.id),
    getApprovalsForAssistant(assistant?.id),
  ]);
  const tasksView = tasks.length ? tasks : mockTasks.slice(0, 3);

  return (
    <AppShell
      title="Alex Workspace"
      description="Sales focus: pipeline health, client momentum, and project follow-through."
      actions={<Button className="rounded-full">New Deal Brief</Button>}
    >
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Pipeline (30d)" value="$1.42M" trend="9 active opportunities" />
        <StatCard label="Client Touches" value="18" trend="Last 24 hours" />
        <StatCard label="Open Proposals" value="5" trend="2 in negotiation" />
      </div>

      <Card className="glass-panel p-6">
        <SectionHeader
          title="Focus Queue"
          description="Auto-ranked actions for Alex's sales persona."
        />
        <div className="mt-6">
          <LivePersonaQueue
            persona="alex"
            initialTasks={
              tasksView.map((task) =>
                "due" in task
                  ? { id: task.id, title: task.title, due_at: task.due, priority: task.priority }
                  : task,
              ) as { id: string; title: string; due_at?: string | null; priority: string }[]
            }
            initialApprovals={approvals}
          />
        </div>
      </Card>
    </AppShell>
  );
}
