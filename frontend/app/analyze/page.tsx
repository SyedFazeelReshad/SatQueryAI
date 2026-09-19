'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import AnalysisTabs from '@/components/AnalysisTabs';
import UploadCard from '@/components/UploadCard';
import QueryInput from '@/components/QueryInput';
import { AnalysisMode } from '@/types/analysis';
import { analyzeImage } from '@/lib/api';
import { Loader2, AlertCircle } from 'lucide-react';

const EXAMPLES = {
  single_image: [
    "Describe the land cover in this image.",
    "What type of terrain is visible?",
    "Identify the water bodies in this scene.",
    "Estimate the vegetation coverage."
  ],
  optical_sar: [
    "Identify built-up and water-covered regions using both images.",
    "Compare structural features visible in SAR with the optical image."
  ],
  change_analysis: [
    "What changed between these two dates?",
    "Has the built-up area increased?",
    "Describe the land cover changes.",
    "Identify areas of deforestation."
  ]
};

export default function AnalyzePage() {
  const router = useRouter();
  const [mode, setMode] = useState<AnalysisMode>('single_image');
  const [query, setQuery] = useState('');
  
  const [file1, setFile1] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!query) {
      setError("Please enter a query.");
      return;
    }
    if (!file1) {
      setError("Please upload the required imagery.");
      return;
    }
    if (mode !== 'single_image' && !file2) {
      setError("Please upload the second image required for this analysis mode.");
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('mode', mode);
    formData.append('query', query);
    formData.append('files', file1);
    if (file2) formData.append('files', file2);

    try {
      const result = await analyzeImage(formData);
      router.push(`/analyze/results?session_id=${result.session_id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      let errorMsg = Array.isArray(detail)
        ? detail.map((e: any) => e.msg || String(e)).join(', ')
        : typeof detail === 'string'
        ? detail
        : err.message || "An error occurred during analysis.";
      
      if (err.message === 'Network Error' || err.code === 'ERR_NETWORK') {
        errorMsg = "Network Error: Could not connect to backend at http://localhost:8000. Please ensure the Python FastAPI backend is running.";
      }
      setError(errorMsg);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc] text-slate-900">
      <Navbar />
      <main className="flex-1 w-full max-w-4xl mx-auto px-4 py-8 md:py-12 flex flex-col gap-8">
        
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">New Analysis</h1>
          <p className="text-slate-600">Upload your satellite imagery and ask questions in natural language.</p>
        </div>

        <AnalysisTabs mode={mode} onChange={(m) => { setMode(m); setError(null); }} />

        <div className="bg-white border border-slate-200 rounded-2xl p-6 md:p-8 space-y-8 shadow-sm">
          
          {/* Upload Section */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-900">Imagery Input</h2>
            
            {mode === 'single_image' && (
              <UploadCard 
                label="Optical or SAR Image" 
                accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg" 
                description="GeoTIFF preferred for accurate measurements"
                onFile={setFile1} 
              />
            )}

            {mode === 'optical_sar' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UploadCard 
                  label="Optical Image (e.g., Sentinel-2)" 
                  accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg" 
                  onFile={setFile1} 
                />
                <UploadCard 
                  label="SAR Image (e.g., Sentinel-1)" 
                  accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg" 
                  onFile={setFile2} 
                />
              </div>
            )}

            {mode === 'change_analysis' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UploadCard 
                  label="Image Date A (Before)" 
                  accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg" 
                  onFile={setFile1} 
                />
                <UploadCard 
                  label="Image Date B (After)" 
                  accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg" 
                  onFile={setFile2} 
                />
              </div>
            )}
          </div>

          <div className="h-px bg-slate-200 w-full" />

          {/* Query Section */}
          <QueryInput 
            value={query} 
            onChange={setQuery} 
            examples={EXAMPLES[mode]} 
            disabled={isLoading}
          />

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-red-600" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-3 rounded-xl font-semibold transition-all shadow-md shadow-emerald-600/20 hover:shadow-emerald-600/30 disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Analyze &uarr;
                </>
              )}
            </button>
          </div>

        </div>
      </main>
    </div>
  );

}
