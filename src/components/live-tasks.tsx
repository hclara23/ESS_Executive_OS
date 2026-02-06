"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";

type Task = {
  id: string;
  title: string;
  due_at?: string | null;
  priority: string;
  owner_user_id?: string | null;
};

type LegacyTask = {
  id: string;
  title: string;
  due: string;
  priority: string;
  owner?: string;
};

type Props = {
  initialTasks: LiveTaskSeed[];
  intervalMs?: number;
};

export type LiveTaskSeed = Task | LegacyTask;

export function LiveTasks({ initialTasks, intervalMs = 30000 }: Props) {
  const [tasks, setTasks] = React.useState<Task[]>(
    initialTasks.map((task) => {
      if ("due" in task) {
        return {
          id: task.id,
          title: task.title,
          due_at: task.due,
          priority: task.priority,
          owner_user_id: task.owner,
        };
      }
      return task;
    }),
  );

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const response = await fetch("/api/tasks", { cache: "no-store" });
      const data = await response.json();
      if (active && Array.isArray(data.tasks)) {
        setTasks(data.tasks);
      }
    };
    const id = setInterval(load, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  if (tasks.length === 0) {
    return <div className="text-sm text-muted-foreground">No tasks found.</div>;
  }

  return (
    <div className="mt-6 space-y-4">
      {tasks.map((task) => (
        <div key={task.id} className="glass-card flex items-center justify-between p-4">
          <div>
            <div className="text-sm font-semibold">{task.title}</div>
            <div className="text-xs text-muted-foreground">
              Owner: {task.owner_user_id ?? "Unassigned"} • Due{" "}
              {task.due_at ?? "TBD"}
            </div>
          </div>
          <Badge variant="secondary">{task.priority}</Badge>
        </div>
      ))}
    </div>
  );
}
