import { describe, expect, it } from "vitest";
import { transitionApproval } from "@/lib/approvals/logic";

describe("approval transitions", () => {
  it("allows approval from pending", () => {
    const approval = {
      id: "a1",
      status: "pending",
      risk: "medium",
      proposedAction: "Send proposal",
    } as const;
    const updated = transitionApproval(approval, "approved");
    expect(updated.status).toBe("approved");
  });

  it("rejects updates from non-pending", () => {
    const approval = {
      id: "a1",
      status: "approved",
      risk: "medium",
      proposedAction: "Send proposal",
    } as const;
    expect(() => transitionApproval(approval, "rejected")).toThrow();
  });
});
