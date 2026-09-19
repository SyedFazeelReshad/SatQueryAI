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
import { AlertCircle, Loader2, RefreshCcw, ArrowLeft, MessageSquare, Sparkles } from 'lucide-react';

/** Renders markdown content with GFM (tables, bold, lists, headings). */
function MarkdownAnswer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h2: ({ children }) => <h2 className="text-base font-bold text-slate-900 mt-4 mb-1 border-b border-slate-200 pb-1">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-semibold text-slate-800 mt-3 mb-1">{children}</h3>,
        strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
        p: ({ children }) => <p className="text-sm text-slate-700 leading-relaxed mb-2">{children}</p>,
        li: ({ children }) => <li className="text-sm text-slate-700 ml-4 list-disc mb-0.5">{children}</li>,
        table: ({ children }) => (
          <div className="overflow-x-auto my-3">
            <table className="min-w-full text-xs border border-slate-200 rounded-lg overflow-hidden">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-slate-100 text-slate-700 font-medium">{children}</thead>,
        tbody: ({ children }) => <tbody className="divide-y divide-slate-100">{children}</tbody>,
        tr: ({ children }) => <tr className="hover:bg-slate-50">{children}</tr>,
        th: ({ children }) => <th className="px-3 py-2 text-left font-semibold text-slate-800">{children}</th>,
        td: ({ children }) => <td className="px-3 py-2 text-slate-700">{children}</td>,
        hr: () => <hr className="my-3 border-slate-200" />,
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
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400 gap-4 py-20">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        <p>Retrieving analysis results...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 py-20">
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-xl max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-8 h-8 mx-auto" />
          <p>{error || 'Result not found'}</p>
          <Link
            href="/analyze"
            className="inline-block mt-4 text-white bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded border border-slate-700"
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
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div className="space-y-2">
          <Link
            href="/analyze"
            className="text-sm text-slate-500 hover:text-slate-900 flex items-center gap-1 mb-2 w-fit transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Analysis
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Analysis Report</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
              Stage 3 Multi-Modal
            </span>
          </div>
          <div className="flex items-center gap-3 pt-1">
            <span className="text-xs font-mono text-slate-600 bg-white border border-slate-200 px-2.5 py-1 rounded shadow-sm">
              Session: {sessionId}
            </span>
            <ConfidenceBadge score={result.confidence} level={result.confidence_level} />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ReportDownload sessionId={result.session_id} urls={result.report_urls} />
          <Link
            href="/analyze"
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-md shadow-emerald-600/20"
          >
            <RefreshCcw className="w-4 h-4" />
            New Analysis
          </Link>
        </div>
      </div>

      {/* Warnings Banner if any */}
      {result.warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-amber-600" />
          <div className="space-y-1 text-sm">
            <p className="font-semibold text-amber-900">Observation Warnings</p>
            <ul className="list-disc list-inside space-y-0.5 text-xs text-amber-800">
              {result.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Column (Left 2 cols) */}
        <div className="lg:col-span-2 space-y-8">
          {/* VLM Synthesized Answer */}
          <ResultPanel
            title="Analysis Interpretation"
            icon={<MessageSquare className="w-5 h-5 text-emerald-600" />}
          >
            <div className="prose prose-slate prose-sm max-w-none text-slate-800 leading-relaxed
              prose-headings:text-slate-900 prose-headings:font-bold
              prose-h2:text-base prose-h3:text-sm
              prose-strong:text-slate-900
              prose-table:text-xs prose-td:py-1 prose-th:py-1
              prose-li:text-slate-700">
              <MarkdownAnswer content={result.answer} />
            </div>
          </ResultPanel>

          {/* Interactive Multi-Layer Visualizer */}
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
              <div className="mt-3 p-3 rounded-lg bg-indigo-50 border border-indigo-200 text-xs text-indigo-900 flex items-center justify-between">
                <span>
                  Selected Object: <strong>{selectedDetection.label}</strong> (Confidence:{' '}
                  {Math.round(selectedDetection.score * 100)}%)
                </span>
                <button
                  onClick={() => setSelectedDetection(null)}
                  className="text-[11px] underline hover:text-indigo-950 font-medium"
                >
                  Clear Selection
                </button>
              </div>
            )}
          </ResultPanel>


          {/* Conversational Follow-Up Exploration */}
          <FollowUpChat sessionId={result.session_id} />

          {/* Evidence Verification Panel */}
          <EvidencePanel evidenceIds={result.evidence_ids} />
        </div>

        {/* Side Column (Right 1 col) */}
        <div className="space-y-8">
          {/* Measurements Card */}
          {result.measurements.length > 0 && (
            <ResultPanel title="Deterministic Measurements">
              <div className="space-y-3">
                {result.measurements.map((m, i) => (
                  <MeasurementCard key={i} measurement={m} />
                ))}
              </div>
            </ResultPanel>
          )}

          {/* Execution Trace DAG */}
          <ExecutionTracePanel traceId={result.execution_trace_id} />
        </div>
      </div>
    </main>
  );
}

export default function ResultsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc] text-slate-900">
      <Navbar />

      <Suspense
        fallback={
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400 gap-4 py-20">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
            <p>Loading results...</p>
          </div>
        }
      >
        <ResultsContent />
      </Suspense>
    </div>
  );
}
