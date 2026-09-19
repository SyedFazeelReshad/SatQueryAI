'use client';

import Link from 'next/link';
import { Globe2, Sparkles, Satellite, Moon } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 group-hover:scale-105 transition-transform">
            <Globe2 className="w-5 h-5 text-emerald-600" />
          </div>
          <span className="font-bold text-lg tracking-tight text-slate-900 group-hover:text-emerald-600 transition-colors">
            SatQuery AI
          </span>
        </Link>
        
        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
          <Link href="/#hero" className="hover:text-slate-900 transition-colors">Home</Link>
          <Link href="/#how-it-works" className="hover:text-slate-900 transition-colors">How It Works</Link>
          <Link href="/#capabilities" className="hover:text-slate-900 transition-colors">Capabilities</Link>
          <Link href="/#benchmarks" className="hover:text-slate-900 transition-colors">Benchmarks</Link>
        </div>

        {/* Right CTA */}
        <div className="flex items-center gap-3">
          <Link 
            href="/analyze" 
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-md shadow-emerald-600/20 hover:shadow-emerald-600/30 flex items-center gap-1.5"
          >
            <span>Analyze Scene</span>
          </Link>
        </div>
      </div>
    </nav>
  );
}

