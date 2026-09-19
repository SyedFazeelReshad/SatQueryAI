'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { 
  Upload, 
  BrainCircuit, 
  CheckCircle2, 
  Globe2, 
  Send, 
  Activity, 
  Layers, 
  Search, 
  Compass, 
  Sparkles, 
  BarChart3, 
  ArrowRight, 
  ShieldCheck, 
  Database, 
  Satellite, 
  FileText, 
  ArrowUp,
  Mail,
  MapPin,
  Phone,
  Twitter,
  Instagram,
  Linkedin
} from 'lucide-react';
import Navbar from '@/components/Navbar';

export default function LandingPage() {
  const router = useRouter();

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col selection:bg-emerald-500 selection:text-white">
      <Navbar />

      <main className="flex-1 w-full">
        {/* ========================================================= */}
        {/* 1. HERO SECTION (Light Mode Match)                        */}
        {/* ========================================================= */}
        <section id="hero" className="relative pt-12 pb-20 md:pt-20 md:pb-28 bg-white border-b border-slate-200 overflow-hidden">
          {/* Subtle ambient glow */}
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
          
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <div className="space-y-8 flex flex-col items-center">
              
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 shadow-sm">
                <Sparkles className="w-4 h-4 text-emerald-600" />
                <span>Student Innovation Project · Smart India Hackathon (SIH26167)</span>
              </div>

              {/* Main Heading */}
              <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight leading-[1.15] text-slate-900 max-w-4xl mx-auto">
                Every satellite pixel holds insights for a{' '}
                <span className="text-emerald-600">fast, verified</span> decision
              </h1>

              {/* Subtitle */}
              <p className="text-base sm:text-xl text-slate-600 leading-relaxed max-w-3xl mx-auto">
                SatQuery AI turns raw optical, SAR, and multispectral satellite imagery into instant, verified environmental intelligence — answering natural language queries with zero fabrication and strict mathematical rigor.
              </p>

              {/* Buttons */}
              <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
                <Link
                  href="/analyze"
                  className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-8 py-4 rounded-xl transition-all shadow-lg shadow-emerald-600/20 hover:shadow-emerald-600/30 text-base sm:text-lg"
                >
                  <span>Analyze a Satellite Scene</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  href="#how-it-works"
                  className="inline-flex items-center justify-center bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-medium px-8 py-4 rounded-xl transition-colors shadow-sm text-base sm:text-lg"
                >
                  See How It Works
                </Link>
              </div>

              {/* Feature Highlights Pill Bar */}
              <div className="pt-6 flex flex-wrap items-center justify-center gap-3 text-xs text-slate-600">
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-50 border border-slate-200 shadow-sm">
                  <Satellite className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Sentinel-2 Multispectral (10m)</span>
                </div>
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-50 border border-slate-200 shadow-sm">
                  <Layers className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Sentinel-1 SAR Radar Fusion</span>
                </div>
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-50 border border-slate-200 shadow-sm">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Zero Hallucination Guaranteed</span>
                </div>
              </div>

            </div>
          </div>
        </section>


        {/* ========================================================= */}
        {/* 2. HOW IT WORKS (Light Mode Match)                        */}
        {/* ========================================================= */}
        <section id="how-it-works" className="py-20 bg-[#f8fafc] border-b border-slate-200">

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-12">
            
            {/* Header */}
            <div className="space-y-3 max-w-3xl mx-auto">
              <span className="text-xs font-bold tracking-widest text-emerald-600 uppercase">
                HOW IT WORKS
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
                From Raw Satellite Signal to Verified Analysis
              </h2>
              <p className="text-slate-600 text-sm sm:text-base">
                A seamless, human-in-the-loop scientific workflow designed for zero hallucinations when environmental decisions matter most.
              </p>
            </div>

            {/* 5 Step Process Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              
              {/* Step 1 */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center space-y-4 hover:border-emerald-500 transition-all hover:-translate-y-1 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
                  <Upload className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">1. Upload Scene</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Upload GeoTIFF, PNG, or JPG scenes from optical (Sentinel-2) or SAR radar platforms.
                </p>
              </div>

              {/* Step 2 */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center space-y-4 hover:border-emerald-500 transition-all hover:-translate-y-1 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
                  <BrainCircuit className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">2. Raster Engine</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Deterministic geospatial engines calculate exact NDVI, NDWI, built-up proxies, and K-Means land cover.
                </p>
              </div>

              {/* Step 3 */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center space-y-4 hover:border-emerald-500 transition-all hover:-translate-y-1 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">3. Zero-Hallucination</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  AI language reasoning references only verified pixel observations — never inventing unverified numbers.
                </p>
              </div>

              {/* Step 4 */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center space-y-4 hover:border-emerald-500 transition-all hover:-translate-y-1 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
                  <Send className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">4. Interactive Query</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Ask follow-up questions in natural language. Get instant answers grounded in calculated session evidence.
                </p>
              </div>

              {/* Step 5 */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center space-y-4 hover:border-emerald-500 transition-all hover:-translate-y-1 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
                  <Activity className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">5. Audit & Reports</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Download full Markdown or JSON reports with DAG traces and full evidence provenance for ISRO reviews.
                </p>
              </div>

            </div>

          </div>
        </section>


        {/* ========================================================= */}
        {/* 3. WHAT MAKES IT DIFFERENT / CAPABILITIES                 */}
        {/* ========================================================= */}
        <section id="capabilities" className="py-20 bg-white border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            
            {/* Section Header */}
            <div className="text-center space-y-3 max-w-3xl mx-auto">
              <span className="text-xs font-bold tracking-widest text-emerald-600 uppercase">
                WHAT MAKES IT DIFFERENT
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
                A Complete Remote Sensing Intelligence Platform
              </h2>
              <p className="text-slate-600 text-sm sm:text-base">
                Not just a generic chatbot — a multimodal system designed around remote sensing physics, multispectral math, and explainable AI.
              </p>
            </div>

            {/* 6 Feature Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              {/* Feature 1 */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 space-y-4 hover:border-emerald-500 transition-colors shadow-sm">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <Search className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Natural Language VQA</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Ask conversational questions in plain English: urban density, flood boundaries, crop stress, and mangrove canopy coverage without writing Python or GDAL scripts.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 space-y-4 hover:border-emerald-500 transition-colors shadow-sm">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <Activity className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Automated Change Detection</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Dual-date bi-temporal analysis with CVA (Change Vector Analysis) and automated Otsu thresholding to quantify urban growth, deforestation, and water retreat over time.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 space-y-4 hover:border-emerald-500 transition-colors shadow-sm">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <Layers className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Optical + SAR Radar Fusion</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Cross-modal analysis combining Sentinel-2 optical spectral fidelity with Sentinel-1 SAR cloud-penetrating structural radar for disaster response during storms and monsoons.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 space-y-4 hover:border-emerald-500 transition-colors shadow-sm">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Strict Deterministic Math</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Every percentage and km² metric comes directly from verified numpy & rasterio computations. Language models explain the findings but never fabricate values.
                </p>
              </div>

              {/* Feature 5 */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 space-y-4 hover:border-emerald-500 transition-colors shadow-sm">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <Compass className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Interactive Visualizer</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Multi-layer raster inspection with instant toggling between RGB true color, false color infrared, NDVI vegetation heatmaps, and classified land cover overlays.
                </p>
              </div>

              {/* Feature 6 */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 space-y-4 hover:border-emerald-500 transition-colors shadow-sm">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Provenance & Evidence Audit</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Every single output maintains an immutable evidence trace linking back to sensor band metadata, CRS coordinates, and exact algorithm formulas.
                </p>
              </div>

            </div>

          </div>
        </section>


        {/* ========================================================= */}
        {/* 4. PERFORMANCE & ACCURACY BENCHMARKS                      */}
        {/* ========================================================= */}
        <section id="benchmarks" className="py-20 bg-[#f8fafc] border-b border-slate-200 text-center">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
            
            <div className="space-y-3 max-w-2xl mx-auto">
              <span className="text-xs font-bold tracking-widest text-emerald-600 uppercase">
                BUILT BY STUDENTS · POWERED BY REMOTE SENSING
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
                Engineering Next-Gen Earth Intelligence
              </h2>
              <p className="text-slate-600 text-sm sm:text-base">
                Developed by our student engineering team for Smart India Hackathon problem statement SIH26167: Vision-Language remote sensing assistant.
              </p>
            </div>

            {/* Testimonials / Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 text-left">
              
              <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-3 shadow-sm">
                <div className="text-2xl font-extrabold text-emerald-600">50,000+</div>
                <h4 className="text-sm font-bold text-slate-900">BigEarthNet Training Dataset</h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Trained on 50k real multi-spectral satellite scenes across diverse biomes, terrain types, and climate conditions.
                </p>
              </div>

              <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-3 shadow-sm">
                <div className="text-2xl font-extrabold text-emerald-600">&lt; 1 Second</div>
                <h4 className="text-sm font-bold text-slate-900">Deterministic Computation</h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Real-time extraction of NDVI, NDWI, and built-up index with sub-second execution on standard hardware.
                </p>
              </div>

              <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-3 shadow-sm">
                <div className="text-2xl font-extrabold text-emerald-600">100% Provenance</div>
                <h4 className="text-sm font-bold text-slate-900">Audit Trail Guarantee</h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Every numeric value reported includes the mathematical formula, band numbers, and sensor metadata.
                </p>
              </div>

            </div>

          </div>
        </section>


      </main>


      {/* ========================================================= */}
      {/* 5. FOOTER (Screenshot 4 Match)                           */}
      {/* ========================================================= */}
      <footer className="bg-[#0a111e] border-t border-[#1d3356] pt-16 pb-12 text-slate-400 text-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          
          {/* Main Footer Links Columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
            
            {/* Brand column */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Globe2 className="w-5 h-5 text-emerald-400" />
                </div>
                <span className="font-bold text-xl tracking-tight text-white">SatQuery AI</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed max-w-sm">
                An AI-powered multimodal remote sensing analysis platform connecting satellite imagery, automated raster science, and conversational reasoning — from raw signal to verified decisions.
              </p>
              <div className="flex items-center gap-3 pt-2">
                <a href="#" className="w-8 h-8 rounded-lg bg-[#13233c] border border-[#1d3356] flex items-center justify-center text-slate-400 hover:text-white transition-colors">
                  <Twitter className="w-4 h-4" />
                </a>
                <a href="#" className="w-8 h-8 rounded-lg bg-[#13233c] border border-[#1d3356] flex items-center justify-center text-slate-400 hover:text-white transition-colors">
                  <Instagram className="w-4 h-4" />
                </a>
                <a href="#" className="w-8 h-8 rounded-lg bg-[#13233c] border border-[#1d3356] flex items-center justify-center text-slate-400 hover:text-white transition-colors">
                  <Linkedin className="w-4 h-4" />
                </a>
              </div>
            </div>

            {/* Quick Links */}
            <div className="space-y-3">
              <h4 className="text-white font-semibold text-xs uppercase tracking-wider">Quick Links</h4>
              <ul className="space-y-2 text-xs">
                <li><Link href="#how-it-works" className="hover:text-white transition-colors">How It Works</Link></li>
                <li><Link href="#capabilities" className="hover:text-white transition-colors">Capabilities</Link></li>
                <li><Link href="/analyze" className="hover:text-white transition-colors">Analyze Imagery</Link></li>
                <li><Link href="#partners" className="hover:text-white transition-colors">ISRO Problem SIH26167</Link></li>
              </ul>
            </div>

            {/* Platform */}
            <div className="space-y-3">
              <h4 className="text-white font-semibold text-xs uppercase tracking-wider">Platform</h4>
              <ul className="space-y-2 text-xs">
                <li><Link href="/analyze" className="hover:text-white transition-colors">Single Image VQA</Link></li>
                <li><Link href="/analyze" className="hover:text-white transition-colors">Bi-Temporal Change</Link></li>
                <li><Link href="/analyze" className="hover:text-white transition-colors">Optical + SAR Fusion</Link></li>
                <li><Link href="/analyze" className="hover:text-white transition-colors">Report Generator</Link></li>
              </ul>
            </div>

            {/* Community & Docs */}
            <div className="space-y-3">
              <h4 className="text-white font-semibold text-xs uppercase tracking-wider">Community & Docs</h4>
              <ul className="space-y-2 text-xs">
                <li><a href="https://browser.dataspace.copernicus.eu" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">Copernicus Data Space</a></li>
                <li><a href="https://bhuvan.nrsc.gov.in" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">ISRO Bhuvan Portal</a></li>
                <li><a href="https://huggingface.co/datasets/BIFOLD-BigEarthNetv2-0/BigEarthNet.txt" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">BigEarthNet Dataset</a></li>
                <li><a href="https://huggingface.co/datasets/xiang709/VRSBench" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">VRSBench Benchmark</a></li>
              </ul>
            </div>

          </div>

          {/* Contact & Newsletter Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-8 border-t border-[#1d3356]/60 text-xs">
            
            <div className="space-y-2">
              <h4 className="text-white font-semibold uppercase tracking-wider text-[11px]">STUDENT INNOVATION TEAM</h4>
              <div className="flex items-center gap-2 text-slate-400">
                <MapPin className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Smart India Hackathon (SIH26167) Team, India</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <Mail className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>contact@satquery.ai</span>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-white font-semibold uppercase tracking-wider text-[11px]">SUPPORT & ACCURACY</h4>
              <div className="space-y-1 text-slate-400">
                <p>Deterministic calculations via NumPy, OpenCV, and Rasterio.</p>
                <p>Validated on Sentinel-2 MSI and Sentinel-1 SAR standards.</p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-white font-semibold uppercase tracking-wider text-[11px]">STAY CONNECTED</h4>
              <p className="text-slate-400">Get updates on new model evaluations and satellite support.</p>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="bg-[#101d32] border border-[#1d3356] rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-full text-xs"
                />
                <button
                  type="button"
                  className="bg-emerald-500 hover:bg-emerald-400 text-[#0c1524] px-3.5 py-2 rounded-lg font-bold text-xs transition-colors shrink-0"
                >
                  Subscribe
                </button>
              </div>
            </div>

          </div>

          {/* Bottom copyright line */}
          <div className="pt-6 border-t border-[#1d3356]/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <p>© {new Date().getFullYear()} SatQuery AI. Built by Students for SIH.</p>
            <div className="flex items-center gap-4">
              <span>Built with 💚 by Student Innovators</span>
              <button
                onClick={scrollToTop}
                className="w-8 h-8 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-[#0c1524] flex items-center justify-center transition-transform hover:-translate-y-0.5 shadow-md shadow-emerald-500/20"
                title="Back to Top"
              >
                <ArrowUp className="w-4 h-4 font-bold" />
              </button>
            </div>
          </div>

        </div>
      </footer>
    </div>
  );
}
