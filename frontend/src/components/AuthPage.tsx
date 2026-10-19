// import { useState } from "react";
// import { login, register } from "../lib/api";
// import {Eye,EyeOff} from "lucide-react";

// type AuthPageProps = {
//   onAuthenticated: () => void;
// };

// export function AuthPage({ onAuthenticated }: AuthPageProps) {
//   const [mode, setMode] = useState<"login" | "register">("login");
//   const [email, setEmail] = useState("");
//   const [password, setPassword] = useState("");
//   const [confirmPassword, setConfirmPassword] = useState("");
//   const [error, setError] = useState("");
//   const [busy, setBusy] = useState(false);
//   const [showPswd, setShowPswd]=useState(false);
//   const [showConfirmPassword, setShowConfirmPassword]=useState(false);

//   async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
//     e.preventDefault();
//     setError("");

//     if (mode === "register" && password !== confirmPassword) {
//       setError("Passwords do not match.");
//       return; 
//     }

//     setBusy(true);

//     try {
//       if (mode === "login") {
//         await login(email.trim(), password);
//       } else {
//         await register(email.trim(), password);
//       }

//       onAuthenticated();
//     } catch (err) {
//       setError(
//         err instanceof Error ? err.message : "Authentication failed.",
//       );
//     } finally {
//       setBusy(false);
//     }
//   }

//   return (
//     <main className="min-h-screen flex items-center justify-center bg-background p-6">
//       <section className="w-full max-w-md rounded-xl border border-border p-8 shadow-sm">
//         <div className="mb-8 text-center">
//           <div className="text-3xl font-bold tracking-tight">DocSage</div>
//           <p className="mt-2 text-sm text-muted">
//             Your documents. Searchable and ready to chat.
//           </p>
//         </div>

//         <div className="mb-6 grid grid-cols-2 rounded-lg bg-muted/10 p-1">
//           <button
//             type="button"
//             onClick={() => {
//               setMode("login");
//               setError("");
//             }}
//             className={`rounded-md px-4 py-2 text-sm ${
//               mode === "login" ? "bg-white text-black shadow-sm" : ""
//             }`}
//           >
//             Log in
//           </button>
//           <button
//             type="button"
//             onClick={() => {
//               setMode("register");
//               setError("");
//             }}
//             className={`rounded-md px-4 py-2 text-sm ${
//               mode === "register" ? "bg-white text-black shadow-sm" : ""
//             }`}
//           >
//             Register 
//           </button>
//         </div>

//         <h1 className="mb-1 text-xl font-semibold">
//           {mode === "login" ? "Welcome back" : "Create your account"}
//         </h1>
//         <p className="mb-6 text-sm text-muted">
//           {mode === "login"
//             ? "Log in to access your documents."
//             : "Register to start using DocSage."}
//         </p>

//         <form onSubmit={handleSubmit} className="flex flex-col gap-4">
//           <label className="flex flex-col gap-1.5 text-sm">
//             Email address
//             <input
//               type="email"
//               autoComplete="email"
//               required
//               value={email}
//               onChange={(e) => setEmail(e.target.value)}
//               placeholder="you@example.com"
//               className="rounded-md border border-border bg-transparent px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500"
//             />
//           </label>

          
// <label className="flex flex-col gap-1.5 text-sm">
//   Password
//   <div className="relative">
//     <input
//       type={showPswd ? "text" : "password"}
//       autoComplete={
//         mode === "login" ? "current-password" : "new-password"
//       }
//       minLength={8}
//       required
//       value={password}
//       onChange={(e) => setPassword(e.target.value)}
//       placeholder="At least 8 characters"
//       className="w-full rounded-md border border-border bg-transparent px-3 py-2.5 pr-11 outline-none focus:ring-2 focus:ring-blue-500"
//     />
//     <button
//       type="button"
//       onClick={() => setShowPswd((prev) => !prev)}
//       aria-label={showPswd ? "Hide password" : "Show password"}
//       aria-pressed={showPswd}
//       className="absolute inset-y-0 right-0 flex items-center px-3 text-muted hover:text-foreground"
//     >
//       {showPswd ? (
//         <EyeOff size={18} />
//       ) : (
//         <Eye size={18} />
//       )}
//     </button>
//   </div>
// </label>


          
// {mode ==="register" && (
// <label className="flex flex-col gap-1.5 text-sm">
//   Confirm password
//   <div className="relative">
//     <input
//       type={showConfirmPassword ? "text" : "password"}
//       autoComplete="new-password"
//       minLength={8}
//       required
//       value={confirmPassword}
//       onChange={(e) => setConfirmPassword(e.target.value)}
//       placeholder="Re-enter your password"
//       className="w-full rounded-md border border-border bg-transparent px-3 py-2.5 pr-11 outline-none focus:ring-2 focus:ring-blue-500"
//     />
//     <button
//       type="button"
//       onClick={() => setShowConfirmPassword((prev) => !prev)}
//       aria-label={
//         showConfirmPassword ? "Hide confirm password" : "Show confirm password"
//       }
//       aria-pressed={showConfirmPassword}
//       className="absolute inset-y-0 right-0 flex items-center px-3 text-muted hover:text-foreground"
//     >
//       {showConfirmPassword ? (
//         <EyeOff size={18} />
//       ) : (
//         <Eye size={18} />
//       )}
//     </button>
//   </div>
// </label>
// )}


