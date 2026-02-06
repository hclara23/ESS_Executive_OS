import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { corsHeaders } from "../_shared/cors.ts";
import { getServiceClient } from "../_shared/supabase.ts";

type Signal = {
  type: string;
  title: string;
  severity: "low" | "medium" | "high";
};

const makePlan = (signals: Signal[]) => {
  return signals.map((signal, index) => ({
    id: crypto.randomUUID(),
    rank: index + 1,
    title: signal.title,
    risk:
      signal.type === "approval_pending" || signal.severity === "high"
        ? "confirm"
        : signal.severity === "medium"
          ? "suggest"
          : "auto_do",
    rationale: signal.type === "task_due" ? "Task due soon." : "Operational signal.",
  }));
};

const fetchPlanFromLLM = async (signals: Signal[]) => {
  const endpoint = Deno.env.get("OPTIONAL_LLM_PLANNER_URL");
  if (!endpoint) return null;
  const apiKey = Deno.env.get("OPTIONAL_LLM_API_KEY");
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify({ signals }),
  });
  if (!response.ok) return null;
  const data = await response.json();
  if (Array.isArray(data?.items)) {
    return data.items;
  }
  return null;
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const secret = Deno.env.get("SCHEDULER_SECRET");
  const incomingSecret = req.headers.get("x-scheduler-secret");
  if (secret && secret !== incomingSecret) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const supabase = getServiceClient();
  const { data: assistants, error } = await supabase
    .from("jarvis.assistants")
    .select("id, org_id, persona, owner_user_id");

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const results = [];
  for (const assistant of assistants ?? []) {
    const now = new Date();
    const { data: pendingApprovals } = await supabase
      .from("jarvis.approvals")
      .select("id")
      .eq("assistant_id", assistant.id)
      .eq("status", "pending");
    const { data: dueTasks } = await supabase
      .from("jarvis.tasks")
      .select("id, title")
      .eq("assistant_id", assistant.id)
      .lte("due_at", new Date(now.getTime() + 1000 * 60 * 60 * 48).toISOString());
    const { data: kbDocs } = await supabase
      .from("jarvis.kb_documents")
      .select("id")
      .eq("assistant_id", assistant.id)
      .gte("created_at", new Date(now.getTime() - 1000 * 60 * 60 * 12).toISOString());

    const signals: Signal[] = [];
    if ((pendingApprovals?.length ?? 0) > 0) {
      signals.push({
        type: "approval_pending",
        title: `${pendingApprovals?.length} approvals pending`,
        severity: "high",
      });
    }
    if ((dueTasks?.length ?? 0) > 0) {
      signals.push({
        type: "task_due",
        title: `${dueTasks?.length} tasks due within 48h`,
        severity: "medium",
      });
    }
    if ((kbDocs?.length ?? 0) > 0) {
      signals.push({
        type: "kb_update",
        title: `${kbDocs?.length} new knowledge docs`,
        severity: "low",
      });
    }

    const llmPlan = await fetchPlanFromLLM(signals);
    const plan = Array.isArray(llmPlan) ? llmPlan : makePlan(signals);
    const { data: run, error: runError } = await supabase
      .from("jarvis.assistant_runs")
      .insert({
        org_id: assistant.org_id,
        assistant_id: assistant.id,
        domain: "WORK",
        status: "completed",
        trigger: "scheduler",
        summary: `Generated ${plan.length} plan items.`,
        started_at: now.toISOString(),
        finished_at: now.toISOString(),
      })
      .select()
      .single();

    if (runError) {
      results.push({ assistant: assistant.id, error: runError.message });
      continue;
    }

    await supabase.from("jarvis.assistant_plans").insert({
      run_id: run.id,
      org_id: assistant.org_id,
      assistant_id: assistant.id,
      plan_json: { items: plan },
    });

    const approvalsToInsert = plan
      .filter((item) => item.risk !== "auto_do")
      .map((item) => ({
        org_id: assistant.org_id,
        assistant_id: assistant.id,
        owner_user_id: assistant.owner_user_id,
        domain: "WORK",
        visibility: "business_private",
        status: "pending",
        risk: item.risk === "confirm" ? "high" : "medium",
        proposed_action: item.title,
        metadata: { planId: item.id, rationale: item.rationale },
        requested_by: assistant.owner_user_id,
      }));

    if (approvalsToInsert.length > 0) {
      await supabase.from("jarvis.approvals").insert(approvalsToInsert);
      await supabase.from("jarvis.audit_log").insert({
        org_id: assistant.org_id,
        actor_user_id: assistant.owner_user_id,
        action: "approvals.queued",
        target_table: "jarvis.approvals",
        metadata: { count: approvalsToInsert.length },
      });
    }

    const { data: lastMorning } = await supabase
      .from("jarvis.briefings")
      .select("id, created_at")
      .eq("assistant_id", assistant.id)
      .eq("briefing_type", "morning")
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();

    const nowIso = now.toISOString();
    const lastMorningAt = lastMorning?.created_at
      ? new Date(lastMorning.created_at)
      : null;
    const shouldCreateMorning =
      !lastMorningAt ||
      now.getTime() - lastMorningAt.getTime() > 1000 * 60 * 60 * 20;

    if (shouldCreateMorning) {
      await supabase.from("jarvis.briefings").insert({
        org_id: assistant.org_id,
        assistant_id: assistant.id,
        owner_user_id: assistant.owner_user_id,
        domain: "WORK",
        visibility: "business_private",
        briefing_type: "morning",
        content: {
          generated_at: nowIso,
          summary: "Auto-generated morning briefing.",
          items: signals.map((signal) => signal.title),
        },
      });
    }

    await supabase.from("jarvis.briefings").insert({
      org_id: assistant.org_id,
      assistant_id: assistant.id,
      owner_user_id: assistant.owner_user_id,
      domain: "WORK",
      visibility: "business_private",
      briefing_type: "night",
      content: {
        generated_at: nowIso,
        run_id: run.id,
        plan_count: plan.length,
        approvals_queued: approvalsToInsert.length,
      },
    });

    await supabase.from("jarvis.audit_log").insert({
      org_id: assistant.org_id,
      actor_user_id: assistant.owner_user_id,
      action: "scheduler.run",
      target_table: "jarvis.assistant_runs",
      target_id: run.id,
      metadata: { planCount: plan.length },
    });

    results.push({ assistant: assistant.id, planCount: plan.length });
  }

  return new Response(JSON.stringify({ status: "ok", results }), {
    status: 200,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
});
