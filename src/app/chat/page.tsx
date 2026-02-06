import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function ChatPage() {
  return (
    <AppShell
      title="Chat"
      description="Directly collaborate with the active persona. Conversations honor domain boundaries."
    >
      <Card className="glass-panel p-6">
        <SectionHeader
          title="Conversation"
          description="Context-aware, policy-checked, and cite-backed responses."
          action={<Button className="rounded-full">New Thread</Button>}
        />
        <div className="mt-6 space-y-4">
          <div className="glass-card p-4 text-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Alex • Work
            </div>
            <p className="mt-2">
              I reviewed the Northstar renewal notes. Two blockers remain: delivery
              schedule and warranty terms. Do you want a draft response?
            </p>
          </div>
          <div className="glass-card p-4 text-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              You • Work
            </div>
            <p className="mt-2">
              Draft response and highlight the schedule risks. Keep it concise.
            </p>
          </div>
          <div className="glass-card p-4 text-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Alex • Draft
            </div>
            <p className="mt-2 text-muted-foreground">
              Draft prepared. Requires approval before sending external email.
            </p>
          </div>
        </div>
        <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-border/60 bg-background/60 p-4">
          <Textarea placeholder="Ask Alex or Sandra anything..." rows={4} />
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              External actions require approval.
            </div>
            <Button className="rounded-full">Send</Button>
          </div>
        </div>
      </Card>
    </AppShell>
  );
}
