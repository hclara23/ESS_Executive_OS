"use client";

import * as React from "react";
import { motion } from "framer-motion";
import {
  Bell,
  ChevronDown,
  Command,
  Globe,
  Moon,
  Sun,
} from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Switch } from "@/components/ui/switch";
import { useSessionStore } from "@/stores/session";

export function TopNav() {
  const { theme, setTheme } = useTheme();
  const { domain, setDomain, allowPersonalInWork, togglePersonalInWork, role } =
    useSessionStore();

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur"
    >
      <div className="mx-auto flex w-full max-w-[1400px] items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-foreground text-background shadow-sm">
            <Command className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              ESS
            </div>
            <div className="text-lg font-semibold tracking-tight">Executive OS</div>
          </div>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <div className="glass-card flex items-center gap-3 rounded-full px-3 py-1.5 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Domain</span>
            <button
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                domain === "WORK" ? "bg-foreground text-background" : "text-muted-foreground"
              }`}
              onClick={() => setDomain("WORK")}
            >
              Work
            </button>
            <button
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                domain === "PERSONAL"
                  ? "bg-foreground text-background"
                  : "text-muted-foreground"
              }`}
              onClick={() => setDomain("PERSONAL")}
            >
              Personal
            </button>
          </div>

          <div className="glass-card flex items-center gap-3 rounded-full px-3 py-1.5 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Merge Personal</span>
            <Switch
              checked={allowPersonalInWork}
              onCheckedChange={() => togglePersonalInWork()}
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" className="rounded-full">
            <Bell className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="rounded-full">
            <Globe className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="rounded-full px-3">
                <span className="text-sm font-medium">Role: {role}</span>
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => useSessionStore.getState().setRole("owner")}>
                Owner
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => useSessionStore.getState().setRole("admin")}>
                Admin
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => useSessionStore.getState().setRole("member")}>
                Member
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </motion.header>
  );
}
