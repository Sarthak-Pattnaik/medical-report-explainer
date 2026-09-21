
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import {
  getReportDetails,
  type ReportDetails,
} from "@/services/reportService";
import { downloadReportFile } from "@/services/reportService";

import {
  getReportAnalysis,
  ReportAnalysis
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

  const handlePreviewFile = async () => {
    try {
      setIsLoadingFile(true);
      setFileError("");

      const blob = await downloadReportFile(reportId);

      const url = URL.createObjectURL(blob);

      setFileUrl(url);
    } catch (error) {
      console.error("Failed to load report file:", error);
      setFileError("Unable to load the report file.");
    } finally {
      setIsLoadingFile(false);
    }
  };

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setIsLoadingAnalysis(true);
        setAnalysisError("");

        const data = await getReportAnalysis(reportId);

        setAnalysis(data);
      } catch (error) {
        console.error("Failed to fetch analysis:", error);
        setAnalysisError("Unable to load extracted text.");
      } finally {
        setIsLoadingAnalysis(false);
      }
    };

    fetchAnalysis();
  }, [reportId]);

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
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-white">
      <div className="mx-auto max-w-4xl">

        <button
          onClick={() => router.push("/dashboard")}
          className="text-sm text-emerald-400 hover:text-emerald-300"
        >
          ← Back to Dashboard
        </button>

        <h1 className="mt-6 text-3xl font-bold">
          Report Details
        </h1>

        {error ? (
          <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 p-5 text-red-400">
            {error}
          </div>
        ) : report ? (
          <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6">

            <h2 className="text-xl font-semibold">
              {report.file_name}
            </h2>

            <div className="mt-6 space-y-4">
              <div>
                <p className="text-sm text-slate-400">
                  Report ID
                </p>
                <p>{report.id}</p>
              </div>

              <div>
                <p className="text-sm text-slate-400">
                  Status
                </p>
                <span className="inline-block rounded-full bg-emerald-500/10 px-3 py-1 text-sm text-emerald-400">
                  {report.status}
                </span>
              </div>

              <div>
                <p className="text-sm text-slate-400">
                  Uploaded On
                </p>
                <p>
                  {new Date(report.created_at).toLocaleString()}
                </p>
              </div>

              <button
                onClick={handlePreviewFile}
                disabled={isLoadingFile}
                className="rounded-lg bg-emerald-500 px-4 py-2 font-medium text-black transition hover:bg-emerald-400 disabled:opacity-50"
              >
                {isLoadingFile ? "Loading..." : "Preview Report"}
              </button>

              {fileError && (
                <p className="mt-4 text-red-400">
                  {fileError}
                </p>
              )}

              {fileUrl && (
                <div className="mt-6">
                  <a
                    href={fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-400 underline"
                  >
                    Open Report File
                  </a>

                  <a
                    href={fileUrl}
                    download={report?.file_name}
                    className="ml-4 text-emerald-400 underline"
                  >
                    Download Report
                  </a>
                </div>
              )}
            </div>

            <div className="mt-8 rounded-xl border border-white/10 bg-white/5 p-6">
              <h2 className="mb-4 text-xl font-semibold">
                Extracted Text
              </h2>

              {isLoadingAnalysis && (
                <p className="text-gray-400">
                  Loading extracted text...
                </p>
              )}

              {analysisError && (
                <p className="text-red-400">
                  {analysisError}
                </p>
              )}

              {!isLoadingAnalysis && analysis && (
                <pre className="max-h-[600px] overflow-auto whitespace-pre-wrap text-sm leading-6 text-gray-300">
                  {analysis.extracted_text}
                </pre>
              )}
            </div>

            <div className="mt-8 rounded-xl border border-white/10 bg-white/5 p-6">
              <h2 className="mb-4 text-xl font-semibold">
                Structured Medical Parameters
              </h2>

              {analysis?.structured_data?.parameters?.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="px-4 py-3">Parameter</th>
                        <th className="px-4 py-3">Value</th>
                        <th className="px-4 py-3">Unit</th>
                        <th className="px-4 py-3">Flag</th>
                        <th className="px-4 py-3">Confidence</th>
                      </tr>
                    </thead>

                    <tbody>
                      {analysis.structured_data.parameters.map(
                        (parameter, index) => (
                          <tr
                            key={`${parameter.name}-${index}`}
                            className="border-b"
                          >
                            <td className="px-4 py-3 font-medium">
                              {parameter.name}
                            </td>

                            <td className="px-4 py-3">
                              {parameter.value ?? "Not available"}
                            </td>

                            <td className="px-4 py-3">
                              {parameter.unit ?? "—"}
                            </td>

                            <td className="px-4 py-3">
                              {parameter.flag ?? "unknown"}
                            </td>

                            <td className="px-4 py-3">
                              {parameter.confidence}
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  No structured parameters were extracted.
                </p>
              )}
            </div>

            {analysis?.structured_data?.extraction_notes?.length ? (
              <div className="mt-4 rounded-lg border border-yellow-500/40 bg-yellow-500/10 p-4">
                <h3 className="font-semibold text-yellow-600">
                  Extraction Notes
                </h3>

                <ul className="mt-2 list-disc pl-5 text-sm">
                  {analysis.structured_data.extraction_notes.map(
                    (note, index) => (
                      <li key={index}>{note}</li>
                    )
                  )}
                </ul>
              </div>
            ) : null}

            {analysis?.structured_data?.extraction_method && (
              <p className="mt-3 text-sm text-gray-500">
                Extraction method:{" "}
                <span className="font-medium">
                  {analysis.structured_data.extraction_method}
                </span>
              </p>
            )}

            <div className="mt-8 rounded-xl border border-slate-800 bg-slate-950 p-5">
              <h3 className="font-semibold">
                Report Analysis
              </h3>

              <p className="mt-2 text-sm text-slate-400">
                Analysis functionality will be added in the next stage.
              </p>
            </div>

          </section>
        ) : null}

      </div>
    </main>
  );
}