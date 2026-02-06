import { AppShell } from "@/components/app-shell";
import { RunNowButton } from "@/components/run-now-button";
import { SectionHeader } from "@/components/section-header";
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { mockApprovals, mockBriefing, mockTasks } from "@/lib/mock-data";
import { getApprovals, getMorningBriefing, getTasks } from "@/lib/data";
import { LiveApprovals, type LiveApprovalSeed } from "@/components/live-approvals";
import { LiveTasks, type LiveTaskSeed } from "@/components/live-tasks";
import { LiveBriefing } from "@/components/live-briefing";

export default async function HomePage() {
  const [approvals, tasks, briefing] = await Promise.all([
    getApprovals(),
    getTasks(),
    getMorningBriefing(),
  ]);
  const approvalsView = approvals.length ? approvals : mockApprovals;
  const tasksView = tasks.length ? tasks : mockTasks;
  const briefingView =
    briefing?.content && typeof briefing.content === "object"
      ? (briefing.content as typeof mockBriefing)
      : mockBriefing;

  return (
    <AppShell
      title="Command Center"
      description="A calm, high-fidelity overview of ESS executive operations. Switch personas, triage approvals, and review system planning in one place."
      actions={<RunNowButton />}
    >
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Active Approvals"
          value={`${approvalsView.length}`}
          trend="Owner/admin approval required"
        />
        <StatCard
          label="Tasks Due (48h)"
          value={`${tasksView.length}`}
          trend="Prioritized by due date"
        />
        <StatCard
          label="Unread Briefings"
          value={briefing ? "1" : "0"}
          trend="Latest generated within 24h"
        />
      </div>

      <Card className="glass-panel p-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <SectionHeader
              title="Morning Brief"
              description="Auto-summarized priorities and opportunities for today."
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Work</Badge>
            <Badge variant="outline">Org Shared</Badge>
          </div>
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
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Schedule
                  </div>
                  <ul className="mt-4 space-y-3 text-sm">
                    {schedule.map((item) => (
                      <li key={item.time} className="flex items-center justify-between">
                        <span className="font-medium">{item.title}</span>
                        <span className="text-muted-foreground">{item.time}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="glass-card p-5">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Top Priorities
                  </div>
                  <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                    {priorities.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="glass-card p-5">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Opportunities
                  </div>
                  <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
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

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-panel p-6">
          <SectionHeader
            title="Approvals Queue"
            description="Actions awaiting human confirmation."
            action={<Button className="rounded-full">Review All</Button>}
          />
          <LiveApprovals initialApprovals={approvalsView as LiveApprovalSeed[]} />
        </Card>

        <Card className="glass-panel p-6">
          <SectionHeader
            title="Critical Tasks"
            description="High impact tasks across both personas."
            action={<Button variant="secondary" className="rounded-full">Open Tasks</Button>}
          />
          <LiveTasks initialTasks={tasksView as LiveTaskSeed[]} />
        </Card>
      </div>
    </AppShell>
  );
}
