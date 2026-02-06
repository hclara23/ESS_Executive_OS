import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { mockApprovals } from "@/lib/mock-data";
import { getApprovals } from "@/lib/data";
import { LiveApprovals, type LiveApprovalSeed } from "@/components/live-approvals";

export default async function ApprovalsPage() {
  const approvals = await getApprovals();
  const approvalsView = approvals.length ? approvals : mockApprovals;

  return (
    <AppShell
      title="Approvals"
      description="Human-in-the-loop control for any high-risk or external actions."
      actions={<Button className="rounded-full">Policy Settings</Button>}
    >
      <Card className="glass-panel p-6">
        <SectionHeader title="Pending Approvals" description="Owner/admin required." />
        <LiveApprovals initialApprovals={approvalsView as LiveApprovalSeed[]} />
      </Card>
    </AppShell>
  );
}
