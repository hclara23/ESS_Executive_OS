import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabase/server";

export async function GET(
  _req: Request,
  { params }: { params: { persona: "alex" | "sandra" } },
) {
  const supabase = await getSupabaseServerClient();
  if (!supabase) {
    return NextResponse.json({ error: "Supabase not configured." }, { status: 500 });
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data: assistant } = await supabase
    .from("jarvis.assistants")
    .select("id")
    .eq("persona", params.persona)
    .limit(1)
    .maybeSingle();

  if (!assistant?.id) {
    return NextResponse.json({ error: "Assistant not found" }, { status: 404 });
  }

  const { data: tasks } = await supabase
    .from("jarvis.tasks")
    .select("id, title, due_at, priority")
    .eq("assistant_id", assistant.id)
    .order("due_at", { ascending: true })
    .limit(6);

  const { data: approvals } = await supabase
    .from("jarvis.approvals")
    .select("id, proposed_action, risk, status")
    .eq("assistant_id", assistant.id)
    .eq("status", "pending")
    .order("created_at", { ascending: false })
    .limit(6);

  return NextResponse.json({ tasks: tasks ?? [], approvals: approvals ?? [] });
}
