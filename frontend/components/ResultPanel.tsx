'use client';

import { ReactNode } from 'react';

interface ResultPanelProps {
  title: string;
  children: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
}

export default function ResultPanel({ title, children, icon, action }: ResultPanelProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          {icon}
          {title}
        </h2>
        {action && <div>{action}</div>}
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  );
}

