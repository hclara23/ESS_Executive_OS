import type { Domain } from "@/lib/constants";

export type RiskLevel = "auto_do" | "suggest" | "confirm";

export type Signal = {
  type: "task_due" | "approval_pending" | "kb_update" | "calendar_event" | "message_inbound";
  title: string;
  domain: Domain;
  severity: "low" | "medium" | "high";
  metadata?: Record<string, unknown>;
};

export type PlanItem = {
  id: string;
  title: string;
  domain: Domain;
  risk: RiskLevel;
  rationale: string;
  actions: string[];
  relatedSignals: string[];
};

export type Plan = {
  generatedAt: string;
  items: PlanItem[];
};
