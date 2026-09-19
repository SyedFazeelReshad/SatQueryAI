'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { FileImage, Layers, Activity, MessageSquare } from 'lucide-react';

const features = [
  {
    icon: <FileImage className="w-6 h-6 text-primary" />,
    title: 'Single Image Analysis',
    desc: 'Describe land cover, terrain, and identify key features from a single optical or SAR image.',
  },
  {
    icon: <Layers className="w-6 h-6 text-primary" />,
    title: 'Optical + SAR Fusion',
    desc: 'Combine optical imagery with synthetic aperture radar for structural and material insights.',
  },
  {
    icon: <Activity className="w-6 h-6 text-primary" />,
    title: 'Change Detection',
    desc: 'Analyze multi-temporal imagery to identify and quantify changes over time.',
  },
  {
    icon: <MessageSquare className="w-6 h-6 text-primary" />,
    title: 'Natural Language Queries',
    desc: 'Ask questions naturally. The AI translates your query into a remote sensing execution pipeline.',
  }
];

export default function Hero() {
  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-20 lg:py-32 flex flex-col items-center text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-6"
      >
        <div className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1 text-sm text-gray-300">
          <span className="text-primary font-semibold mr-2">ISRO SIH26167</span> Stage 1 Prototype
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white max-w-4xl mx-auto">
          Understand Earth from <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-primary">every signal.</span>
        </h1>
        
        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
          Ask questions about satellite imagery using natural language — across single images, time, and multiple sensors. No coding required.
        </p>

        <div className="pt-4">
          <Link href="/analyze" className="inline-flex items-center justify-center bg-primary hover:bg-primary-hover text-white text-lg font-medium px-8 py-4 rounded-xl transition-all shadow-lg shadow-primary/20 hover:shadow-primary/40">
            Analyze a Scene &rarr;
          </Link>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.2 }}
        className="mt-32 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full"
      >
        {features.map((feature, i) => (
          <div key={i} className="bg-card border border-border rounded-xl p-6 text-left hover:border-primary/50 transition-colors">
            <div className="bg-background rounded-lg w-12 h-12 flex items-center justify-center border border-border mb-4">
              {feature.icon}
            </div>
            <h3 className="text-white font-semibold text-lg mb-2">{feature.title}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
          </div>
        ))}
      </motion.div>
    </div>
  );
}
