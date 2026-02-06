export type ApprovalStatus = "pending" | "approved" | "rejected" | "canceled";

export type Approval = {
  id: string;
  status: ApprovalStatus;
  risk: "low" | "medium" | "high";
  proposedAction: string;
  result?: string | null;
};

export function transitionApproval(
  approval: Approval,
  nextStatus: ApprovalStatus,
): Approval {
  if (approval.status !== "pending") {
    throw new Error("Only pending approvals can be updated.");
  }
  if (nextStatus === "pending") {
    throw new Error("Cannot revert approval back to pending.");
  }
  return {
    ...approval,
    status: nextStatus,
    result:
      nextStatus === "approved"
        ? "Approved for execution."
        : nextStatus === "rejected"
          ? "Rejected by approver."
          : "Canceled by system.",
  };
}
