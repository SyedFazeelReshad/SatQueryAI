export interface QueryRequest {
  session_id: string;
  query: string;
}

export interface TraceStep {
  step_id: string;
  name: string;
  tool: string;
  parameters: Record<string, unknown>;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  started_at: string | null;
  completed_at: string | null;
  duration_s: number | null;
  output_summary: Record<string, unknown>;
  warnings: string[];
  error: string | null;
}

export interface ExecutionTrace {
  trace_id: string;
  session_id: string;
  task_type: string;
  started_at: string;
  completed_at: string | null;
  total_duration_s: number | null;
  steps: TraceStep[];
  status: 'pending' | 'running' | 'success' | 'failed';
}
