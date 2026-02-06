import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabase/server";
import { getSupabaseAdminClient } from "@/lib/supabase/admin";

export async function POST(req: Request) {
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
  const phone = (body.phone ?? "").toString().trim();
  if (!phone) {
    return NextResponse.json({ error: "Missing phone" }, { status: 400 });
  }

  const admin = getSupabaseAdminClient();
  const { data: orgMembership } = await admin
    .from("jarvis.org_members")
    .select("org_id")
    .eq("user_id", user.id)
    .limit(1)
    .maybeSingle();

  if (!orgMembership?.org_id) {
    return NextResponse.json({ error: "No org membership" }, { status: 403 });
  }

  const { data: consent, error } = await admin
    .from("jarvis.whatsapp_consent")
    .upsert({
      org_id: orgMembership.org_id,
      owner_user_id: user.id,
      phone,
      opted_in_at: new Date().toISOString(),
      opted_out_at: null,
      source: "web",
    })
    .select("id")
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }

  await admin.from("jarvis.audit_log").insert({
    org_id: orgMembership.org_id,
    actor_user_id: user.id,
    action: "whatsapp.consent",
    target_table: "jarvis.whatsapp_consent",
    target_id: consent.id,
  });

  return NextResponse.json({ ok: true });
}
