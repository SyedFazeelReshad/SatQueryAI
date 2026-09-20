'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { 
  Upload, 
  Layers, 
  GitCompare, 
  FileText, 
  Sparkles, 
  Loader2, 
  AlertCircle,
  X,
  ArrowUp
} from 'lucide-react';

const SUGGESTIONS = {
  single_image: [
    'Describe the land cover in this image.',
    'What type of terrain is visible?',
    'Identify the water bodies in this scene.',
    'Estimate the vegetation coverage.',
  ],
  optical_sar: [
    'Cross-compare optical vegetation with radar backscatter.',
    'Identify flood or moisture extent using SAR.',
    'Assess urban density across optical and SAR bands.',
    'Detect surface roughness and structural features.',
  ],
  change_analysis: [
    'What changed between these two dates?',
    'Has the built-up area increased?',
    'Calculate NDVI & vegetation coverage changes.',
    'Identify areas of deforestation or soil disruption.',
  ],
};

export default function AnalyzePage() {
  const router = useRouter();
  const [tab, setTab] = useState<'single_image' | 'optical_sar' | 'change_analysis'>('single_image');
  
  const [file1, setFile1] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  const [query, setQuery] = useState('Describe the land cover in this image.');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTabChange = (newTab: 'single_image' | 'optical_sar' | 'change_analysis') => {
    setTab(newTab);
    if (newTab === 'single_image') {
      setFile2(null);
      setQuery('Describe the land cover in this image.');
    } else if (newTab === 'optical_sar') {
      setQuery('Cross-compare optical vegetation with radar backscatter.');
    } else {
      setQuery('What changed between these two dates?');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file1) {
      setError('Please upload at least one satellite image.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('files', file1);
    if (file2) {
      formData.append('files', file2);
    }
    formData.append('mode', tab);
    formData.append(
      'query', 
      query.trim() || 'Describe the land cover in this image.'
    );

    try {
      const res = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        let errMsg = 'Failed to analyze satellite scene.';
        if (typeof data.detail === 'string') {
          errMsg = data.detail;
        } else if (Array.isArray(data.detail)) {
          errMsg = data.detail.map((err: any) => `${err.loc?.slice(-1)[0] || 'field'}: ${err.msg}`).join(', ');
        }
        throw new Error(errMsg);
      }

      const result = await res.json();
      // Correct query parameter routing
      router.push(`/analyze/results?session_id=${result.session_id}`);
    } catch (err: any) {
      setError(err.message || 'An error occurred during scene processing.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020612] text-white selection:bg-cyan-500 selection:text-black overflow-x-hidden">
      <Navbar />

      <main className="max-w-4xl mx-auto px-4 pt-28 pb-20 relative z-10">
        {/* Ambient Subtle Glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[550px] h-[300px] bg-cyan-900/15 rounded-full blur-[130px] pointer-events-none" />

        {/* Tab Selection */}
        <div className="flex rounded-xl bg-slate-900/60 p-1 border border-slate-800 backdrop-blur-md mb-8">
          <button
            type="button"
            onClick={() => handleTabChange('single_image')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              tab === 'single_image'
                ? 'bg-slate-800 text-emerald-400 shadow-sm border border-slate-700/60'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Single Image</span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('optical_sar')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              tab === 'optical_sar'
                ? 'bg-slate-800 text-emerald-400 shadow-sm border border-slate-700/60'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Optical + SAR</span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('change_analysis')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              tab === 'change_analysis'
                ? 'bg-slate-800 text-emerald-400 shadow-sm border border-slate-700/60'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <GitCompare className="w-4 h-4" />
            <span>Change Analysis</span>
          </button>
        </div>

        {/* Form Container */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/50 border border-slate-800/90 backdrop-blur-xl shadow-xl">
            <h2 className="text-base font-bold text-white mb-1">
              {tab === 'single_image' ? 'Optical or SAR Image' : 'Imagery Input'}
            </h2>
            <p className="text-xs text-slate-400 mb-6">
              {tab === 'single_image' && 'Upload an optical or SAR satellite scene (PNG, JPG, or GeoTIFF).'}
              {tab === 'optical_sar' && 'Upload complementary optical and radar acquisitions for joint cross-modal synthesis.'}
              {tab === 'change_analysis' && 'Upload baseline (T1) and post-event (T2) scenes for multi-temporal change detection.'}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Image Input 1 */}
              <div className={tab === 'single_image' ? 'md:col-span-2' : ''}>
                {file1 ? (
                  <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-emerald-500/30 bg-slate-950/40 relative">
                    <button
                      type="button"
                      onClick={() => setFile1(null)}
                      className="absolute top-3 right-3 text-slate-400 hover:text-rose-400 p-1 rounded-lg"
                      title="Remove file"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/15 flex items-center justify-center text-emerald-400 mb-3">
                      <FileText className="w-6 h-6" />
                    </div>
                    <p className="text-xs font-semibold text-white truncate max-w-xs">{file1.name}</p>
                    <p className="text-[11px] text-slate-400 mt-1">{(file1.size / 1024).toFixed(2)} KB</p>
                  </div>
                ) : (
                  <label className="flex flex-col items-center justify-center p-10 border-2 border-dashed border-slate-700/80 hover:border-emerald-500/50 rounded-xl cursor-pointer bg-slate-950/40 hover:bg-slate-900/40 transition-all text-center">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-3">
                      <Upload className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-semibold text-white">
                      Click to upload <span className="text-slate-400 font-normal">or drag and drop</span>
                    </span>
                    <span className="text-[11px] text-slate-400 mt-1">GeoTIFF preferred for accurate measurements</span>
                    <input
                      type="file"
                      className="hidden"
                      accept="image/*,.tif,.tiff"
                      onChange={(e) => e.target.files?.[0] && setFile1(e.target.files[0])}
                    />
                  </label>
                )}
              </div>

              {/* Image Input 2 */}
              {tab !== 'single_image' && (
                <div>
{/* removed label */}


                  {file2 ? (
                    <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-emerald-500/30 bg-slate-950/40 relative">
                      <button
                        type="button"
                        onClick={() => setFile2(null)}
                        className="absolute top-3 right-3 text-slate-400 hover:text-rose-400 p-1 rounded-lg"
                      >
                        <X className="w-4 h-4" />
                      </button>
                      <div className="w-12 h-12 rounded-xl bg-teal-500/15 flex items-center justify-center text-teal-400 mb-3">
                        <FileText className="w-6 h-6" />
                      </div>
                      <p className="text-xs font-semibold text-white truncate max-w-xs">{file2.name}</p>
                      <p className="text-[11px] text-slate-400 mt-1">{(file2.size / 1024).toFixed(2)} KB</p>
                    </div>
                  ) : (
                    <label className="flex flex-col items-center justify-center p-10 border-2 border-dashed border-slate-700/80 hover:border-emerald-500/50 rounded-xl cursor-pointer bg-slate-950/40 hover:bg-slate-900/40 transition-all text-center">
                      <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center text-teal-400 mb-3">
                        <Upload className="w-5 h-5" />
                      </div>
                      <span className="text-xs font-semibold text-white">Click to upload second scene</span>
                      <span className="text-[11px] text-slate-400 mt-1">GeoTIFF, PNG, JPG</span>
                      <input
                        type="file"
                        className="hidden"
                        accept="image/*,.tif,.tiff"
                        onChange={(e) => e.target.files?.[0] && setFile2(e.target.files[0])}
                      />
                    </label>
                  )}
                </div>
              )}
            </div>

            {/* Query Section */}
            <div className="mt-8 text-left">
              <label className="flex items-center gap-2 text-xs font-semibold text-emerald-400 mb-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Natural Language Query</span>
              </label>
              
              <div className="relative">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  maxLength={500}
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl bg-slate-950/60 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/80 transition-colors resize-none pr-16"
                />
                <span className="absolute bottom-3 right-3 text-[11px] text-slate-500 font-mono">
                  {query.length} / 500
                </span>
              </div>

              {/* Dynamic Suggestions based on active Tab */}
              <div className="mt-3 flex flex-wrap gap-2 items-center text-[11px] text-slate-400">
                <span className="text-slate-500 font-medium">Examples:</span>
                {SUGGESTIONS[tab].map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setQuery(sample)}
                    className="px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition-colors"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="mt-6 p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <div className="mt-8 flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 px-7 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-[0_0_20px_rgba(16,185,129,0.35)] hover:shadow-[0_0_28px_rgba(16,185,129,0.6)] transition-all disabled:opacity-50 disabled:pointer-events-none"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <span>Analyze</span>
                    <ArrowUp className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}
