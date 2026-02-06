"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function WhatsAppConsent() {
  const [phone, setPhone] = React.useState("");
  const [status, setStatus] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const submit = async () => {
    if (!phone.trim()) return;
    setLoading(true);
    setStatus(null);
    const response = await fetch("/api/whatsapp/consent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone }),
    });
    const data = await response.json();
    setStatus(data.ok ? "Opt-in saved." : data.error ?? "Unable to save.");
    setLoading(false);
  };

  return (
    <Card className="glass-card p-5">
      <div className="text-sm font-semibold">WhatsApp Opt-in</div>
      <div className="mt-3 text-xs text-muted-foreground">
        Only opted-in numbers can receive notifications.
      </div>
      <div className="mt-4 flex gap-2">
        <Input
          placeholder="+1 555 123 4567"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />
        <Button onClick={submit} disabled={loading} className="rounded-full">
          Save
        </Button>
      </div>
      {status && <div className="mt-2 text-xs text-muted-foreground">{status}</div>}
    </Card>
  );
}
