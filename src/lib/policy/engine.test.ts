import { describe, expect, it } from "vitest";
import { generatePlan, enforcePolicy } from "@/lib/policy/engine";
import type { Signal } from "@/lib/policy/types";

describe("policy engine", () => {
  it("generates ranked plan items with risk tags", () => {
    const signals: Signal[] = [
      {
        type: "task_due",
        title: "2 tasks due",
        domain: "WORK",
        severity: "medium",
      },
      {
        type: "approval_pending",
        title: "1 approval pending",
        domain: "WORK",
        severity: "high",
      },
    ];

    const plan = generatePlan(signals);
    expect(plan.items.length).toBe(2);
    expect(plan.items[0].risk).toBe("confirm");
  });

  it("flags non-auto actions for approval", () => {
    const plan = generatePlan([
      {
        type: "task_due",
        title: "Task",
        domain: "WORK",
        severity: "medium",
      },
    ]);
    const enforced = enforcePolicy(plan);
    expect(enforced[0].requiresApproval).toBe(true);
  });
});
