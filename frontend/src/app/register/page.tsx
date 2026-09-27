
"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Stethoscope,
  UserPlus,
  AlertCircle,
  LoaderCircle,
} from "lucide-react";

import { registerUser } from "@/services/authService";

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

  const inputClass =
    "w-full rounded-xl border border-white/[0.08] bg-[#0b1120] py-3.5 pl-11 pr-12 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/10";

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#080d18] px-4 py-10 text-slate-100 sm:px-6">

      {/* Background glow */}
      <div className="pointer-events-none absolute -left-40 -top-40 h-96 w-96 rounded-full bg-emerald-500/8 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-teal-500/6 blur-[120px]" />

      <div className="relative z-10 w-full max-w-md">

        {/* Brand */}
        <Link
          href="/"
          className="mb-8 flex items-center justify-center gap-3"
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-500/10">
            <Activity
              size={23}
              className="text-emerald-400"
            />
          </div>

          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              Medi<span className="text-emerald-400">Clarity</span>
            </h1>
            <p className="text-xs text-slate-500">
              Understand your medical reports
            </p>
          </div>
        </Link>

        {/* Registration Card */}
        <div className="rounded-2xl border border-white/8 bg-[#111827]/90 p-6 shadow-2xl shadow-black/20 sm:p-8">

          {/* Heading */}
          <div className="mb-7">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10">
              <UserPlus
                size={22}
                className="text-emerald-400"
              />
            </div>

            <h2 className="text-2xl font-bold tracking-tight text-white">
              Create your account
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-400">
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
                <Mail
                  size={18}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"
                />

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
                <LockKeyhole
                  size={18}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"
                />

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
                    setShowPassword(!showPassword)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 transition hover:text-emerald-400"
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
                  className="text-emerald-500/70"
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
                <LockKeyhole
                  size={18}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"
                />

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
                      !showConfirmPassword
                    )
                  }
                  aria-label={
                    showConfirmPassword
                      ? "Hide confirm password"
                      : "Show confirm password"
                  }
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 transition hover:text-emerald-400"
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

            {/* Error Message */}
            {error && (
              <div
                role="alert"
                className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.07] p-3.5 text-sm text-red-300"
              >
                <AlertCircle
                  size={18}
                  className="mt-0.5 shrink-0"
                />
                <p>{error}</p>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div
                role="status"
                className="flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/[0.07] p-3.5 text-sm text-emerald-300"
              >
                <CheckCircle2
                  size={18}
                  className="mt-0.5 shrink-0"
                />
                <p>{success}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !!success}
              className="group flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-3.5 text-sm font-semibold text-[#06110d] shadow-lg shadow-emerald-500/10 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <>
                  <LoaderCircle
                    size={18}
                    className="animate-spin"
                  />
                  Creating account...
                </>
              ) : success ? (
                "Account created"
              ) : (
                <>
                  Create account
                  <ArrowRight
                    size={18}
                    className="transition-transform group-hover:translate-x-1"
                  />
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-7 border-t border-white/6 pt-6">
            <p className="text-center text-sm text-slate-400">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-semibold text-emerald-400 transition hover:text-emerald-300"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 space-y-2 text-center">
          <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
            <Stethoscope
              size={14}
              className="text-emerald-500/70"
            />
            Your health information deserves clarity.
          </div>

          <p className="text-[11px] leading-5 text-slate-600">
            MediClarity provides educational explanations
            of medical reports and is not a substitute
            for professional medical advice.
          </p>
        </div>
      </div>
    </main>
  );
}
