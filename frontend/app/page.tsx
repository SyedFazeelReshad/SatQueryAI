'use client';

import React from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import DynamicEarthScene from '@/components/DynamicEarthScene';
import { 
  ArrowRight, 
  Sparkles, 
  ShieldCheck, 
  Layers, 
  Cpu, 
  Activity,
  Compass,
  CheckCircle2,
  FileCheck2,
  Lock,
  Globe2,
  BarChart3
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#020612] text-white selection:bg-cyan-500 selection:text-black overflow-x-hidden">
      <Navbar />

      {/* Hero Section with 3D Earth */}
      <section className="relative min-h-screen flex items-center justify-center pt-24 pb-16 px-4 overflow-hidden">
        <DynamicEarthScene />

        <div className="absolute inset-0 bg-gradient-to-t from-[#020612] via-transparent to-[#020612]/70 pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-400 text-xs font-semibold backdrop-blur-md shadow-[0_0_15px_rgba(6,182,212,0.25)]">
            <Sparkles className="w-3.5 h-3.5 animate-pulse" />
            <span>Student Innovation Project • Smart India Hackathon (SIH26167)</span>
          </div>

          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight leading-[1.1]">
            <span className="text-white block">Every satellite pixel holds</span>
            <span className="block bg-gradient-to-r from-cyan-300 via-teal-300 to-emerald-400 bg-clip-text text-transparent drop-shadow-[0_0_35px_rgba(6,182,212,0.5)]">
              insights for a fast,
            </span>
            <span className="block bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-300 bg-clip-text text-transparent drop-shadow-[0_0_35px_rgba(16,185,129,0.5)]">
              verified decision
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed drop-shadow-md">
            SatQuery AI turns raw optical, SAR, and multispectral satellite imagery into instant, verified environmental intelligence — answering natural language queries with zero fabrication and strict mathematical rigor.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              href="/analyze"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-sm shadow-[0_0_25px_rgba(16,185,129,0.4)] hover:shadow-[0_0_35px_rgba(16,185,129,0.6)] hover:scale-105 transition-all"
            >
              <span>Analyze a Satellite Scene</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#how-it-works"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 border border-slate-700/80 text-sm font-semibold backdrop-blur-md transition-all hover:border-slate-600"
            >
              See How It Works
            </a>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-6 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Sentinel-2 Multispectral (10m)
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> Sentinel-1 SAR Radar Fusion
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" /> Zero Hallucination Guaranteed
            </span>
          </div>

          <p className="pt-2 text-[11px] font-mono text-slate-500 flex items-center justify-center gap-2 tracking-widest uppercase">
            <Compass className="w-3.5 h-3.5 text-cyan-400 animate-spin" style={{ animationDuration: '12s' }} />
            <span>Drag anywhere to rotate Earth • Active orbit telemetry</span>
          </p>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 px-4 max-w-7xl mx-auto relative z-10 border-t border-slate-900">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <h2 className="text-xs font-mono uppercase tracking-widest text-emerald-400">End-to-End Pipeline</h2>
          <h3 className="text-3xl font-extrabold text-white">How SatQuery Delivers Verified Intelligence</h3>
          <p className="text-sm text-slate-400">
            A three-stage verified decision system that eliminates hallucination from remote sensing queries.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-8 rounded-2xl bg-slate-900/50 border border-slate-800/80 backdrop-blur-xl hover:border-slate-700 transition-all">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-6 font-mono font-bold text-lg">
              01
            </div>
            <h4 className="text-lg font-bold text-white mb-2">Ingestion & Indexing</h4>
            <p className="text-sm text-slate-400 leading-relaxed">
              Accepts GeoTIFF, PNG, and JPG rasters across optical (Sentinel-2) and SAR (Sentinel-1) modalities with automated georeferencing and CRS alignment.
            </p>
          </div>

          <div className="p-8 rounded-2xl bg-slate-900/50 border border-slate-800/80 backdrop-blur-xl hover:border-slate-700 transition-all">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-6 font-mono font-bold text-lg">
              02
            </div>
            <h4 className="text-lg font-bold text-white mb-2">Deterministic Calculation</h4>
            <p className="text-sm text-slate-400 leading-relaxed">
              Computes physical indices (NDVI, NDWI, CVA change masks) on pixel arrays before invoking language models. The vision model sees raw ground truth.
            </p>
          </div>

          <div className="p-8 rounded-2xl bg-slate-900/50 border border-slate-800/80 backdrop-blur-xl hover:border-slate-700 transition-all">
            <div className="w-12 h-12 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-400 mb-6 font-mono font-bold text-lg">
              03
            </div>
            <h4 className="text-lg font-bold text-white mb-2">Grounded Synthesis</h4>
            <p className="text-sm text-slate-400 leading-relaxed">
              Generates calibrated natural-language reports with confidence scoring, evidence hashes, and downloadable audit-ready PDF/Markdown exports.
            </p>
          </div>
        </div>
      </section>

      {/* Core Capabilities Section (The 5 Feature Cards) */}
      <section id="capabilities" className="py-24 px-4 max-w-7xl mx-auto relative z-10 border-t border-slate-900">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <h2 className="text-xs font-mono uppercase tracking-widest text-cyan-400">Platform Features</h2>
          <h3 className="text-3xl font-extrabold text-white">Built for High-Stakes Earth Observation</h3>
          <p className="text-sm text-slate-400">
            Five core capabilities distinguishing SatQuery from generic multimodal AI platforms.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-7 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-emerald-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-5">
              <Layers className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white mb-2">Optical + SAR Cross-Modal Fusion</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Combines cloud-penetrating radar backscatter with multi-spectral optical reflectance to eliminate all-weather visibility blind spots.
            </p>
          </div>

          <div className="p-7 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-cyan-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-5">
              <Activity className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white mb-2">Change Vector Analysis (CVA)</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Detects bi-temporal changes between multi-year acquisitions with Otsu thresholding and exact area quantification in km².
            </p>
          </div>

          <div className="p-7 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-teal-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center mb-5">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white mb-2">Mathematical Ground Truth</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every numerical claim in the report is cross-checked against exact raster indices. Hallucinated figures are filtered deterministically.
            </p>
          </div>

          <div className="p-7 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-indigo-500/40 transition-all md:col-span-2">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-5">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white mb-2">Calibrated Confidence & Traceability</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every pipeline run emits an execution trace DAG with stage-level verification hashes, giving defense, disaster, and agricultural teams full auditable provenance.
            </p>
          </div>

          <div className="p-7 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-sky-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center mb-5">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white mb-2">Audit-Ready Export</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Instantly export multi-spectral intelligence briefs into reproducible Markdown and JSON packages for mission ops.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-900/90 text-center text-xs text-slate-500">
        <p>SatQuery AI • Remote Sensing Decision Intelligence • SIH26167</p>
      </footer>
    </div>
  );
}
