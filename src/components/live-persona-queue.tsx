"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";

type Task = {
  id: string;
  title: string;
  due_at?: string | null;
  priority: string;
};

type Approval = {
  id: string;
  proposed_action: string;
  risk: string;
  status: string;
};

type Props = {
  persona: "alex" | "sandra";
  initialTasks: Task[];
  initialApprovals: Approval[];
  intervalMs?: number;
};

export function LivePersonaQueue({
  persona,
  initialTasks,
  initialApprovals,
  intervalMs = 30000,
}: Props) {
  const [tasks, setTasks] = React.useState<Task[]>(initialTasks);
  const [approvals, setApprovals] = React.useState<Approval[]>(initialApprovals);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const response = await fetch(`/api/assistant/${persona}`, { cache: "no-store" });
      const data = await response.json();
      if (active) {
        if (Array.isArray(data.tasks)) setTasks(data.tasks);
        if (Array.isArray(data.approvals)) setApprovals(data.approvals);
      }
    };
    const id = setInterval(load, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs, persona]);

  return (
    <div className="mt-6 space-y-4">
      {tasks.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-2">
          {tasks.map((task) => (
            <div key={task.id} className="glass-card p-4 text-sm">
              <div className="font-semibold">{task.title}</div>
              <div className="mt-2 text-xs text-muted-foreground">
                Due {task.due_at ?? "TBD"} • Priority {task.priority}
              </div>
            </div>
          ))}
        </div>
      )}
      {approvals.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-2">
          {approvals.map((approval) => (
            <div key={approval.id} className="glass-card p-4 text-sm">
              <div className="flex items-center justify-between">
                <div className="font-semibold">{approval.proposed_action}</div>
                <Badge variant="outline">{approval.risk}</Badge>
              </div>
              <div className="mt-2 text-xs text-muted-foreground">Approval required</div>
            </div>
          ))}
        </div>
      )}
      {tasks.length === 0 && approvals.length === 0 && (
        <div className="text-sm text-muted-foreground">No queued items.</div>
      )}
    </div>
  );
}
