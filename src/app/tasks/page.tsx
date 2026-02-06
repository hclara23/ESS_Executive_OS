import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { mockTasks } from "@/lib/mock-data";
import { getTasks } from "@/lib/data";
import { LiveTasks, type LiveTaskSeed } from "@/components/live-tasks";

export default async function TasksPage() {
  const tasks = await getTasks();
  const tasksView = tasks.length ? tasks : mockTasks;

  return (
    <AppShell
      title="Tasks"
      description="Cross-persona task management with work/personal separation."
      actions={<Button className="rounded-full">New Task</Button>}
    >
      <Card className="glass-panel p-6">
        <SectionHeader title="Active Tasks" description="Priority sorted." />
        <LiveTasks initialTasks={tasksView as LiveTaskSeed[]} />
      </Card>
    </AppShell>
  );
}
