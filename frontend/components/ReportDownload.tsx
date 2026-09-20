'use client';

import { Download } from 'lucide-react';

interface ReportDownloadProps {
  sessionId: string;
  urls?: Record<string, string>;
  result?: any;
}

export default function ReportDownload({ sessionId, urls = {}, result }: ReportDownloadProps) {
  const handleDownload = (format: 'json' | 'markdown') => {
    if (format === 'json') {
      const payload = result || { session_id: sessionId, status: 'completed' };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SatQuery_${sessionId}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } else {
      let md = `# SatQuery Analysis Report: ${sessionId}\n\n`;
      md += `**Task Type:** ${result?.task_type || 'Geospatial Analysis'}\n`;
      md += `**Confidence:** ${result?.confidence_level || 'medium'} (${result?.confidence || 0.8})\n\n`;
      md += `## Answer\n${result?.answer || 'Analysis complete.'}\n\n`;
      md += `## Measurements\n`;
      if (result?.measurements && result.measurements.length) {
        result.measurements.forEach((m: any) => {
          md += `- **${m.label}:** ${m.value} ${m.unit || ''} (${m.evidence_type || 'DERIVED'})\n`;
        });
      }
      if (result?.warnings && result.warnings.length) {
        md += `\n## Warnings\n`;
        result.warnings.forEach((w: string) => {
          md += `- ${w}\n`;
        });
      }
      const blob = new Blob([md], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SatQuery_${sessionId}.md`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <button
        onClick={() => handleDownload('json')}
        type="button"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-700/60 hover:border-cyan-500/50 text-xs font-medium text-slate-300 hover:text-white transition-all shadow-sm active:scale-95"
      >
        <Download className="w-3.5 h-3.5 text-cyan-400" />
        JSON Report
      </button>

      <button
        onClick={() => handleDownload('markdown')}
        type="button"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-700/60 hover:border-emerald-500/50 text-xs font-medium text-slate-300 hover:text-white transition-all shadow-sm active:scale-95"
      >
        <Download className="w-3.5 h-3.5 text-emerald-400" />
        Markdown Report
      </button>
    </div>
  );
}
