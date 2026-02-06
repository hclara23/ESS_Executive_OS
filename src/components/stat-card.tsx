"use client";

import { cn } from "@/lib/utils";

type StatCardProps = {
  label: string;
  value: string;
  trend?: string;
  className?: string;
};

export function StatCard({ label, value, trend, className }: StatCardProps) {
  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-3 text-3xl font-semibold tracking-tight">{value}</div>
      {trend && <div className="mt-2 text-xs text-muted-foreground">{trend}</div>}
    </div>
  );
}
