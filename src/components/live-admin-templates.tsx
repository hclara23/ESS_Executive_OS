"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";

type Template = {
  id: string;
  name: string;
  status?: string | null;
};

type Props = {
  initialTemplates: Template[];
  intervalMs?: number;
};

export function LiveAdminTemplates({ initialTemplates, intervalMs = 300000 }: Props) {
  const [templates, setTemplates] = React.useState<Template[]>(initialTemplates);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const response = await fetch("/api/admin/templates", { cache: "no-store" });
      const data = await response.json();
      if (active && Array.isArray(data.templates)) {
        setTemplates(data.templates);
      }
    };
    const id = setInterval(load, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  if (templates.length === 0) {
    return <div className="text-sm text-muted-foreground">No templates configured.</div>;
  }

  return (
    <div className="mt-6 space-y-4">
      {templates.map((template) => (
        <div
          key={template.id}
          className="glass-card flex items-center justify-between p-4 text-sm"
        >
          <div>
            <div className="font-semibold">{template.name}</div>
            <div className="text-xs text-muted-foreground">
              {template.status ?? "Approved"} template
            </div>
          </div>
          <Badge variant="outline">Twilio</Badge>
        </div>
      ))}
    </div>
  );
}
