"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { TopNav } from "@/components/top-nav";
import { Sidebar } from "@/components/sidebar";

type AppShellProps = {
  children: React.ReactNode;
  title?: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
};

export function AppShell({
  children,
  title,
  description,
  actions,
  className,
}: AppShellProps) {
  return (
    <div className="min-h-screen">
      <TopNav />
      <div className="mx-auto flex w-full max-w-[1400px] gap-8 px-6 pb-16 pt-8">
        <Sidebar />
        <main className={cn("flex-1 space-y-8", className)}>
          {(title || description || actions) && (
            <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
              <div>
                {title && (
                  <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
                    {title}
                  </h1>
                )}
                {description && (
                  <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
                    {description}
                  </p>
                )}
              </div>
              {actions && <div className="flex items-center gap-3">{actions}</div>}
            </div>
          )}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: "easeOut" }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