//           {error && (
//             <p role="alert" className="rounded-md bg-red-500/10 p-3 text-sm text-red-600">
//               {error}
//             </p>
//           )}

//           <button
//             type="submit"
//             disabled={busy}
//             className="rounded-md bg-blue-600 px-4 py-2.5 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
//           >
//             {busy
//               ? "Please wait..."
//               : mode === "login"
//                 ? "Log in"
//                 : "Create account"}
//           </button>
//         </form>

//         <p className="mt-6 text-center text-xs text-muted">
//           Your account protects access to your documents and conversations.
//         </p>
//       </section>
//     </main>
//   );
// }



import { useState } from "react";
import { login, register } from "../lib/api";
import {
  Eye,
  EyeOff,
  FileText,
  Sparkles,
  ShieldCheck,
  Search,
  MessageSquareText,
  LoaderCircle,
  ArrowRight,
} from "lucide-react";

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
  const [showPswd, setShowPswd] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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

  function switchMode(nextMode: "login" | "register") {
    setMode(nextMode);
    setError("");
    setConfirmPassword("");
    setShowPswd(false);
    setShowConfirmPassword(false);
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#080B14] px-4 py-10 text-slate-100 sm:px-6">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[420px] w-[700px] -translate-x-1/2 rounded-full bg-violet-600/[0.09] blur-[130px]" />
        <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-indigo-500/[0.06] blur-[100px]" />
      </div>

      <div className="relative z-10 grid w-full max-w-5xl items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <section className="hidden lg:block">
          <div className="mb-10 inline-flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-400/20 bg-violet-500/10 text-violet-300 shadow-lg shadow-violet-950/20">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">
                DocSage
              </h1>
              <p className="text-xs text-slate-500">
                Document intelligence, simplified
              </p>
            </div>
          </div>

          <div className="max-w-lg">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-500/[0.08] px-3 py-1.5 text-xs font-medium text-violet-300">
              <Sparkles className="h-3.5 w-3.5" />
              Your personal document assistant
            </div>

            <h2 className="text-4xl font-semibold leading-[1.2] tracking-tight text-white xl:text-5xl">
              Your documents.
              <span className="block bg-gradient-to-r from-violet-300 to-indigo-300 bg-clip-text text-transparent">
                Now, more intelligent.
              </span>
            </h2>

            <p className="mt-5 max-w-md text-base leading-7 text-slate-400">
              Upload, discover, ask, search and what not from some sized pdfs, the information that
              matters, and get answers in your content.
            </p>
          </div>

          <div className="mt-10 space-y-4">
            <div className="flex items-center gap-4 rounded-2xl border border-slate-800/80 bg-slate-900/50 p-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-500/10 text-violet-300">
                <Search className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">
                  Find what matters
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Search your document content using natural language.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 rounded-2xl border border-slate-800/80 bg-slate-900/50 p-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-300">
                <MessageSquareText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">
                  Ask and understand
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Explore your content through contextual conversations.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 rounded-2xl border border-slate-800/80 bg-slate-900/50 p-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-300">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">
                  Your own workspace
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Sign in to access your account and documents.
                </p>
              </div>
            </div>
          </div>

          <p className="mt-8 text-xs text-slate-600">
            Built for smarter document workflows.
          </p>
        </section>

        <section className="mx-auto w-full max-w-md">
          <div className="mb-7 flex items-center justify-center gap-3 lg:hidden">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-violet-400/20 bg-violet-500/10 text-violet-300">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">
                DocSage
              </h1>
              <p className="text-xs text-slate-500">
                Document intelligence, simplified
              </p>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-700/70 bg-slate-900/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl sm:p-8">
            <div className="mb-7">
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
                {mode === "login" ? "Welcome back" : "Get started"}
              </p>

              <h2 className="text-2xl font-semibold tracking-tight text-white">
                {mode === "login" ? "Sign in to DocSage" : "Create your account"}
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                {mode === "login"
                  ? "Continue exploring your documents and conversations."
                  : "Create an account to start working with your documents."}
              </p>
            </div>

            <div className="mb-6 grid grid-cols-2 gap-1 rounded-xl border border-slate-800 bg-slate-950/70 p-1">
              <button
                type="button"
                onClick={() => switchMode("login")}
                aria-pressed={mode === "login"}
                className={`rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                  mode === "login"
                    ? "bg-violet-500/15 text-violet-200 shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Sign in
              </button>

              <button
                type="button"
                onClick={() => switchMode("register")}
                aria-pressed={mode === "register"}
                className={`rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                  mode === "register"
                    ? "bg-violet-500/15 text-violet-200 shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Create account
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-300">
                Email address
                <input
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/60 px-4 py-3 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-600 hover:border-slate-600 focus:border-violet-400/70 focus:ring-2 focus:ring-violet-500/10"
                />
              </label>

              <label className="flex flex-col gap-2 text-sm font-medium text-slate-300">
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
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/60 px-4 py-3 pr-12 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-600 hover:border-slate-600 focus:border-violet-400/70 focus:ring-2 focus:ring-violet-500/10"
                  />

                  <button
                    type="button"
                    onClick={() => setShowPswd((prev) => !prev)}
                    aria-label={showPswd ? "Hide password" : "Show password"}
                    aria-pressed={showPswd}
                    className="absolute inset-y-0 right-0 flex items-center px-4 text-slate-500 transition-colors hover:text-violet-300"
                  >
                    {showPswd ? (
                      <EyeOff className="h-[18px] w-[18px]" />
                    ) : (
                      <Eye className="h-[18px] w-[18px]" />
                    )}
                  </button>
                </div>
              </label>

              {mode === "register" && (
                <label className="flex flex-col gap-2 text-sm font-medium text-slate-300">
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
                      className="w-full rounded-xl border border-slate-700 bg-slate-950/60 px-4 py-3 pr-12 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-600 hover:border-slate-600 focus:border-violet-400/70 focus:ring-2 focus:ring-violet-500/10"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword((prev) => !prev)
                      }
                      aria-label={
                        showConfirmPassword
                          ? "Hide confirm password"
                          : "Show confirm password"
                      }
                      aria-pressed={showConfirmPassword}
                      className="absolute inset-y-0 right-0 flex items-center px-4 text-slate-500 transition-colors hover:text-violet-300"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-[18px] w-[18px]" />
                      ) : (
                        <Eye className="h-[18px] w-[18px]" />
                      )}
                    </button>
                  </div>
                </label>
              )}

              {error && (
                <p
                  role="alert"
                  className="rounded-xl border border-red-400/20 bg-red-500/[0.08] px-4 py-3 text-sm leading-6 text-red-300"
                >
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={busy}
                className="mt-1 flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-950/30 transition-all hover:bg-violet-500 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? (
                  <>
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                    Please wait...
                  </>
                ) : (
                  <>
                    {mode === "login" ? "Sign in" : "Create account"}
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 flex items-start justify-center gap-2 border-t border-slate-800 pt-5">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
              <p className="max-w-xs text-center text-xs leading-5 text-slate-500">
                Sign in to access your workspace and your documents.
              </p>
            </div>
          </div>

          <p className="mt-5 text-center text-[11px] text-slate-600">
            DocSage · Document intelligence powered by AI
          </p>
        </section>
      </div>
    </main>
  );
}
