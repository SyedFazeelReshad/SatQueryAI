'use client';

import Image from 'next/image';
import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import clsx from 'clsx';

interface ImagePreviewProps {
  previewUrl: string | null;
  overlayUrl: string | null;
}

export default function ImagePreview({ previewUrl, overlayUrl }: ImagePreviewProps) {
  const [showOverlay, setShowOverlay] = useState(true);

  if (!previewUrl) {
    return (
      <div className="w-full aspect-video bg-surface border border-border rounded-xl flex items-center justify-center text-gray-500 text-sm">
        No preview available
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-square md:aspect-video bg-[#050505] border border-border rounded-xl overflow-hidden group">
      
      {/* Base Image */}
      <div className="absolute inset-0">
        <Image 
          src={previewUrl}
          alt="Original satellite imagery"
          fill
          className="object-contain"
        />
      </div>

      {/* Overlay Image */}
      {overlayUrl && (
        <div 
          className={clsx(
            "absolute inset-0 transition-opacity duration-300",
            showOverlay ? "opacity-100" : "opacity-0"
          )}
        >
          <Image 
            src={overlayUrl}
            alt="Analysis overlay"
            fill
            className="object-contain"
          />
        </div>
      )}

      {/* Controls */}
      {overlayUrl && (
        <div className="absolute bottom-4 right-4 z-10">
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className="flex items-center gap-2 px-3 py-1.5 bg-black/60 hover:bg-black/80 backdrop-blur text-white text-xs font-medium rounded-lg border border-white/10 transition-colors"
          >
            {showOverlay ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {showOverlay ? "Hide Overlay" : "Show Overlay"}
          </button>
        </div>
      )}
    </div>
  );
}
