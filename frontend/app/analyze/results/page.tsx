'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Navbar from '@/components/Navbar';
import { InteractiveVisualizer } from '@/components/InteractiveVisualizer';
import { FollowUpChat } from '@/components/FollowUpChat';
import MeasurementCard from '@/components/MeasurementCard';
import ConfidenceBadge from '@/components/ConfidenceBadge';
import EvidencePanel from '@/components/EvidencePanel';
import ExecutionTracePanel from '@/components/ExecutionTrace';
import ReportDownload from '@/components/ReportDownload';
import ResultPanel from '@/components/ResultPanel';
import { AnalysisResult, DetectionResult } from '@/types/analysis';
import { getResult } from '@/lib/api';
import { AlertCircle, Loader2, RefreshCcw, ArrowLeft, MessageSquare } from 'lucide-react';

function MarkdownAnswer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h2: ({ children }) => <h2 className="text-base font-bold text-white mt-4 mb-2 border-b border-slate-700 pb-1">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-semibold text-emerald-400 mt-3 mb-1">{children}</h3>,
        strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
        p: ({ children }) => <p className="text-sm text-slate-200 leading-relaxed mb-2">{children}</p>,
        li: ({ children }) => <li className="text-sm text-slate-200 ml-4 list-disc mb-0.5">{children}</li>,
        table: ({ children }) => (
          <div className="overflow-x-auto my-3 border border-slate-700 rounded-lg">
            <table className="min-w-full text-xs text-slate-200">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-slate-800 text-white font-semibold">{children}</thead>,
        tbody: ({ children }) => <tbody className="divide-y divide-slate-800">{children}</tbody>,
        tr: ({ children }) => <tr className="hover:bg-slate-800/50">{children}</tr>,
        th: ({ children }) => <th className="px-3 py-2 text-left font-semibold text-white">{children}</th>,
        td: ({ children }) => <td className="px-3 py-2 text-slate-200">{children}</td>,
        hr: () => <hr className="my-3 border-slate-700" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function ResultsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get('session_id');

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDetection, setSelectedDetection] = useState<DetectionResult | null>(null);

  useEffect(() => {
    if (!sessionId) {
      router.push('/analyze');
      return;
    }

    setLoading(true);
    getResult(sessionId)
      .then(setResult)
      .catch((err) => {
        const detail = err.response?.data?.detail;
        const errorMsg = Array.isArray(detail)
          ? detail.map((e: any) => e.msg || String(e)).join(', ')
          : typeof detail === 'string'
          ? detail
          : err.message || 'Failed to load results';
        setError(errorMsg);
      })
      .finally(() => setLoading(false));
  }, [sessionId, router]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-slate-300 gap-4 py-32">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        <p className="text-sm font-medium">Retrieving analysis results...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 py-32">
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 p-6 rounded-xl max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-8 h-8 mx-auto text-red-400" />
          <p className="text-sm">{error || 'Result not found'}</p>
          <Link
            href="/analyze"
            className="inline-block mt-4 text-white bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg border border-slate-700 text-xs font-semibold"
          >
            Go Back
          </Link>
        </div>
      </div>
    );
  }

  return (
    <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-8 md:py-12 space-y-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-slate-800 pb-6">
        <div className="space-y-2">
          <Link
            href="/analyze"
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1 mb-2 w-fit transition-colors font-medium"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Analysis
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Analysis Report</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold">
              Stage 3 Multi-Modal
            </span>
          </div>
          <div className="flex items-center gap-3 pt-1">
            <span className="text-xs font-mono text-slate-300 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded">
              Session: {sessionId}
            </span>
            <ConfidenceBadge score={result.confidence} level={result.confidence_level} />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ReportDownload sessionId={result.session_id} urls={result.report_urls} />
          <Link
            href="/analyze"
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-md shadow-emerald-900/40"
          >
            <RefreshCcw className="w-3.5 h-3.5" />
            New Analysis
          </Link>
        </div>
      </div>

      {/* Observation Warnings */}
      {result.warnings.length > 0 && (
        <div className="bg-amber-950/40 border border-amber-500/40 rounded-xl p-4 text-amber-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-amber-400" />
          <div className="space-y-1 text-sm">
            <p className="font-bold text-amber-300">Observation Warnings</p>
            <ul className="list-disc list-inside space-y-0.5 text-xs text-amber-200/90">
              {result.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-8">
          <ResultPanel
            title="Analysis Interpretation"
            icon={<MessageSquare className="w-5 h-5 text-emerald-400" />}
          >
            <div className="prose prose-invert max-w-none text-slate-200 leading-relaxed">
              <MarkdownAnswer content={result.answer} />
            </div>
          </ResultPanel>

          <ResultPanel title="Multi-Layer Imagery & Visualizer">
            <InteractiveVisualizer
              previewUrl={result.preview_url}
              previewBUrl={result.preview_b_url}
              overlayUrl={result.overlay_url}
              layers={result.layers}
              detections={result.detections}
              onSelectDetection={(det) => setSelectedDetection(det)}
            />
            {selectedDetection && (
              <div className="mt-3 p-3 rounded-lg bg-indigo-950/50 border border-indigo-500/30 text-xs text-indigo-300 flex items-center justify-between">
                <span>
                  Selected Object: <strong className="text-white">{selectedDetection.label}</strong> (Confidence: {Math.round(selectedDetection.score * 100)}%)
                </span>
                <button
                  onClick={() => setSelectedDetection(null)}
                  className="text-[11px] underline hover:text-white"
                >
                  Clear Selection
                </button>
              </div>
            )}
          </ResultPanel>

          <FollowUpChat sessionId={result.session_id} />

          <EvidencePanel evidenceIds={result.evidence_ids} />
        </div>

        {/* Side Column */}
        <div className="lg:col-span-1 space-y-8">
          {result.measurements.length > 0 && (
            <ResultPanel title="Deterministic Measurements">
              <div className="space-y-3">
                {result.measurements.map((m, i) => (
                  <MeasurementCard key={i} measurement={m} />
                ))}
              </div>
            </ResultPanel>
          )}

          <ExecutionTracePanel traceId={result.execution_trace_id} />
        </div>
      </div>
    </main>
  );
}

export default function ResultsPage() {
  return (
    <div className="results-page min-h-screen flex flex-col bg-[#020612] text-white">
      <Navbar />
      <div className="pt-16">
        <Suspense
          fallback={
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 gap-4 py-32">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
              <p className="text-sm">Loading results...</p>
            </div>
          }
        >
          <ResultsContent />
        </Suspense>
      </div>
    </div>
  );
}
