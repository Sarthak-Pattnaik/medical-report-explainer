
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";

import { useAuth } from "@/context/AuthContext";
import MedicalExplanationSection from "@/components/reports/MedicalExplanationSection";

import {
  getReportDetails,
  getReportAnalysis,
  getReportExplanation,
  downloadReportFile,
  type ReportDetails,
  type ReportAnalysis,
  type MedicalExplanation,
  type ClinicalContextExplanation,
} from "@/services/reportService";

function formatParameterName(parameter: string): string {
  return parameter
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

export default function ReportDetailsPage() {
  const params = useParams();
  const router = useRouter();

  const { loading, isAuthenticated } = useAuth();

  const [report, setReport] = useState<ReportDetails | null>(null);
  const [loadingReport, setLoadingReport] = useState(true);
  const [error, setError] = useState("");
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [fileError, setFileError] = useState("");

  const [analysis, setAnalysis] = useState<ReportAnalysis | null>(null);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(true);
  const [analysisError, setAnalysisError] = useState("");

  const reportId = Number(params.id);

  const [explanation, setExplanation] =
    useState<MedicalExplanation | null>(null);

  const [isLoadingExplanation, setIsLoadingExplanation] =
    useState(true);

  const [explanationError, setExplanationError] =
    useState("");

  const handlePreviewFile = async () => {
    try {
      setIsLoadingFile(true);
      setFileError("");

      const blob = await downloadReportFile(reportId);
      if (!blob) {
        setFileError("The report file does not exist.");
        return;
      }
      const url = URL.createObjectURL(blob);

      setFileUrl((previousUrl) => {
        if (previousUrl) {
          URL.revokeObjectURL(previousUrl);
        }

        return url;
      });
    } catch (error) {
      console.error("Failed to load report file:", error);
      setFileError("Unable to load the report file.");
    } finally {
      setIsLoadingFile(false);
    }
  };

  useEffect(() => {
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [fileUrl]);

  useEffect(() => {
    if (
      !isAuthenticated ||
      !Number.isInteger(reportId) ||
      reportId <= 0
    ) {
      return;
    }

    const fetchAnalysis = async () => {
      try {
        setIsLoadingAnalysis(true);
        setAnalysisError("");
        setAnalysis(null);

        const data = await getReportAnalysis(reportId);
        if (!data) {
          // Handled gracefully as a null state rather than an error state
          setAnalysisError("No analysis exists for this report yet.");
          return;
        }
        setAnalysis(data);
      } catch (error) {
        console.error("Failed to fetch analysis:", error);

        setAnalysisError("Unable to load extracted text.");
      } finally {
        setIsLoadingAnalysis(false);
      }
    };

    fetchAnalysis();
  }, [isAuthenticated, reportId]);


  useEffect(() => {
    if (
      !isAuthenticated ||
      !Number.isInteger(reportId) ||
      reportId <= 0
    ) {
      return;
    }

    const fetchExplanation = async () => {
      try {
        setIsLoadingExplanation(true);
        setExplanationError("");

        const data = await getReportExplanation(reportId);

        if (!data) {
          // Graceful empty state
          setExplanationError("No explanation has been generated for this report yet.");
          return;
        }

        setExplanation(data.explanation);
      } catch (error) {
        // Only log actual unexpected errors
        console.error("Failed to fetch explanation:", error);
        setExplanationError(
          "An error occurred while loading the explanation."
        );
      } finally {
        setIsLoadingExplanation(false);
      }
    };

    fetchExplanation();
  }, [isAuthenticated, reportId]);


  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && Number.isInteger(reportId) && reportId > 0) {
      loadReport();
    } else if (isAuthenticated) {
      setError("Invalid report ID.");
      setLoadingReport(false);
    }
  }, [isAuthenticated, reportId]);

  async function loadReport() {
    try {
      setLoadingReport(true);
      setError("");

      const data = await getReportDetails(reportId);
      setReport(data);
    } catch {
      setError("Unable to load this report.");
    } finally {
      setLoadingReport(false);
    }
  }

  if (loading || loadingReport) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        Loading report...
      </main>
    );
  }

  if (!isAuthenticated) {
    return null;
  }


  return (
    <main className="min-h-screen bg-[#080d18] text-slate-100">
      {/* Top navigation */}
      <nav className="sticky top-0 z-20 border-b border-white/6 bg-[#080d18]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-3 text-left"
          >
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
          </button>

          <button
            onClick={() => router.push("/dashboard")}
            className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-emerald-400/30 hover:text-emerald-300"
          >
            ← Dashboard
          </button>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
        {/* Breadcrumb */}
        <div className="mb-6 flex flex-wrap items-center gap-2 text-sm">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-slate-500 transition hover:text-emerald-300"
          >
            Dashboard
          </button>

          <span className="text-slate-700">/</span>

          <span className="text-slate-300">
            Report Details
          </span>
        </div>

        {error ? (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/6 p-6 text-sm text-red-300">
            {error}
          </div>
        ) : report ? (
          <>

            {/* Report header */}
            <section className="overflow-hidden rounded-3xl border border-white/[0.07] bg-slate-900/60">
              {/* Header title */}
              <div className="border-b border-white/6 p-6 sm:p-8">
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
                  <div className="min-w-0">
                    <div className="mb-4 flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-emerald-400/20 bg-emerald-400/[0.07] px-3 py-1 text-xs font-medium text-emerald-300">
                        Medical document
                      </span>

                      <span className="text-xs text-slate-500">
                        Report #{report.id}
                      </span>
                    </div>

                    <h1 className="wrap-break-word text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                      {report.file_name}
                    </h1>

                    <p className="mt-3 text-sm leading-6 text-slate-400">
                      Uploaded on{" "}
                      {new Date(report.created_at).toLocaleString(
                        undefined,
                        {
                          day: "numeric",
                          month: "long",
                          year: "numeric",
                          hour: "numeric",
                          minute: "2-digit",
                        }
                      )}
                    </p>
                  </div>

                  <span className="w-fit shrink-0 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
                    {report.status
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (char) => char.toUpperCase())}
                  </span>
                </div>
              </div>

              {/* Document actions */}
              <div className="flex flex-col justify-between gap-4 p-6 sm:flex-row sm:items-center sm:px-8">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Original document
                  </h2>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Preview or download the uploaded medical report.
                  </p>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handlePreviewFile}
                    disabled={isLoadingFile}
                    className="flex items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isLoadingFile ? (
                      <>
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950" />
                        Loading preview...
                      </>
                    ) : (
                      <>
                        <span aria-hidden="true">↗</span>
                        Preview report
                      </>
                    )}
                  </button>

                  {fileUrl && (
                    <a
                      href={fileUrl}
                      download={report.file_name}
                      className="flex items-center justify-center gap-2 rounded-xl border border-white/10 px-5 py-3 text-sm font-medium text-slate-300 transition hover:border-emerald-400/30 hover:text-emerald-300"
                    >
                      Download
                      <span aria-hidden="true">↓</span>
                    </a>
                  )}
                </div>
              </div>

              {fileError && (
                <div
                  role="alert"
                  className="mx-6 mb-6 rounded-xl border border-red-400/20 bg-red-400/6 px-4 py-3 text-sm text-red-300 sm:mx-8"
                >
                  {fileError}
                </div>
              )}

              {/* Document preview */}
              {fileUrl && (
                <div className="border-t border-white/6 p-4 sm:p-6">
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-slate-200">
                        Document preview
                      </h3>

                      <p className="mt-1 text-xs text-slate-500">
                        Original uploaded file
                      </p>
                    </div>

                    <a
                      href={fileUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-medium text-emerald-300 transition hover:text-emerald-200"
                    >
                      Open in new tab ↗
                    </a>
                  </div>

                  <div className="overflow-hidden rounded-2xl border border-white/8 bg-[#080d18]">
                    {report.file_name.toLowerCase().endsWith(".pdf") ? (
                      <iframe
                        src={fileUrl}
                        title="Medical report preview"
                        className="h-162.5 w-full sm:h-200"
                      />
                    ) : (
                      <div className="flex max-h-200 min-h-64 items-center justify-center overflow-auto p-4 sm:p-8">
                        <img
                          src={fileUrl}
                          alt="Uploaded medical report"
                          className="h-auto max-h-187.5 max-w-full rounded-lg object-contain"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-8 rounded-xl border border-white/10 bg-white/5 p-6">
                <h2 className="mb-4 text-xl font-semibold">
                  Extracted Text
                </h2>


                {analysisError ? (
                  <div className="mt-4 rounded-xl border border-red-400/15 bg-red-400/4 p-5">
                    <div className="flex items-start gap-3">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-red-400/15 bg-red-400/6 text-red-400">
                        !
                      </span>

                      <div>
                        <p className="text-sm font-semibold text-red-300">
                          Unable to load extracted text
                        </p>
                        <p className="mt-1 text-sm leading-6 text-slate-400">
                          {analysisError}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : !analysis?.extracted_text?.trim() ? (
                  <div className="mt-4 rounded-xl border border-white/[0.07] bg-slate-900/40 p-6 text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-white/[0.07] bg-white/3 text-slate-500">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        className="h-6 w-6"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
                        <path d="M14 3v5h5M9 13h6m-6 4h6" />
                      </svg>
                    </div>

                    <h3 className="mt-4 text-sm font-semibold text-white">
                      No extracted text available
                    </h3>

                    <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-400">
                      Text could not be extracted from this report.
                      This may happen if the document contains
                      scanned images or unreadable content.
                    </p>

                    <p className="mt-3 text-xs text-slate-500">
                      You can still view or download your original report above.
                    </p>
                  </div>
                ) : (

                  <div className="mt-4 overflow-hidden rounded-xl border border-white/[0.07] bg-[#0b1120]">
                    {/* Text container header */}
                    <div className="flex items-center justify-between border-b border-white/6 px-5 py-3">
                      <span className="text-xs font-medium text-slate-400">
                        Extracted report text
                      </span>

                      <span className="text-xs text-slate-500">
                        Scroll to read
                      </span>
                    </div>

                    {/* Scrollable text */}
                    <div className="max-h-100 overflow-y-auto overscroll-contain p-5 sm:p-6">
                      <pre className="whitespace-pre-wrap wrap-break-word font-mono text-sm leading-7 text-slate-300">
                        {analysis.extracted_text}
                      </pre>
                    </div>
                  </div>

                )}

              </div>


              {/* Structured Medical Parameters */}
              <section className="mt-8 overflow-hidden rounded-2xl border border-white/[0.07] bg-slate-900/60">
                {/* Section Header */}
                <div className="border-b border-white/[0.06] px-5 py-5 sm:px-7">
                  <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                    <div>
                      <h2 className="text-xl font-semibold tracking-tight text-white">
                        Structured Medical Parameters
                      </h2>
                      <p className="mt-1.5 text-sm text-slate-500">
                        Extracted values and their reported reference information.
                      </p>
                    </div>

                    {analysis?.structured_data?.parameters?.length ? (
                      <span className="w-fit rounded-full border border-emerald-400/20 bg-emerald-400/[0.06] px-3 py-1.5 text-xs font-medium text-emerald-300">
                        {analysis.structured_data.parameters.length}{" "}
                        {analysis.structured_data.parameters.length === 1
                          ? "parameter"
                          : "parameters"}
                      </span>
                    ) : null}
                  </div>
                </div>

                {/* Parameters Table */}
                {analysis?.structured_data?.parameters?.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[850px] text-left text-sm">
                      <thead className="bg-white/[0.02]">
                        <tr className="border-b border-white/[0.07] text-xs uppercase tracking-wider text-slate-500">
                          <th className="px-5 py-4 font-medium sm:px-7">
                            Parameter
                          </th>
                          <th className="px-5 py-4 font-medium">
                            Value
                          </th>
                          <th className="px-5 py-4 font-medium">
                            Unit
                          </th>
                          <th className="px-5 py-4 font-medium">
                            Reference Range
                          </th>
                          <th className="px-5 py-4 font-medium">
                            Flag
                          </th>
                          <th className="px-5 py-4 font-medium">
                            Confidence
                          </th>
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-white/[0.06]">
                        {analysis.structured_data.parameters.map(
                          (parameter, index) => {
                            const flag = (
                              parameter.flag ?? "unknown"
                            ).toLowerCase();

                            const confidence = (
                              parameter.confidence ?? "low"
                            ).toLowerCase();

                            const flagStyles: Record<string, string> = {
                              normal:
                                "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
                              high:
                                "border-amber-400/20 bg-amber-400/10 text-amber-300",
                              low:
                                "border-sky-400/20 bg-sky-400/10 text-sky-300",
                              critical:
                                "border-red-400/20 bg-red-400/10 text-red-300",
                              unknown:
                                "border-slate-500/20 bg-slate-500/10 text-slate-400",
                            };

                            const confidenceStyles: Record<string, string> = {
                              high:
                                "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
                              medium:
                                "border-amber-400/20 bg-amber-400/10 text-amber-300",
                              low:
                                "border-slate-500/20 bg-slate-500/10 text-slate-400",
                            };

                            return (
                              <tr
                                key={`${parameter.name}-${index}`}
                                className="transition hover:bg-white/[0.02]"
                              >
                                {/* Parameter Name */}
                                <td className="px-5 py-4 sm:px-7">
                                  <div className="font-medium text-slate-200">
                                    {parameter.name}
                                  </div>

                                  {parameter.source_text && (
                                    <details className="mt-2 max-w-xs">
                                      <summary className="cursor-pointer text-xs text-slate-500 transition hover:text-emerald-300">
                                        View source text
                                      </summary>

                                      <p className="mt-2 whitespace-normal break-words rounded-lg border border-white/[0.06] bg-[#080d18] p-3 text-xs leading-5 text-slate-400">
                                        {parameter.source_text}
                                      </p>
                                    </details>
                                  )}
                                </td>

                                {/* Value */}
                                <td className="px-5 py-4">
                                  <span className="font-semibold tabular-nums text-white">
                                    {parameter.value ?? "—"}
                                  </span>
                                </td>

                                {/* Unit */}
                                <td className="px-5 py-4 text-slate-400">
                                  {parameter.unit ?? "—"}
                                </td>

                                {/* Reference Range */}
                                <td className="px-5 py-4 text-slate-400">
                                  {parameter.reference_range ?? "—"}
                                </td>

                                {/* Flag */}
                                <td className="px-5 py-4">
                                  <span
                                    className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium capitalize ${flagStyles[flag] ??
                                      flagStyles.unknown
                                      }`}
                                  >
                                    {flag}
                                  </span>
                                </td>

                                {/* Confidence */}
                                <td className="px-5 py-4">
                                  <span
                                    className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium capitalize ${confidenceStyles[confidence] ??
                                      confidenceStyles.low
                                      }`}
                                  >
                                    {confidence}
                                  </span>
                                </td>
                              </tr>
                            );
                          }
                        )}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="px-6 py-12 text-center">
                    <p className="text-sm font-medium text-slate-300">
                      No structured parameters found
                    </p>
                    <p className="mt-2 text-sm text-slate-500">
                      No measurable parameters could be extracted from this report.
                    </p>
                  </div>
                )}
              </section>

              {/* Extraction Notes */}
              {analysis?.structured_data?.extraction_notes?.length ? (
                <section className="mt-4 rounded-2xl border border-amber-400/15 bg-amber-400/4 p-5 sm:p-6">
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-amber-400/15 bg-amber-400/8 text-amber-300">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        className="h-5 w-5"
                        stroke="currentColor"
                        strokeWidth="1.7"
                      >
                        <circle cx="12" cy="12" r="9" />
                        <path
                          d="M12 11v5m0-8h.01"
                          strokeLinecap="round"
                        />
                      </svg>
                    </div>

                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-amber-300">
                        Extraction Notes
                      </h3>

                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        Review these notes when interpreting extracted values.
                      </p>

                      <ul className="mt-4 space-y-2.5">
                        {analysis.structured_data.extraction_notes.map(
                          (note, index) => (
                            <li
                              key={index}
                              className="flex items-start gap-3 text-sm leading-6 text-slate-300"
                            >
                              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                              <span>{note}</span>
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  </div>
                </section>
              ) : null}

              {/* Extraction Method */}

              {analysis?.structured_data?.extraction_method && (
                <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-white/6 bg-slate-900/40 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-emerald-400/15 bg-emerald-400/6 text-emerald-300">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        className="h-5 w-5"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4" />
                        <path d="M9 12h6m-6 4h6" />
                        <path d="m16 3 5 5-9 9-4 1 1-4 9-9Z" />
                      </svg>
                    </div>

                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        Extraction method
                      </p>

                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        Method used to identify and structure report data.
                      </p>
                    </div>
                  </div>

                  <span className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/6 px-3.5 py-2 text-xs font-semibold text-emerald-300">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                    {analysis.structured_data.extraction_method
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (char) => char.toUpperCase())}
                  </span>
                </div>
              )}


              <MedicalExplanationSection
                explanation={explanation}
                loading={isLoadingExplanation}
                error={explanationError}
              />
            </section>
          </>
        ) : null}
      </div>
    </main>
  );

}