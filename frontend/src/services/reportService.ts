
import api from "@/lib/api";
import type {
  MedicalReport,
  UploadResponse,
} from "@/types/report";


export async function uploadReport(
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post<UploadResponse>(
    "/reports/upload",
    formData
  );

  return response.data;
}

export async function getUserReports(): Promise<MedicalReport[]> {
  const response = await api.get<MedicalReport[]>("/reports/");

  return response.data;
}


export interface ReportDetails {
  id: number;
  file_name: string;
  file_path: string;
  status: string;
  created_at: string;
}

export async function getReportDetails(
  reportId: number
): Promise<ReportDetails> {
  const response = await api.get<ReportDetails>(
    `/reports/${reportId}`
  );

  return response.data;
}

export function getReportFileUrl(reportId: number): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;

  return `${baseUrl}/reports/${reportId}/file`;
}


export async function downloadReportFile(
  reportId: number
): Promise<Blob> {
  const response = await api.get(
    `/reports/${reportId}/file`,
    {
      responseType: "blob",
    }
  );

  return response.data;
}

export interface ReportAnalysis {
  id?: number;
  report_id: number;
  extracted_text: string | null;
  structured_data: StructuredData | null;
  explanation: Record<string, unknown> | null;
  created_at?: string;
}

export interface StructuredParameter {
  name: string;
  value: number | null;
  unit: string | null;
  flag: "low" | "high" | "normal" | "critical" | "unknown" | null;
  reference_range: string | null;
  source_text: string | null;
  confidence: "low" | "medium" | "high";
}

export interface StructuredData {
  parameters: StructuredParameter[];
  extraction_notes: string[];
  extraction_method?: "groq" | "gemini" | "rule_based" | "failed";
}


export interface ParameterExplanation {
  parameter_name: string;
  result_summary: string;
  what_it_measures: string;
  what_your_result_means: string;
  why_it_matters: string;
  limitations: string[];
  source_text: string | null;
  confidence: "low" | "medium" | "high";
}

export interface ClinicalContextExplanation {
  category: string;
  item: string;
  explanation: string;
  source_text: string | null;
  confidence: "low" | "medium" | "high";
}

export interface MedicalExplanation {
  report_summary: string;
  parameter_explanations: ParameterExplanation[];
  clinical_context_explanations: ClinicalContextExplanation[];
  important_observations: string[];
  limitations: string[];
  disclaimer: string;
}

export interface ReportExplanationResponse {
  report_id: number;
  explanation: MedicalExplanation;
  created_at: string;
}


export async function getReportAnalysis(
  reportId: number
): Promise<ReportAnalysis> {
  const response = await api.get(
    `/reports/${reportId}/analysis`
  );

  return response.data;
}


export async function getReportExplanation(
  reportId: number
): Promise<ReportExplanationResponse> {
  const response = await api.get(
    `/reports/${reportId}/explanation`
  );

  return response.data;
}
