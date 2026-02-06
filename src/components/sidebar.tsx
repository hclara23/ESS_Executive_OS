"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  CalendarCheck,
  ClipboardList,
  Home,
  Inbox,
  MessageCircle,
  MoonStar,
  Settings,
  Shield,
  Sparkles,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSessionStore } from "@/stores/session";

const navItems = [
  { href: "/", label: "Command Center", icon: Home },
  { href: "/alex", label: "Alex Workspace", icon: User },
  { href: "/sandra", label: "Sandra Workspace", icon: User },
  { href: "/chat", label: "Chat", icon: MessageCircle },
  { href: "/briefing", label: "Morning Briefing", icon: Sparkles },
  { href: "/night", label: "Night Shift", icon: MoonStar },
  { href: "/tasks", label: "Tasks", icon: ClipboardList },
  { href: "/approvals", label: "Approvals", icon: CalendarCheck },
  { href: "/kb", label: "Knowledge Base", icon: BookOpen },
  { href: "/memory", label: "Memory", icon: Inbox },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/admin", label: "Admin", icon: Shield },
];

export function Sidebar() {
  const pathname = usePathname();
  const { activePersona, role, setPersona } = useSessionStore();

  return (
    <aside className="hidden w-64 shrink-0 flex-col gap-6 rounded-[32px] border border-border/60 bg-sidebar/80 p-4 shadow-sm backdrop-blur lg:flex">
      <div className="glass-card rounded-2xl p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Persona
        </div>
        <div className="mt-2 text-lg font-semibold">{activePersona === "alex" ? "Alex" : "Sandra"} Sanchez</div>
        <div className="mt-3 text-xs text-muted-foreground">
          {activePersona === "alex" ? "Sales, pipeline, client relationships" : "Admin, finance, HR"}
        </div>
        {role !== "member" && (
          <div className="mt-4 flex gap-2">
            <button
              className={cn(
                "rounded-full px-3 py-1 text-xs font-semibold transition",
                activePersona === "alex"
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:text-foreground",
              )}
              onClick={() => setPersona("alex")}
            >
              Alex
            </button>
            <button
              className={cn(
                "rounded-full px-3 py-1 text-xs font-semibold transition",
                activePersona === "sandra"
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:text-foreground",
              )}
              onClick={() => setPersona("sandra")}
            >
              Sandra
            </button>
          </div>
        )}
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3 py-2 text-sm font-medium transition",
                active
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
