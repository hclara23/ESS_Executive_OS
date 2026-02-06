import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getRuns } from "@/lib/data";
import { LiveRuns } from "@/components/live-runs";

export default async function NightPage() {
  const runs = await getRuns();
  const viewRuns =
    runs.length > 0
      ? runs
      : [
          {
            id: "run-1",
            created_at: new Date().toISOString(),
            summary: "Generated 4 plans.",
          },
          {
            id: "run-2",
            created_at: new Date().toISOString(),
            summary: "Queued 2 approvals.",
          },
          {
            id: "run-3",
            created_at: new Date().toISOString(),
            summary: "Updated memory episodes.",
          },
        ];

  return (
    <AppShell
      title="Night Shift Log"
      description="Every scheduler run, plan draft, and queued approval is recorded here."
      actions={<Button className="rounded-full">Export Log</Button>}
    >
      <Card className="glass-panel p-6">
        <SectionHeader title="Latest Runs" description="Auto-generated every 30 minutes." />
        <LiveRuns initialRuns={viewRuns} />
      </Card>
    </AppShell>
  );
}
