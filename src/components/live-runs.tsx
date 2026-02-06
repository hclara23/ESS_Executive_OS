"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";

type Run = {
  id: string;
  created_at: string;
  summary?: string | null;
};

type Props = {
  initialRuns: Run[];
  intervalMs?: number;
};

export function LiveRuns({ initialRuns, intervalMs = 60000 }: Props) {
  const [runs, setRuns] = React.useState<Run[]>(initialRuns);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const response = await fetch("/api/runs", { cache: "no-store" });
      const data = await response.json();
      if (active && Array.isArray(data.runs)) {
        setRuns(data.runs);
      }
    };
    const id = setInterval(load, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  if (runs.length === 0) {
    return <div className="text-sm text-muted-foreground">No runs recorded yet.</div>;
  }

  return (
    <div className="mt-6 space-y-4">
      {runs.map((run) => (
        <div key={run.id} className="glass-card p-4 text-sm">
          <div className="flex items-center justify-between">
            <div className="font-semibold">
              Scheduler Run •{" "}
              {new Date(run.created_at).toLocaleTimeString("en-US", {
                hour: "numeric",
                minute: "2-digit",
              })}
            </div>
            <Badge variant="outline">Completed</Badge>
          </div>
          <div className="mt-2 text-muted-foreground">
            {run.summary ?? "Scheduler completed."}
          </div>
        </div>
      ))}
    </div>
  );
}
