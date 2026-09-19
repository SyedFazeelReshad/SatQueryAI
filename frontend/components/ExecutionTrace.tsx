'use client';

import { useState, useEffect } from 'react';
import { GitCommit, Clock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { ExecutionTrace } from '@/types/query';
import { getExecutionTrace } from '@/lib/api';
import clsx from 'clsx';

interface ExecutionTraceProps {
  traceId: string;
}

export default function ExecutionTracePanel({ traceId }: ExecutionTraceProps) {
  const [trace, setTrace] = useState<ExecutionTrace | null>(null);

  useEffect(() => {
    if (traceId) {
      getExecutionTrace(traceId).then(setTrace).catch(console.error);
    }
  }, [traceId]);

  if (!trace) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <GitCommit className="w-5 h-5 text-emerald-600" />
          Execution Trace
        </h3>
        {trace.total_duration_s && (
          <span className="text-sm text-slate-500 flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {trace.total_duration_s.toFixed(2)}s
          </span>
        )}
      </div>

      <div className="relative border-l border-slate-200 ml-3 space-y-6">
        {trace.steps.map((step, i) => (
          <div key={step.step_id} className="relative pl-6">
            <div className={clsx(
              "absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 bg-white flex items-center justify-center shadow-sm",
              step.status === 'success' ? "border-emerald-500" :
              step.status === 'failed' ? "border-red-500" :
              step.status === 'skipped' ? "border-amber-500" : "border-slate-400"
            )}>
              {step.status === 'success' && <CheckCircle2 className="w-3 h-3 text-emerald-600 absolute" />}
              {step.status === 'failed' && <XCircle className="w-3 h-3 text-red-500 absolute" />}
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2">
              <div className="flex justify-between items-start gap-2">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">{step.name}</h4>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">{step.tool}</p>
                </div>
                {step.duration_s && (
                  <span className="text-xs text-slate-500">{step.duration_s.toFixed(2)}s</span>
                )}
              </div>

              {step.warnings && step.warnings.length > 0 && (
                <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2 flex items-start gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
                  <ul className="list-disc list-inside">
                    {step.warnings.map((w, j) => <li key={j}>{w}</li>)}
                  </ul>
                </div>
              )}
              
              {step.error && (
                <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded p-2">
                  {step.error}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

