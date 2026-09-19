'use client';

import clsx from 'clsx';
import { Sparkles } from 'lucide-react';

interface QueryInputProps {
  value: string;
  onChange: (val: string) => void;
  examples: string[];
  disabled?: boolean;
}

export default function QueryInput({ value, onChange, examples, disabled }: QueryInputProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-emerald-600" />
        Natural Language Query
      </label>
      
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="Ask a question about this satellite image..."
          className="w-full h-32 bg-white border border-slate-300 rounded-xl p-4 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed shadow-sm text-sm"
        />
        <div className="absolute bottom-3 right-3 text-xs text-slate-400">
          {value.length} / 500
        </div>
      </div>

      {examples.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-slate-500 py-1 font-medium">Examples:</span>
          {examples.map((ex, i) => (
            <button
              key={i}
              onClick={() => onChange(ex)}
              disabled={disabled}
              className="text-xs px-3 py-1 bg-slate-50 border border-slate-200 rounded-full text-slate-700 hover:text-slate-900 hover:bg-slate-100 hover:border-slate-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>

  );
}
