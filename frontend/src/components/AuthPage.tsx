import { useState } from "react";
import { login, register } from "../lib/api";
import {Eye,EyeOff} from "lucide-react";

type AuthPageProps = {
  onAuthenticated: () => void;
};

export function AuthPage({ onAuthenticated }: AuthPageProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPswd, setShowPswd]=useState(false);
  const [showConfirmPassword, setShowConfirmPassword]=useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");

    if (mode === "register" && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);

    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password);
      }

      onAuthenticated();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Authentication failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-background p-6">
      <section className="w-full max-w-md rounded-xl border border-border p-8 shadow-sm">
        <div className="mb-8 text-center">
          <div className="text-3xl font-bold tracking-tight">DocSage</div>
          <p className="mt-2 text-sm text-muted">
            Your documents. Searchable and ready to chat.
          </p>
        </div>

        <div className="mb-6 grid grid-cols-2 rounded-lg bg-muted/10 p-1">
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError("");
            }}
            className={`rounded-md px-4 py-2 text-sm ${
              mode === "login" ? "bg-white text-black shadow-sm" : ""
            }`}
          >
            Log in
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError("");
            }}
            className={`rounded-md px-4 py-2 text-sm ${
              mode === "register" ? "bg-white text-black shadow-sm" : ""
            }`}
          >
            Register 
          </button>
        </div>

        <h1 className="mb-1 text-xl font-semibold">
          {mode === "login" ? "Welcome back" : "Create your account"}
        </h1>
        <p className="mb-6 text-sm text-muted">
          {mode === "login"
            ? "Log in to access your documents."
            : "Register to start using DocSage."}
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5 text-sm">
            Email address
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="rounded-md border border-border bg-transparent px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </label>

          
<label className="flex flex-col gap-1.5 text-sm">
  Password
  <div className="relative">
    <input
      type={showPswd ? "text" : "password"}
      autoComplete={
        mode === "login" ? "current-password" : "new-password"
      }
      minLength={8}
      required
      value={password}
      onChange={(e) => setPassword(e.target.value)}
      placeholder="At least 8 characters"
      className="w-full rounded-md border border-border bg-transparent px-3 py-2.5 pr-11 outline-none focus:ring-2 focus:ring-blue-500"
    />
    <button
      type="button"
      onClick={() => setShowPswd((prev) => !prev)}
      aria-label={showPswd ? "Hide password" : "Show password"}
      aria-pressed={showPswd}
      className="absolute inset-y-0 right-0 flex items-center px-3 text-muted hover:text-foreground"
    >
      {showPswd ? (
        <EyeOff size={18} />
      ) : (
        <Eye size={18} />
      )}
    </button>
  </div>
</label>


          
{mode ==="register" && (
<label className="flex flex-col gap-1.5 text-sm">
  Confirm password
  <div className="relative">
    <input
      type={showConfirmPassword ? "text" : "password"}
      autoComplete="new-password"
      minLength={8}
      required
      value={confirmPassword}
      onChange={(e) => setConfirmPassword(e.target.value)}
      placeholder="Re-enter your password"
      className="w-full rounded-md border border-border bg-transparent px-3 py-2.5 pr-11 outline-none focus:ring-2 focus:ring-blue-500"
    />
    <button
      type="button"
      onClick={() => setShowConfirmPassword((prev) => !prev)}
      aria-label={
        showConfirmPassword ? "Hide confirm password" : "Show confirm password"
      }
      aria-pressed={showConfirmPassword}
      className="absolute inset-y-0 right-0 flex items-center px-3 text-muted hover:text-foreground"
    >
      {showConfirmPassword ? (
        <EyeOff size={18} />
      ) : (
        <Eye size={18} />
      )}
    </button>
  </div>
</label>
)}


          {error && (
            <p role="alert" className="rounded-md bg-red-500/10 p-3 text-sm text-red-600">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-blue-600 px-4 py-2.5 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {busy
              ? "Please wait..."
              : mode === "login"
                ? "Log in"
                : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-muted">
          Your account protects access to your documents and conversations.
        </p>
      </section>
    </main>
  );
}
