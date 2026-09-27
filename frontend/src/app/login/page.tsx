
"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await login({
        username: email.trim(),
        password,
      });

      router.push("/dashboard");
    } catch (error: unknown) {
      const message =
        (
          error as {
            response?: {
              data?: {
                detail?: string;
              };
            };
          }
        )?.response?.data?.detail ||
        "Login failed. Please check your credentials and try again.";

      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#080d18] px-5 py-10 text-slate-100 sm:px-8">
      {/* Background decorations */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-emerald-500/[0.07] blur-[120px]" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-emerald-400/5 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Brand */}
        <Link
          href="/"
          className="mb-8 flex items-center justify-center gap-3"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-400 text-xl font-bold text-slate-950 shadow-lg shadow-emerald-500/10">
            M
          </div>

          <div>
            <p className="text-xl font-semibold tracking-tight text-white">
              Medi<span className="text-emerald-400">Clarity</span>
            </p>

            <p className="mt-0.5 text-[10px] font-medium tracking-[0.18em] text-slate-500">
              MEDICAL REPORT EXPLAINER
            </p>
          </div>
        </Link>

        {/* Login Card */}
        <div className="rounded-3xl border border-white/8 bg-slate-900/70 p-6 shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-9">
          {/* Heading */}
          <div className="mb-8">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/6 px-3 py-1.5 text-xs font-medium text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Your health documents, simplified
            </div>

            <h1 className="text-3xl font-semibold tracking-tight text-white">
              Welcome back
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Sign in to access your medical reports and
              their plain-language explanations.
            </p>
          </div>

          {/* Login Form */}
          <form
            onSubmit={handleSubmit}
            className="space-y-5"
          >
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                Email address
              </label>

              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-5 w-5"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect
                      x="3"
                      y="5"
                      width="18"
                      height="14"
                      rx="2"
                    />
                    <path d="m3 7 9 6 9-6" />
                  </svg>
                </span>

                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  className="w-full rounded-xl border border-white/8 bg-[#080d18] py-3.5 pl-12 pr-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/10"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-slate-300"
                >
                  Password
                </label>
              </div>

              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-5 w-5"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect
                      x="4"
                      y="10"
                      width="16"
                      height="11"
                      rx="2"
                    />
                    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                  </svg>
                </span>

                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  className="w-full rounded-xl border border-white/8 bg-[#080d18] py-3.5 pl-12 pr-14 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/10"
                  placeholder="Enter your password"
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword((previous) => !previous)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                  className="absolute inset-y-0 right-4 flex items-center text-xs font-medium text-slate-500 transition hover:text-emerald-300"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div
                role="alert"
                className="flex items-start gap-3 rounded-xl border border-red-400/15 bg-red-400/5 p-4"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-red-400/20 text-xs font-semibold text-red-300">
                  !
                </span>

                <p className="text-sm leading-6 text-red-300">
                  {error}
                </p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 py-3.5 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/8 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <span aria-hidden="true">→</span>
                </>
              )}
            </button>
          </form>

          {/* Registration */}
          <div className="mt-7 border-t border-white/6 pt-6">
            <p className="text-center text-sm text-slate-400">
              Don't have an account?{" "}
              <Link
                href="/register"
                className="font-semibold text-emerald-300 transition hover:text-emerald-200"
              >
                Create account
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-xs leading-6 text-slate-500">
            Your medical documents are private and
            accessible only through your account.
          </p>

          <p className="mt-3 text-xs text-slate-600">
            MediClarity provides educational information
            and does not replace professional medical advice.
          </p>
        </div>
      </div>
    </main>
  );
}
