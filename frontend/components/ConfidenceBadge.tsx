'use client';

import clsx from 'clsx';
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

interface ConfidenceBadgeProps {
  score: number | null;
  level: string;
  basis?: string | null;
}

export default function ConfidenceBadge({ score, level, basis }: ConfidenceBadgeProps) {
  return null;
  const getStyle = () => {
    if (!score) return "bg-slate-100 text-slate-700 border-slate-300";
    if (score >= 0.8) return "bg-emerald-50 text-emerald-700 border-emerald-200";
    if (score >= 0.5) return "bg-amber-50 text-amber-700 border-amber-200";
    return "bg-rose-50 text-rose-700 border-rose-200";
  };

  const Icon = () => {
    if (!score) return <Shield className="w-4 h-4" />;
    if (score >= 0.8) return <ShieldCheck className="w-4 h-4" />;
    if (score >= 0.5) return <ShieldAlert className="w-4 h-4" />;
    return <ShieldAlert className="w-4 h-4" />;
  };

  return (
    <div className="group relative inline-block">
      <div className={clsx("inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold shadow-xs", getStyle())}>
        <Icon />
        {level} {score && `(${Math.round(score * 100)}%)`}
      </div>
      
      {basis && (
        <div className="opacity-0 invisible group-hover:opacity-100 group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-white border border-slate-200 p-3 rounded-lg shadow-xl text-xs text-slate-600 z-10 transition-all">
          <p className="font-semibold text-slate-900 mb-1">Confidence Basis</p>
          {basis}
        </div>
      )}
    </div>
  );
}
