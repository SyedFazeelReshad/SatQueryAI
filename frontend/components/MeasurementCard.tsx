'use client';

import React from 'react';
import { Measurement } from '@/types/analysis';

export default function MeasurementCard({ measurement }: { measurement: Measurement }) {
  return (
    <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all shadow-sm">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold text-slate-300">
          {measurement.metric_name || (measurement as any).name || (measurement as any).label}
        </span>
        {measurement.category && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-800/40 uppercase tracking-wider font-semibold">
            {measurement.category}
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-1.5 mt-1">
        <span className="text-2xl font-black tracking-tight text-white">{measurement.value}</span>
        {measurement.unit && (
          <span className="text-xs font-medium text-emerald-400">{measurement.unit}</span>
        )}
      </div>
      {measurement.interpretation && (
        <p className="text-[11px] text-slate-400 mt-2 leading-relaxed border-t border-slate-800/60 pt-2">
          {measurement.interpretation}
        </p>
      )}
    </div>
  );
}
