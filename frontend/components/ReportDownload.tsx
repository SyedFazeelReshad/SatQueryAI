'use client';

import { Download } from 'lucide-react';
import { getReport } from '@/lib/api';

interface ReportDownloadProps {
  sessionId: string;
  urls: Record<string, string>;
}

export default function ReportDownload({ sessionId, urls }: ReportDownloadProps) {
  const handleDownload = async (format: 'json' | 'markdown') => {
    try {
      const blob = await getReport(sessionId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${sessionId}.${format === 'markdown' ? 'md' : 'json'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed', err);
      // In a real app we'd show a toast here
    }
  };

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      {urls.json && (
        <button
          onClick={() => handleDownload('json')}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 shadow-sm rounded-lg text-sm font-medium text-slate-700 transition-colors"
        >
          <Download className="w-4 h-4 text-slate-500" />
          JSON Report
        </button>
      )}
      {urls.markdown && (
        <button
          onClick={() => handleDownload('markdown')}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 shadow-sm rounded-lg text-sm font-medium text-slate-700 transition-colors"
        >
          <Download className="w-4 h-4 text-slate-500" />
          Markdown Report
        </button>
      )}
    </div>
  );
}
