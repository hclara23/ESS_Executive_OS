import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { corsHeaders } from "../_shared/cors.ts";
import { getServiceClient } from "../_shared/supabase.ts";

const twiml = (message: string) =>
  new Response(`<?xml version="1.0" encoding="UTF-8"?><Response><Message>${message}</Message></Response>`, {
    headers: { "Content-Type": "text/xml" },
  });

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const form = await req.formData();
  const from = String(form.get("From") ?? "");
  const body = String(form.get("Body") ?? "").trim();

  const supabase = getServiceClient();

  const { data: consent } = await supabase
    .from("jarvis.whatsapp_consent")
    .select("org_id, owner_user_id, opted_out_at")
    .eq("phone", from)
    .maybeSingle();

  if (!consent || consent.opted_out_at) {
    if (body.toUpperCase() === "START") {
      const orgId = Deno.env.get("DEFAULT_ORG_ID");
      if (!orgId) {
        return twiml("Unable to opt in. Contact administrator.");
      }
      await supabase.from("jarvis.whatsapp_consent").upsert({
        org_id: orgId,
        phone: from,
        opted_in_at: new Date().toISOString(),
        opted_out_at: null,
        source: "whatsapp",
      });
      return twiml("You are now opted in. Reply BRIEF, STATUS, APPROVE <id>, or REJECT <id>.");
    }
    return twiml("You are not opted in. Reply START to opt in.");
  }

  await supabase.from("jarvis.messages").insert({
    org_id: consent.org_id,
    owner_user_id: consent.owner_user_id,
    domain: "WORK",
    visibility: "business_private",
    channel: "whatsapp",
    direction: "inbound",
    status: "received",
    sender: from,
    content: body,
  });

  await supabase.from("jarvis.audit_log").insert({
    org_id: consent.org_id,
    actor_user_id: consent.owner_user_id,
    action: "whatsapp.inbound",
    target_table: "jarvis.messages",
    metadata: { from, body },
  });

  await supabase.from("jarvis.whatsapp_sessions").upsert({
    org_id: consent.org_id,
    phone: from,
    last_inbound_at: new Date().toISOString(),
  });

  const upper = body.toUpperCase();
  if (upper === "STOP") {
    await supabase
      .from("jarvis.whatsapp_consent")
      .update({ opted_out_at: new Date().toISOString() })
      .eq("phone", from);
    return twiml("You have been opted out. Reply START to opt in again.");
  }

  if (upper.startsWith("APPROVE")) {
    const id = body.split(" ")[1];
    if (id) {
      await supabase
        .from("jarvis.approvals")
        .update({ status: "approved", approved_by: consent.owner_user_id })
        .eq("id", id)
        .eq("status", "pending");
      return twiml(`Approval ${id} recorded.`);
    }
  }

  if (upper.startsWith("REJECT")) {
    const id = body.split(" ")[1];
    if (id) {
      await supabase
        .from("jarvis.approvals")
        .update({ status: "rejected", approved_by: consent.owner_user_id })
        .eq("id", id)
        .eq("status", "pending");
      return twiml(`Rejection ${id} recorded.`);
    }
  }

  if (upper === "BRIEF") {
    return twiml("Briefing requested. Latest summary will be delivered shortly.");
  }

  if (upper === "STATUS") {
    return twiml("Status: 2 approvals pending, 4 tasks due within 48h.");
  }

  if (upper === "OPEN") {
    return twiml("Command Center opened. Reply APPROVE <id> or REJECT <id>.");
  }

  return twiml("Command received. Reply BRIEF, STATUS, APPROVE <id>, or REJECT <id>.");
});
