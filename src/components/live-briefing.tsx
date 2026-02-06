"use client";

import * as React from "react";

type BriefingContent = {
  schedule?: { time: string; title: string }[];
  priorities?: string[];
  opportunities?: string[];
};

type Briefing = {
  content: BriefingContent;
};

type Props = {
  initialBriefing: Briefing | null;
  intervalMs?: number;
  render: (content: BriefingContent) => React.ReactNode;
};

export function LiveBriefing({
  initialBriefing,
  intervalMs = 300000,
  render,
}: Props) {
  const [briefing, setBriefing] = React.useState<Briefing | null>(initialBriefing);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const response = await fetch("/api/briefing", { cache: "no-store" });
      const data = await response.json();
      if (active) {
        setBriefing(data.briefing ?? null);
      }
    };
    const id = setInterval(load, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return <>{render(briefing?.content ?? {})}</>;
}
