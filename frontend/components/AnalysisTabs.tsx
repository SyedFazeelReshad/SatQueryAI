'use client';

import clsx from 'clsx';
import { AnalysisMode } from '@/types/analysis';
import { FileImage, Layers, Activity } from 'lucide-react';

interface AnalysisTabsProps {
  mode: AnalysisMode;
  onChange: (mode: AnalysisMode) => void;
}

export default function AnalysisTabs({ mode, onChange }: AnalysisTabsProps) {
  const tabs = [
    { id: 'single_image', label: 'Single Image', icon: <FileImage className="w-4 h-4" /> },
    { id: 'optical_sar', label: 'Optical + SAR', icon: <Layers className="w-4 h-4" /> },
    { id: 'change_analysis', label: 'Change Analysis', icon: <Activity className="w-4 h-4" /> },
  ] as const;

  return (
    <div className="flex p-1 bg-slate-100 border border-slate-200 rounded-xl">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id as AnalysisMode)}
          className={clsx(
            "flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all",
            mode === tab.id 
              ? "bg-white text-slate-900 shadow-sm border border-slate-200 font-semibold" 
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
          )}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
}

