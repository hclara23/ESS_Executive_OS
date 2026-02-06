"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

export function AuthForm() {
  const [mode, setMode] = React.useState<"login" | "register">("login");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [status, setStatus] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    setStatus(null);
    const supabase = getSupabaseBrowserClient();
    if (!supabase) {
      setStatus("Supabase not configured.");
      setLoading(false);
      return;
    }
    if (mode === "login") {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        setStatus(error.message);
      } else {
        window.location.href = "/";
      }
    } else {
      const { error } = await supabase.auth.signUp({
        email,
        password,
      });
      setStatus(
        error ? error.message : "Check your email to confirm your account.",
      );
    }
    setLoading(false);
  };

  return (
    <div className="mt-6 space-y-4">
      <Input
        placeholder="name@ess.com"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <Input
        placeholder="Password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <Button onClick={handleSubmit} disabled={loading} className="w-full rounded-full">
        {loading ? "Loading..." : mode === "login" ? "Sign in" : "Create account"}
      </Button>
      <button
        className="w-full text-xs text-muted-foreground"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
        type="button"
      >
        {mode === "login"
          ? "Need an account? Create one."
          : "Already have an account? Sign in."}
      </button>
      {status && <div className="text-xs text-muted-foreground">{status}</div>}
    </div>
  );
}
