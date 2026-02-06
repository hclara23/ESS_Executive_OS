"use client";

import * as React from "react";
import { Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

export function RunNowButton() {
  const [isRunning, setIsRunning] = React.useState(false);
  const [status, setStatus] = React.useState<string | null>(null);

  const handleRun = async () => {
    setIsRunning(true);
    setStatus(null);
    try {
      const supabase = getSupabaseBrowserClient();
      if (!supabase) {
        setStatus("Supabase not configured.");
        return;
      }
      const { data, error } = await supabase.functions.invoke("scheduler-run", {
        body: { trigger: "manual" },
      });
      if (error) {
        setStatus(error.message);
      } else {
        setStatus(data?.status ?? "Run started");
      }
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Unable to run scheduler.");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-2">
      <Button onClick={handleRun} disabled={isRunning} className="rounded-full">
        {isRunning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
        Run Now
      </Button>
      {status && <div className="text-xs text-muted-foreground">{status}</div>}
    </div>
  );
}
