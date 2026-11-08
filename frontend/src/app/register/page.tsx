"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from "lucide-react";

import { registerUser } from "@/services/authService";

const inputClass =
  "w-full rounded-xl border border-white/8 bg-[#080d18] py-3.5 pl-12 pr-14 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/10";

const inputIconClass =
  "pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-500";

const toggleClass =
  "absolute inset-y-0 right-4 flex items-center text-slate-500 transition hover:text-emerald-300";

export default function RegisterPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (password.length < 8) {
      setError(
        "Password must be at least 8 characters long."
      );
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await registerUser({
        email,
        password,
      });

      setSuccess(
        "Account created successfully! Redirecting to sign in..."
      );

      setTimeout(() => {
        router.push("/login");
      }, 1200);
    } catch (error: unknown) {
      const message =
        (
          error as {
            response?: {
              data?: {
                detail?: unknown;
              };
            };
          }
        ).response?.data?.detail;

      setError(
        typeof message === "string"
          ? message
          : "Registration failed. Please check your details and try again."
      );
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

        {/* Registration Card */}
        <div className="rounded-3xl border border-white/8 bg-slate-900/70 p-6 shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-9">
          {/* Heading */}
          <div className="mb-8">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/6 px-3 py-1.5 text-xs font-medium text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Your health documents, simplified
            </div>

            <h1 className="text-3xl font-semibold tracking-tight text-white">
              Create your account
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Get started with clearer, easier-to-understand
              medical reports.
            </p>
          </div>

          {/* Form */}
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
                <Mail size={20} className={inputIconClass} />

                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  className={inputClass}
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                Password
              </label>

              <div className="relative">
                <LockKeyhole size={20} className={inputIconClass} />

                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  className={inputClass}
                  placeholder="Create a password"
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
                  className={toggleClass}
                >
                  {showPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>

              <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
                <ShieldCheck
                  size={14}
                  className="text-emerald-400/70"
                />
                Use at least 8 characters.
              </p>
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                Confirm password
              </label>

              <div className="relative">
                <LockKeyhole size={20} className={inputIconClass} />

                <input
                  id="confirmPassword"
                  type={
                    showConfirmPassword
                      ? "text"
                      : "password"
                  }
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                  className={inputClass}
                  placeholder="Re-enter your password"
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowConfirmPassword(
                      (previous) => !previous
                    )
                  }
                  aria-label={
                    showConfirmPassword
                      ? "Hide confirm password"
                      : "Show confirm password"
                  }
                  className={toggleClass}
                >
                  {showConfirmPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>

              {confirmPassword.length > 0 && (
                <p
                  className={`mt-2 flex items-center gap-1.5 text-xs ${
                    password === confirmPassword
                      ? "text-emerald-400"
                      : "text-slate-500"
                  }`}
                >
                  {password === confirmPassword ? (
                    <>
                      <CheckCircle2 size={14} />
                      Passwords match
                    </>
                  ) : (
                    "Passwords must match"
                  )}
                </p>
              )}
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

            {/* Success */}
            {success && (
              <div
                role="status"
                className="flex items-start gap-3 rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-4"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-emerald-400/20 text-xs font-semibold text-emerald-300">
                  ✓
                </span>

                <p className="text-sm leading-6 text-emerald-300">
                  {success}
                </p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !!success}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 py-3.5 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/8 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950" />
                  Creating account...
                </>
              ) : success ? (
                "Account created"
              ) : (
                <>
                  Create account
                  <span aria-hidden="true">→</span>
                </>
              )}
            </button>
          </form>

          {/* Login link */}
          <div className="mt-7 border-t border-white/6 pt-6">
            <p className="text-center text-sm text-slate-400">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-semibold text-emerald-300 transition hover:text-emerald-200"
              >
                Sign in
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