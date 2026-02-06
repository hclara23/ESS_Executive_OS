"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { ApprovalActions } from "@/components/approval-actions";

type Approval = {
  id: string;
  proposed_action: string;
  risk: string;
  status: string;
  requested_by?: string | null;
};

type LegacyApproval = {
  id: string;
  title: string;
  risk: string;
  requestedBy?: string;
};

export type LiveApprovalSeed = Approval | LegacyApproval;

type Props = {
  initialApprovals: LiveApprovalSeed[];
  intervalMs?: number;
};

export function LiveApprovals({ initialApprovals, intervalMs = 30000 }: Props) {
  const [approvals, setApprovals] = React.useState<Approval[]>(
    initialApprovals.map((item) =>
      "proposed_action" in item
        ? item
        : {
            id: item.id,
            proposed_action: item.title,
            risk: item.risk,
            status: "pending",
            requested_by: item.requestedBy,
          },
    ),
  );

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const response = await fetch("/api/approvals", { cache: "no-store" });
      const data = await response.json();
      if (active && Array.isArray(data.approvals)) {
        setApprovals(data.approvals);
      }
    };
    const id = setInterval(load, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  if (approvals.length === 0) {
    return <div className="text-sm text-muted-foreground">No approvals pending.</div>;
  }

  return (
    <div className="mt-6 space-y-4">
      {approvals.map((approval) => (
        <div key={approval.id} className="glass-card p-4 text-sm">
          <div className="flex items-center justify-between">
            <div className="font-semibold">{approval.proposed_action}</div>
            <Badge variant="outline">{approval.risk}</Badge>
          </div>
          <div className="mt-2 text-muted-foreground">
            Requested by {approval.requested_by ?? "System"}
          </div>
          <ApprovalActions approvalId={approval.id} />
        </div>
      ))}
    </div>
  );
}
