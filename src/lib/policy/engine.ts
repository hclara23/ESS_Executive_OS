import { randomUUID } from "crypto";
import type { Plan, PlanItem, Signal, RiskLevel } from "@/lib/policy/types";

const riskFromSignal = (signal: Signal): RiskLevel => {
  if (signal.type === "approval_pending") return "confirm";
  if (signal.severity === "high") return "confirm";
  if (signal.severity === "medium") return "suggest";
  return "auto_do";
};

const scoreSignal = (signal: Signal) => {
  const base =
    signal.severity === "high" ? 90 : signal.severity === "medium" ? 60 : 35;
  const typeBoost =
    signal.type === "approval_pending"
      ? 20
      : signal.type === "task_due"
        ? 12
        : signal.type === "calendar_event"
          ? 10
          : signal.type === "kb_update"
            ? 6
            : 4;
  return base + typeBoost;
};

export function generatePlan(signals: Signal[]): Plan {
  const sorted = [...signals].sort((a, b) => scoreSignal(b) - scoreSignal(a));

  const items: PlanItem[] = sorted.map((signal) => ({
    id: randomUUID(),
    title: signal.title,
    domain: signal.domain,
    risk: riskFromSignal(signal),
    rationale:
      signal.type === "approval_pending"
        ? "Approval required before any external action."
        : signal.type === "task_due"
          ? "Task is nearing due date; schedule follow-up."
          : signal.type === "calendar_event"
            ? "Upcoming event needs prep material."
            : signal.type === "kb_update"
              ? "New knowledge added; suggest briefing update."
              : "Inbound message requires triage.",
    actions:
      signal.type === "approval_pending"
        ? ["Prepare decision brief", "Queue approval request"]
        : signal.type === "task_due"
          ? ["Draft reminder", "Confirm blockers"]
          : signal.type === "calendar_event"
            ? ["Draft agenda", "Prepare pre-reads"]
            : signal.type === "kb_update"
              ? ["Update briefing summary"]
              : ["Respond with acknowledgement"],
    relatedSignals: [signal.title],
  }));

  return {
    generatedAt: new Date().toISOString(),
    items,
  };
}

export function enforcePolicy(plan: Plan) {
  return plan.items.map((item) => ({
    ...item,
    requiresApproval: item.risk !== "auto_do",
  }));
}
