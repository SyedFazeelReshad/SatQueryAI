'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, FileSearch, CheckCircle2, AlertCircle } from 'lucide-react';
import { EvidenceRecord } from '@/types/evidence';
import { getEvidence } from '@/lib/api';
import clsx from 'clsx';

interface EvidencePanelProps {
  evidenceIds: string[];
}

export default function EvidencePanel({ evidenceIds }: EvidencePanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (expanded && evidence.length === 0 && evidenceIds.length > 0) {
      setLoading(true);
      Promise.all(evidenceIds.map(id => getEvidence(id).catch(() => null)))
        .then(results => {
          setEvidence(results.filter((r): r is EvidenceRecord => r !== null));
        })
        .finally(() => setLoading(false));
    }
  }, [expanded, evidenceIds, evidence.length]);

  if (evidenceIds.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <FileSearch className="w-5 h-5 text-emerald-600" />
          <span className="font-semibold text-slate-900">Evidence Records ({evidenceIds.length})</span>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500" />}
      </button>

      {expanded && (
        <div className="p-4 border-t border-slate-200 bg-slate-50/50 space-y-4">
          {loading ? (
            <div className="text-center py-4 text-sm text-slate-500 animate-pulse">Loading evidence...</div>
          ) : evidence.map(record => (
            <div key={record.evidence_id} className="bg-white border border-slate-200 rounded-lg p-4 space-y-3 shadow-sm">
              
              <div className="flex justify-between items-start gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">{record.evidence_id.split('-')[0]}</span>
                  <span className="text-sm font-semibold text-slate-900">{record.task}</span>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider bg-slate-100 text-slate-700 border-slate-200">
                  {record.evidence_type}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-500">Tool:</span> <span className="text-slate-700 font-medium">{record.tool}</span>
                </div>
                <div>
                  <span className="text-slate-500">Model:</span> <span className="text-slate-700 font-medium">{record.model || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500">Source:</span> <span className="text-slate-700 font-medium truncate block">{record.source_image}</span>
                </div>
                {record.confidence && (
                  <div>
                    <span className="text-slate-500">Confidence:</span> <span className="text-slate-700 font-medium">{(record.confidence * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>

              {record.warnings && record.warnings.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded text-amber-800 text-xs p-2 flex items-start gap-2 mt-2">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
                  <ul className="list-disc list-inside space-y-0.5">
                    {record.warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}

            </div>
          ))}
        </div>
      )}
    </div>
  );

}
