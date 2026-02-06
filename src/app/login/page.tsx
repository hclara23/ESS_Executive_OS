import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="glass-panel w-full max-w-md p-8">
        <div className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          ESS Executive OS
        </div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Sign in</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Access your executive workspace securely.
        </p>
        <AuthForm />
      </div>
    </div>
  );
}
