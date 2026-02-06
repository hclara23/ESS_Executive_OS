"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";

type Props = {
  approvalId: string;
};

export function ApprovalActions({ approvalId }: Props) {
  const [status, setStatus] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const update = async (next: "approved" | "rejected") => {
    setLoading(true);
    setStatus(null);
    const response = await fetch(`/api/approvals/${approvalId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: next }),
    });
    const data = await response.json();
    setStatus(data.ok ? `Marked ${next}.` : data.error ?? "Update failed.");
    setLoading(false);
  };

  return (
    <div className="mt-4 flex flex-col gap-2">
      <div className="flex gap-2">
        <Button
          className="rounded-full"
          size="sm"
          onClick={() => update("approved")}
          disabled={loading}
        >
          Approve
        </Button>
        <Button
          variant="secondary"
          className="rounded-full"
          size="sm"
          onClick={() => update("rejected")}
          disabled={loading}
        >
          Reject
        </Button>
      </div>
      {status && <div className="text-xs text-muted-foreground">{status}</div>}
    </div>
  );
}
