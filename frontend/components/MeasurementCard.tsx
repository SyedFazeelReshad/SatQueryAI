'use client';

import clsx from 'clsx';
import { MeasurementResult } from '@/types/analysis';
import { Ruler } from 'lucide-react';

interface MeasurementCardProps {
  measurement: MeasurementResult;
}

export default function MeasurementCard({ measurement }: MeasurementCardProps) {
  const getBadgeStyle = (type: string) => {
    const t = type.toUpperCase();
    if (t === 'OBSERVED') return 'bg-blue-50 text-blue-700 border-blue-200';
    if (t === 'DERIVED') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (t === 'DETECTED') return 'bg-amber-50 text-amber-700 border-amber-200';
    if (t === 'AI_DETECTED') return 'bg-purple-50 text-purple-700 border-purple-200';
    if (t === 'INFERRED') return 'bg-orange-50 text-orange-700 border-orange-200';
    if (t === 'SYNTHETIC') return 'bg-rose-50 text-rose-700 border-rose-200';
    return 'bg-slate-100 text-slate-600 border-slate-200';
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col gap-3 hover:border-slate-300 transition-colors">
      <div className="flex justify-between items-start gap-2">
        <span className="text-sm font-medium text-slate-700">{measurement.label}</span>
        <span className={clsx("text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider", getBadgeStyle(measurement.evidence_type))}>
          {measurement.evidence_type}
        </span>
      </div>
      <div className="flex items-baseline gap-1 mt-auto">
        <span className="text-2xl font-bold text-slate-900">{measurement.value}</span>
        <span className="text-sm text-slate-500 font-medium">{measurement.unit}</span>
      </div>
    </div>
  );
}

