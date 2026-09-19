'use client';

import React from 'react';

interface ResultPanelProps {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export default function ResultPanel({ title, icon, children, className = '' }: ResultPanelProps) {
  return (
    <div className={`rounded-2xl bg-[#090f1f]/80 border border-slate-800/80 backdrop-blur-xl shadow-xl overflow-hidden ${className}`}>
      {/* Sleek Dark Header */}
      <div className="flex items-center gap-2.5 px-6 py-4 bg-[#0d162d]/90 border-b border-slate-800/80">
        {icon && <span className="text-emerald-400">{icon}</span>}
        <h2 className="text-sm sm:text-base font-bold text-white tracking-wide">{title}</h2>
      </div>
      {/* Body */}
      <div className="p-6">{children}</div>
    </div>
  );
}
