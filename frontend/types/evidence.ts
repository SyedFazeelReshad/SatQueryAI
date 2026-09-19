export type EvidenceType = 'OBSERVED' | 'DERIVED' | 'DETECTED' | 'AI_DETECTED' | 'INFERRED' | 'SYNTHETIC';

export interface EvidenceRecord {
  evidence_id: string;
  task: string;
  evidence_type: EvidenceType;
  source_image: string;
  source_date: string | null;
  sensor: string | null;
  tool: string;
  model: string | null;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
  confidence: number | null;
  confidence_basis: string | null;
  geometry: Record<string, unknown> | null;
  timestamp: string;
  warnings: string[];
}
