
"use client";

import {
  ChangeEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import {
  getUserReports,
  uploadReport,
} from "@/services/reportService";

import type { MedicalReport } from "@/types/report";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const ALLOWED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
];

export default function DashboardPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    user,
    loading,
    isAuthenticated,
    logout,
  } = useAuth();

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [reports, setReports] =
    useState<MedicalReport[]>([]);

  const [uploading, setUploading] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadReports = useCallback(async () => {
    try {
      setLoadingReports(true);
      setError("");

      const data = await getUserReports();
      setReports(data);
    } catch {
      setError("Unable to load your reports.");
    } finally {
      setLoadingReports(false);
    }
  }, []);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadReports();
    }
  }, [isAuthenticated, loadReports]);

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(null);
    setMessage("");
    setError("");

    if (!file) return;

    if (
      !ALLOWED_TYPES.includes(file.type) &&
      !/\.(pdf|jpe?g|png)$/i.test(file.name)
    ) {
      setError(
        "Please select a PDF, JPG, JPEG, or PNG file."
      );
      event.target.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("The maximum file size is 10 MB.");
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) {
      setError("Please select a file first.");
      return;
    }

    try {
      setUploading(true);
      setMessage("");
      setError("");

      await uploadReport(selectedFile);

      setMessage("Your report was uploaded successfully.");
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      await loadReports();
    } catch {
      setError(
        "We couldn't upload your report. Please try again."
      );
    } finally {
      setUploading(false);
    }
  }

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  function formatStatus(status: string) {
    return status
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }

  function getStatusStyle(status: string) {
    const normalized = status.toLowerCase();

    if (
      normalized === "completed" ||
      normalized === "text_extracted"
    ) {
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-400";
    }

    if (
      normalized === "failed" ||
      normalized === "error"
    ) {
      return "border-red-500/20 bg-red-500/10 text-red-400";
    }

    return "border-amber-500/20 bg-amber-500/10 text-amber-400";
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#080d18] text-slate-300">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
          <span className="text-sm">Loading your dashboard...</span>
        </div>
      </main>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <main className="min-h-screen bg-[#080d18] text-slate-100">
      {/* Top navigation */}
      <nav className="sticky top-0 z-20 border-b border-white/6 bg-[#080d18]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-400 text-lg font-bold text-slate-950">
              M
            </div>

            <div>
              <p className="font-semibold tracking-tight text-white">
                Medi<span className="text-emerald-400">Clarity</span>
              </p>
              <p className="text-[11px] tracking-wide text-slate-500">
                MEDICAL REPORT EXPLAINER
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="max-w-48 truncate text-sm font-medium text-slate-200">
                {user.email}
              </p>
              <p className="text-xs text-slate-500">
                Personal workspace
              </p>
            </div>

            <button
              onClick={logout}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-red-400/30 hover:bg-red-400/10 hover:text-red-300"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-12">
        {/* Welcome section */}
        <section className="mb-10">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/6 px-3 py-1.5 text-xs font-medium text-emerald-300">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Your personal health workspace
              </div>

              <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Welcome back
                <span className="text-emerald-400">.</span>
              </h1>

              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400 sm:text-base">
                Keep your medical reports organized and
                understand the information in them, one
                report at a time.
              </p>
            </div>

            <div className="flex items-center gap-3 rounded-2xl border border-white/6 bg-white/2 px-4 py-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 text-emerald-300">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  className="h-5 w-5"
                  stroke="currentColor"
                  strokeWidth="1.7"
                >
                  <path
                    d="M12 3v18M3 12h18"
                    strokeLinecap="round"
                  />
                </svg>
              </div>

              <div>
                <p className="text-xl font-semibold text-white">
                  {reports.length}
                </p>
                <p className="text-xs text-slate-500">
                  Reports uploaded
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Upload section */}
        <section
          id="upload"
          className="mb-12 overflow-hidden rounded-3xl border border-emerald-400/15 bg-linear-to-br from-emerald-400/[0.07] via-slate-900/80 to-slate-900/80"
        >
          <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[1fr_1.1fr] lg:items-center lg:p-10">
            <div>
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-emerald-300">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  className="h-6 w-6"
                  stroke="currentColor"
                  strokeWidth="1.6"
                >
                  <path
                    d="M12 16V4m0 0L7 9m5-5 5 5M5 15v4a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>

              <h2 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">
                Understand your next report
              </h2>

              <p className="mt-3 max-w-md text-sm leading-6 text-slate-400">
                Upload a medical report to extract its
                contents, organize key findings, and
                receive an easy-to-understand explanation.
              </p>

              <div className="mt-6 flex flex-wrap gap-2">
                {["PDF", "JPG", "JPEG", "PNG"].map((format) => (
                  <span
                    key={format}
                    className="rounded-lg border border-white/8 bg-white/3 px-3 py-1.5 text-xs font-medium text-slate-400"
                  >
                    {format}
                  </span>
                ))}

                <span className="rounded-lg border border-white/8 bg-white/3 px-3 py-1.5 text-xs text-slate-500">
                  Up to 10 MB
                </span>
              </div>
            </div>

            <div className="rounded-2xl border border-white/8 bg-[#080d18]/70 p-5 sm:p-6">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileChange}
                disabled={uploading}
                className="hidden"
                id="report-upload"
              />

              <label
                htmlFor="report-upload"
                className={`flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed px-5 py-8 text-center transition ${
                  uploading
                    ? "cursor-not-allowed border-slate-700 opacity-50"
                    : "border-slate-700 hover:border-emerald-400/50 hover:bg-emerald-400/3"
                }`}
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-emerald-300">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-6 w-6"
                    stroke="currentColor"
                    strokeWidth="1.6"
                  >
                    <path
                      d="M12 16V4m0 0L7 9m5-5 5 5M5 15v4a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>

                {selectedFile ? (
                  <>
                    <p className="max-w-full break-all text-sm font-medium text-emerald-300">
                      {selectedFile.name}
                    </p>
                    <p className="mt-2 text-xs text-slate-500">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                      {" · "}Click to change file
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-medium text-slate-200">
                      Choose a report to upload
                    </p>
                    <p className="mt-2 text-xs text-slate-500">
                      Click here to browse your files
                    </p>
                  </>
                )}
              </label>

              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {uploading ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950" />
                    Uploading report...
                  </>
                ) : (
                  <>
                    Upload medical report
                    <span aria-hidden="true">→</span>
                  </>
                )}
              </button>

              {message && (
                <p
                  role="status"
                  className="mt-4 rounded-xl border border-emerald-400/20 bg-emerald-400/6 px-4 py-3 text-sm text-emerald-300"
                >
                  {message}
                </p>
              )}

              {error && (
                <p
                  role="alert"
                  className="mt-4 rounded-xl border border-red-400/20 bg-red-400/6 px-4 py-3 text-sm text-red-300"
                >
                  {error}
                </p>
              )}
            </div>
          </div>
        </section>

        {/* Reports section */}
        <section>
          <div className="mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
                Your workspace
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                Your reports
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Access your uploaded medical documents and
                their available analysis.
              </p>
            </div>

            <button
              onClick={loadReports}
              disabled={loadingReports}
              className="w-fit rounded-xl border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:border-emerald-400/30 hover:text-emerald-300 disabled:opacity-50"
            >
              {loadingReports ? "Refreshing..." : "Refresh reports"}
            </button>
          </div>

          {loadingReports && reports.length === 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((item) => (
                <div
                  key={item}
                  className="animate-pulse rounded-2xl border border-white/6 bg-slate-900/60 p-6"
                >
                  <div className="h-10 w-10 rounded-xl bg-slate-800" />
                  <div className="mt-5 h-4 w-3/4 rounded bg-slate-800" />
                  <div className="mt-3 h-3 w-1/2 rounded bg-slate-800" />
                  <div className="mt-6 h-6 w-24 rounded-full bg-slate-800" />
                </div>
              ))}
            </div>
          ) : reports.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-800 bg-slate-900/40 px-6 py-14 text-center sm:py-20">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800 text-slate-400">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  className="h-8 w-8"
                  stroke="currentColor"
                  strokeWidth="1.5"
                >
                  <path
                    d="M7 3.75h7l5 5v11.5H7a2 2 0 0 1-2-2v-12a2 2 0 0 1 2-2.5Z"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M14 4v5h5M9 14h6M9 17h6"
                    strokeLinecap="round"
                  />
                </svg>
              </div>

              <h3 className="mt-5 text-lg font-semibold text-white">
                No reports yet
              </h3>

              <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">
                Your uploaded reports will appear here.
                Start by uploading your first medical
                document above.
              </p>

              <button
                onClick={() =>
                  document.getElementById("upload")?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                  })
                }
                className="mt-6 rounded-xl bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300"
              >
                Upload your first report
              </button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {reports.map((report) => (
                <button
                  key={report.id}
                  type="button"
                  onClick={() =>
                    router.push(
                      `/dashboard/reports/${report.id}`
                    )
                  }
                  className="group flex flex-col rounded-2xl border border-white/[0.07] bg-slate-900/60 p-5 text-left transition duration-200 hover:-translate-y-0.5 hover:border-emerald-400/30 hover:bg-slate-900"
                >
                  <div className="flex w-full items-start justify-between gap-3">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/6 bg-slate-800 text-emerald-300">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        className="h-5 w-5"
                        stroke="currentColor"
                        strokeWidth="1.6"
                      >
                        <path
                          d="M7 3.75h7l5 5v11.5H7a2 2 0 0 1-2-2v-12a2 2 0 0 1 2-2.5Z"
                          strokeLinejoin="round"
                        />
                        <path
                          d="M14 4v5h5M9 14h6M9 17h6"
                          strokeLinecap="round"
                        />
                      </svg>
                    </div>

                    <span
                      className={`rounded-full border px-2.5 py-1 text-[11px] font-medium ${getStatusStyle(report.status)}`}
                    >
                      {formatStatus(report.status)}
                    </span>
                  </div>

                  <p className="mt-5 line-clamp-2 break-all text-sm font-semibold leading-6 text-slate-100 transition group-hover:text-emerald-300">
                    {report.file_name}
                  </p>

                  <p className="mt-2 text-xs text-slate-500">
                    Uploaded {formatDate(report.created_at)}
                  </p>

                  <div className="mt-6 flex w-full items-center justify-between border-t border-white/6 pt-4">
                    <span className="text-xs font-medium text-slate-400">
                      View report
                    </span>

                    <span className="text-sm text-slate-500 transition group-hover:translate-x-1 group-hover:text-emerald-300">
                      →
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Medical disclaimer */}
        <footer className="mt-16 border-t border-white/6 py-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 text-emerald-400">ⓘ</span>
              <p className="max-w-2xl text-xs leading-6 text-slate-500">
                MediClarity provides educational
                information to help users understand their
                medical documents. It does not replace
                professional medical advice, diagnosis, or
                treatment.
              </p>
            </div>

            <p className="shrink-0 text-xs text-slate-600">
              Medical Report Explainer
            </p>
          </div>
        </footer>
      </div>
    </main>
  );
}
