import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await getSupabaseServerClient();
  if (!supabase) {
    return NextResponse.json({ status: "error", message: "Supabase not configured" }, { status: 500 });
  }

  const { error } = await supabase.from("jarvis.orgs").select("id").limit(1);
  if (error) {
    return NextResponse.json({ status: "error", message: error.message }, { status: 500 });
  }

  return NextResponse.json({ status: "ready" });
}
