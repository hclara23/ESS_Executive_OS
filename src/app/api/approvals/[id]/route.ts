import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabase/server";
import { getSupabaseAdminClient } from "@/lib/supabase/admin";

export async function PATCH(
  req: Request,
  { params }: { params: { id: string } },
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

  const body = await req.json();
  const status = body.status as "approved" | "rejected" | "canceled";
  if (!status) {
    return NextResponse.json({ error: "Missing status" }, { status: 400 });
  }

  const admin = getSupabaseAdminClient();
  const { data: approval, error } = await admin
    .from("jarvis.approvals")
    .update({ status, approved_by: user.id })
    .eq("id", params.id)
    .eq("status", "pending")
    .select("id, org_id")
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }

  await admin.from("jarvis.audit_log").insert({
    org_id: approval.org_id,
    actor_user_id: user.id,
    action: "approval.update",
    target_table: "jarvis.approvals",
    target_id: approval.id,
    metadata: { status },
  });

  return NextResponse.json({ ok: true, approvalId: approval.id, status });
}
