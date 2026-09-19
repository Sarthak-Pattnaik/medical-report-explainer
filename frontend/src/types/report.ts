
export interface MedicalReport {
  id: number;
  file_name: string;
  status: string;
  created_at: string;
}

export interface UploadResponse {
  message: string;
  report_id: number;
  file_name: string;
  status: string;
}