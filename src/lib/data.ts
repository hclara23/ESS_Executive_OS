import { getSupabaseServerClient } from "@/lib/supabase/server";

export async function getApprovals() {
  const supabase = await getSupabaseServerClient();
  if (!supabase) return [];
  const { data } = await supabase
    .from("jarvis.approvals")
    .select(
      "id, proposed_action, risk, status, created_at, requested_by, owner_user_id",
    )
    .eq("status", "pending")
    .order("created_at", { ascending: false })
    .limit(10);
  return data ?? [];
}

export async function getTasks() {
  const supabase = await getSupabaseServerClient();
  if (!supabase) return [];
  const { data } = await supabase
    .from("jarvis.tasks")
    .select("id, title, due_at, priority, owner_user_id, created_at")
    .order("due_at", { ascending: true })
    .limit(10);
  return data ?? [];
}

export async function getMorningBriefing(assistantId?: string) {
  const supabase = await getSupabaseServerClient();
  if (!supabase) return null;
  let query = supabase
    .from("jarvis.briefings")
    .select("id, content, created_at, assistant_id")
    .eq("briefing_type", "morning")
    .order("created_at", { ascending: false })
    .limit(1);
  if (assistantId) {
    query = query.eq("assistant_id", assistantId);
  }
  const { data } = await query.maybeSingle();
  return data ?? null;
}

export async function getRuns() {
  const supabase = await getSupabaseServerClient();
  if (!supabase) return [];
  const { data } = await supabase
    .from("jarvis.assistant_runs")
    .select("id, status, created_at, summary")
    .order("created_at", { ascending: false })
    .limit(8);
  return data ?? [];
}

export async function getAssistantByPersona(persona: "alex" | "sandra") {
  const supabase = await getSupabaseServerClient();
  if (!supabase) return null;
  const { data: assistant } = await supabase
    .from("jarvis.assistants")
    .select("id, persona, display_name")
    .eq("persona", persona)
    .limit(1)
    .maybeSingle();
  return assistant ?? null;
}

export async function getTasksForAssistant(assistantId?: string) {
  const supabase = await getSupabaseServerClient();
  if (!supabase || !assistantId) return [];
  const { data } = await supabase
    .from("jarvis.tasks")
    .select("id, title, due_at, priority, owner_user_id, created_at")
    .eq("assistant_id", assistantId)
    .order("due_at", { ascending: true })
    .limit(6);
  return data ?? [];
}

export async function getApprovalsForAssistant(assistantId?: string) {
  const supabase = await getSupabaseServerClient();
  if (!supabase || !assistantId) return [];
  const { data } = await supabase
    .from("jarvis.approvals")
    .select("id, proposed_action, risk, status, created_at, requested_by")
    .eq("assistant_id", assistantId)
    .eq("status", "pending")
    .order("created_at", { ascending: false })
    .limit(6);
  return data ?? [];
}

export async function getAdminTemplates() {
  const supabase = await getSupabaseServerClient();
  if (!supabase) return [];
  const { data } = await supabase
    .from("jarvis.whatsapp_templates")
    .select("id, name, status, description")
    .order("created_at", { ascending: false })
    .limit(6);
  return data ?? [];
}

export async function getAuditLog() {
  const supabase = await getSupabaseServerClient();
  if (!supabase) return [];
  const { data } = await supabase
    .from("jarvis.audit_log")
    .select("id, action, actor_user_id, created_at")
    .order("created_at", { ascending: false })
    .limit(6);
  return data ?? [];
}
