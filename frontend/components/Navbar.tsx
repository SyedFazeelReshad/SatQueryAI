'use client';

import React from 'react';
import Link from 'next/link';
import { Sparkles, ArrowRight, Satellite } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#020612]/80 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-500 flex items-center justify-center text-slate-950 shadow-[0_0_15px_rgba(6,182,212,0.4)]">
            <Satellite className="w-5 h-5" />
          </div>
          <span className="font-extrabold text-lg tracking-tight text-white">
            SatQuery <span className="bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">AI</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-7 text-xs font-semibold text-slate-300">
          <Link href="/" className="hover:text-cyan-400 transition-colors">Home</Link>
          <a href="/#how-it-works" className="hover:text-cyan-400 transition-colors">How It Works</a>
          <a href="/#capabilities" className="hover:text-cyan-400 transition-colors">Capabilities</a>
          <Link href="/benchmarks" className="hover:text-cyan-400 transition-colors">Benchmarks</Link>
        </nav>

        <Link
          href="/analyze"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-xs shadow-md shadow-emerald-500/20 hover:scale-105 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Analyze Scene</span>
        </Link>
      </div>
    </header>
  );
}
