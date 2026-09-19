
"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import {
  getUserReports,
  uploadReport,
} from "@/services/reportService";

import type { MedicalReport } from "@/types/report";


export default function DashboardPage() {
  const router = useRouter();

  const {
    user,
    loading,
    isAuthenticated,
    logout,
  } = useAuth();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadReports();
    }
  }, [isAuthenticated]);

  async function loadReports() {
    try {
      setLoadingReports(true);
      const data = await getUserReports();
      setReports(data);
    } catch {
      setError("Unable to load your reports.");
    } finally {
      setLoadingReports(false);
    }
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(file);
    setMessage("");
    setError("");
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

      setMessage("Report uploaded successfully.");
      setSelectedFile(null);

      await loadReports();
    } catch {
      setError("Failed to upload report.");
    } finally {
      setUploading(false);
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        Loading dashboard...
      </main>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-white">
      <div className="mx-auto max-w-6xl">

        {/* Header */}
        <header className="flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-center">
          <div>
            <p className="text-sm font-medium text-emerald-400">
              MEDICAL REPORT EXPLAINER
            </p>

            <h1 className="mt-2 text-3xl font-bold">
              Your Dashboard
            </h1>

            <p className="mt-2 text-slate-400">
              Upload and manage your medical reports.
            </p>
          </div>

          <button
            onClick={logout}
            className="rounded-lg border border-red-500/40 px-4 py-2 text-red-400 transition hover:bg-red-500/10"
          >
            Logout
          </button>
        </header>

        {/* Welcome */}
        <section className="mt-8">
          <p className="text-slate-400">
            Signed in as
          </p>

          <p className="font-medium">
            {user.email}
          </p>
        </section>

        {/* Upload Section */}
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold">
            Upload a Medical Report
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Supported formats: PDF, JPG, JPEG, and PNG. Maximum size: 10 MB.
          </p>

          <div className="mt-6 rounded-xl border border-dashed border-slate-600 p-8 text-center">
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileChange}
              className="block w-full text-sm text-slate-300 file:mr-4 file:rounded-lg file:border-0 file:bg-emerald-500 file:px-4 file:py-2 file:font-medium file:text-slate-950 hover:file:bg-emerald-400"
            />

            {selectedFile && (
              <p className="mt-4 text-sm text-emerald-400">
                Selected: {selectedFile.name}
              </p>
            )}
          </div>

          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="mt-5 rounded-lg bg-emerald-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {uploading ? "Uploading..." : "Upload Report"}
          </button>

          {message && (
            <p className="mt-4 text-sm text-emerald-400">
              {message}
            </p>
          )}

          {error && (
            <p className="mt-4 text-sm text-red-400">
              {error}
            </p>
          )}
        </section>

        {/* Report History */}
        <section className="mt-8">
          <h2 className="text-xl font-semibold">
            Your Reports
          </h2>

          {loadingReports ? (
            <p className="mt-4 text-slate-400">
              Loading reports...
            </p>
          ) : reports.length === 0 ? (
            <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900 p-6 text-slate-400">
              No reports uploaded yet.
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              {reports.map((report) => (
                <div
                  key={report.id}
                  onClick={() => router.push(`/dashboard/reports/${report.id}`)}
                  className="cursor-pointer rounded-xl border border-slate-800 bg-slate-900 p-5 transition hover:border-emerald-500/50"
                >
                  <div>
                    <p className="font-medium">
                      {report.file_name}
                    </p>

                    <p className="mt-1 text-sm text-slate-400">
                      Uploaded:{" "}
                      {new Date(report.created_at).toLocaleString()}
                    </p>
                  </div>

                  <span className="w-fit rounded-full bg-emerald-500/10 px-3 py-1 text-sm text-emerald-400">
                    {report.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Medical Disclaimer */}
        <footer className="mt-12 border-t border-slate-800 pt-6 text-sm text-slate-500">
          This application provides educational information and does not
          replace professional medical advice or diagnosis.
        </footer>

      </div>
    </main>
  );
}