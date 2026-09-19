
import api from "@/lib/api";
import type {
  MedicalReport,
  UploadResponse,
} from "@/types/report";

export interface StructuredParameter {
  value: number;
  flag: string | null;
}

export interface StructuredData {
  [parameter: string]: StructuredParameter;
}

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
  report_id: number;
  extracted_text: string;
  structured_data: StructuredData | null;
  explanation: Record<string, unknown> | null;
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