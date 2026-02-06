import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { corsHeaders } from "../_shared/cors.ts";
import { getServiceClient } from "../_shared/supabase.ts";

type Payload = {
  to: string;
  template: string;
  variables?: Record<string, string>;
  org_id?: string;
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const supabase = getServiceClient();
  const payload = (await req.json()) as Payload;

  if (!payload.to || !payload.template) {
    return new Response(JSON.stringify({ error: "Missing to/template" }), {
      status: 400,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const { data: consent } = await supabase
    .from("jarvis.whatsapp_consent")
    .select("org_id, owner_user_id, opted_out_at")
    .eq("phone", payload.to)
    .maybeSingle();

  if (!consent || consent.opted_out_at) {
    return new Response(JSON.stringify({ error: "No consent" }), {
      status: 403,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const orgId = payload.org_id ?? consent.org_id;
  const { data: templateRow } = await supabase
    .from("jarvis.whatsapp_templates")
    .select("content_sid, status")
    .eq("org_id", orgId)
    .eq("name", payload.template)
    .maybeSingle();

  const contentSid = templateRow?.content_sid ?? payload.template;
  if (templateRow && templateRow.status !== "approved") {
    return new Response(JSON.stringify({ error: "Template not approved" }), {
      status: 403,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const accountSid = Deno.env.get("TWILIO_ACCOUNT_SID")!;
  const authToken = Deno.env.get("TWILIO_AUTH_TOKEN")!;
  const from = Deno.env.get("TWILIO_WHATSAPP_FROM")!;

  const body = new URLSearchParams({
    To: payload.to,
    From: from,
    ContentSid: contentSid,
    ContentVariables: JSON.stringify(payload.variables ?? {}),
  });

  const response = await fetch(
    `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`,
    {
      method: "POST",
      headers: {
        Authorization: `Basic ${btoa(`${accountSid}:${authToken}`)}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    },
  );

  const result = await response.json();
  await supabase.from("jarvis.messages").insert({
    org_id: orgId,
    owner_user_id: consent.owner_user_id,
    domain: "WORK",
    visibility: "business_private",
    channel: "whatsapp",
    direction: "outbound",
    status: response.ok ? "sent" : "failed",
    sender: from,
    recipient: payload.to,
    content: `Template: ${payload.template}`,
    external_id: result.sid ?? null,
    metadata: result,
  });

  await supabase.from("jarvis.audit_log").insert({
    org_id: orgId,
    actor_user_id: consent.owner_user_id,
    action: "whatsapp.send",
    target_table: "jarvis.messages",
    metadata: { template: payload.template, to: payload.to, status: result.status },
  });

  await supabase.from("jarvis.whatsapp_sessions").upsert({
    org_id: orgId,
    phone: payload.to,
    last_outbound_at: new Date().toISOString(),
  });

  return new Response(JSON.stringify({ ok: response.ok, result }), {
    status: response.ok ? 200 : 400,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
});
