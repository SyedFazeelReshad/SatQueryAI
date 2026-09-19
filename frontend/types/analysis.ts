export type AnalysisMode = 'single_image' | 'optical_sar' | 'change_analysis';

export interface MeasurementResult {
  label: string;
  value: number | string;
  unit: string;
  evidence_type: string;
}

export interface DetectionResult {
  label: string;
  score: number;
  box_xyxy: [number, number, number, number];
  polygon_points?: [number, number][];
}

export interface AnalysisResult {
  session_id: string;
  task_type: string;
  answer: string;
  measurements: MeasurementResult[];
  confidence: number | null;
  confidence_level: string;
  evidence_ids: string[];
  execution_trace_id: string;
  warnings: string[];
  preview_url: string | null;
  overlay_url: string | null;
  preview_b_url?: string | null;  // second image preview for change/dual analysis
  layers?: Record<string, string>;
  detections?: DetectionResult[];
  report_urls: Record<string, string>;
}

export interface QueryResponse {
  session_id: string;
  query: string;
  answer: string;
  model: string;
  stage: number;
  is_stub: boolean;
  warnings: string[];
}

export interface InvestigateResponse {
  session_id: string;
  region_label: string;
  spectral_stats: Record<string, any>;
  answer: string;
  evidence_ids: string[];
  warnings: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  stage: number;
  vlm_available: boolean;
  timestamp: string;
}
