import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { mockBriefing } from "@/lib/mock-data";
import { getMorningBriefing } from "@/lib/data";
import { LiveBriefing } from "@/components/live-briefing";

export default async function BriefingPage() {
  const briefing = await getMorningBriefing();
  const briefingView =
    briefing?.content && typeof briefing.content === "object"
      ? (briefing.content as typeof mockBriefing)
      : mockBriefing;

  return (
    <AppShell
      title="Morning Briefing"
      description="Daily executive summary per persona, refreshed automatically."
      actions={<Button className="rounded-full">Generate Briefing</Button>}
    >
      <Card className="glass-panel p-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="secondary">Alex • Work</Badge>
          <Badge variant="outline">Org Shared</Badge>
          <Badge variant="outline">Generated 8:02 AM</Badge>
        </div>
        <LiveBriefing
          initialBriefing={briefing}
          render={(content) => {
            const schedule = content.schedule ?? briefingView.schedule;
            const priorities = content.priorities ?? briefingView.priorities;
            const opportunities = content.opportunities ?? briefingView.opportunities;
            return (
              <div className="mt-6 grid gap-6 lg:grid-cols-3">
                <div className="glass-card p-5">
                  <SectionHeader title="Schedule" />
                  <ul className="mt-3 space-y-2 text-sm">
                    {schedule.map((item) => (
                      <li key={item.time} className="flex items-center justify-between">
                        <span>{item.title}</span>
                        <span className="text-muted-foreground">{item.time}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="glass-card p-5">
                  <SectionHeader title="Priorities" />
                  <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                    {priorities.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="glass-card p-5">
                  <SectionHeader title="Radar" />
                  <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                    {opportunities.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          }}
        />
      </Card>
    </AppShell>
  );
}
