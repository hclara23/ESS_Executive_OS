import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function MemoryPage() {
  return (
    <AppShell
      title="Memory Manager"
      description="Governed long-term memory. Review, edit, delete, or export facts and episodes."
      actions={<Button className="rounded-full">Export Memory</Button>}
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-panel p-6">
          <SectionHeader title="Structured Facts" description="High-confidence facts." />
          <div className="mt-6 space-y-4">
            {["Primary warehouse lead time is 12 days.", "Northstar prefers Friday check-ins."].map(
              (fact) => (
                <div key={fact} className="glass-card p-4 text-sm">
                  <div className="font-semibold">Fact</div>
                  <div className="mt-2 text-muted-foreground">{fact}</div>
                  <div className="mt-4 flex gap-2">
                    <Button size="sm" className="rounded-full">
                      Edit
                    </Button>
                    <Button size="sm" variant="secondary" className="rounded-full">
                      Delete
                    </Button>
                  </div>
                </div>
              ),
            )}
          </div>
        </Card>
        <Card className="glass-panel p-6">
          <SectionHeader title="Lessons Learned" description="Append-only insights." />
          <div className="mt-6 space-y-4">
            {[
              "When a vendor misses SLA twice, prioritize backup sourcing within 72 hours.",
              "Clients respond faster to visual schedules in briefings.",
            ].map((lesson) => (
              <div key={lesson} className="glass-card p-4 text-sm text-muted-foreground">
                {lesson}
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button className="rounded-full">Add Lesson</Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
