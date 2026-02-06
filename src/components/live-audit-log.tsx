"use client";

import * as React from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Audit = {
  id: string;
  action: string;
  actor_user_id?: string | null;
};

type Props = {
  initialAudit: Audit[];
  intervalMs?: number;
};

export function LiveAuditLog({ initialAudit, intervalMs = 60000 }: Props) {
  const [audit, setAudit] = React.useState<Audit[]>(initialAudit);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const response = await fetch("/api/admin/audit", { cache: "no-store" });
      const data = await response.json();
      if (active && Array.isArray(data.audit)) {
        setAudit(data.audit);
      }
    };
    const id = setInterval(load, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  if (audit.length === 0) {
    return <div className="text-sm text-muted-foreground">No audit entries yet.</div>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Action</TableHead>
          <TableHead>Actor</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {audit.map((entry) => (
          <TableRow key={entry.id}>
            <TableCell className="font-medium">{entry.action}</TableCell>
            <TableCell>{entry.actor_user_id ?? "system"}</TableCell>
            <TableCell>ok</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
