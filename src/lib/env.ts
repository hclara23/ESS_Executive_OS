import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1).optional(),
  TWILIO_ACCOUNT_SID: z.string().min(1).optional(),
  TWILIO_AUTH_TOKEN: z.string().min(1).optional(),
  TWILIO_WHATSAPP_FROM: z.string().min(1).optional(),
  OPTIONAL_LLM_API_KEY: z.string().min(1).optional(),
  OPTIONAL_LLM_EMBEDDING_URL: z.string().url().optional(),
  OPTIONAL_LLM_PLANNER_URL: z.string().url().optional(),
  OPTIONAL_LLM_MODEL: z.string().min(1).optional(),
  SCHEDULER_SECRET: z.string().min(1).optional(),
});

export const env = envSchema.parse({
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
  TWILIO_ACCOUNT_SID: process.env.TWILIO_ACCOUNT_SID,
  TWILIO_AUTH_TOKEN: process.env.TWILIO_AUTH_TOKEN,
  TWILIO_WHATSAPP_FROM: process.env.TWILIO_WHATSAPP_FROM,
  OPTIONAL_LLM_API_KEY: process.env.OPTIONAL_LLM_API_KEY,
  OPTIONAL_LLM_EMBEDDING_URL: process.env.OPTIONAL_LLM_EMBEDDING_URL,
  OPTIONAL_LLM_PLANNER_URL: process.env.OPTIONAL_LLM_PLANNER_URL,
  OPTIONAL_LLM_MODEL: process.env.OPTIONAL_LLM_MODEL,
  SCHEDULER_SECRET: process.env.SCHEDULER_SECRET,
});
