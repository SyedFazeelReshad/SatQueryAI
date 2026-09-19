'use client';

import React, { useState, useRef } from 'react';
import { Layers, Eye, EyeOff, Crosshair, ZoomIn, ZoomOut, RotateCcw, ArrowLeftRight } from 'lucide-react';
import { DetectionResult } from '@/types/analysis';

interface InteractiveVisualizerProps {
  previewUrl: string | null;
  previewBUrl?: string | null;       // Second image (T2 / "after") for change analysis
  overlayUrl?: string | null;
  layers?: Record<string, string>;
  detections?: DetectionResult[];
  onSelectDetection?: (detection: DetectionResult) => void;
}

export const InteractiveVisualizer: React.FC<InteractiveVisualizerProps> = ({
  previewUrl,
  previewBUrl,
  overlayUrl,
  layers = {},
  detections = [],
  onSelectDetection,
}) => {
  const isDualImage = !!previewBUrl;

  // Available layers map
  const activeLayersMap: Record<string, string> = { ...layers };
  if (previewUrl && !activeLayersMap['preview']) {
    activeLayersMap['preview'] = previewUrl;
  }
  if (overlayUrl && !activeLayersMap['overlay'] && !activeLayersMap['change']) {
    activeLayersMap['overlay'] = overlayUrl;
  }

  const layerKeys = Object.keys(activeLayersMap);
  const [selectedLayer, setSelectedLayer] = useState<string>(() => {
    if (isDualImage) return 'change';
    if (layerKeys.includes('change')) return 'change';
    if (layerKeys.includes('builtup')) return 'builtup';
    if (layerKeys.includes('ndwi')) return 'ndwi';
    if (layerKeys.includes('overlay')) return 'overlay';
    if (layerKeys.includes('ndvi')) return 'ndvi';
    return 'preview';
  });

  // Keep selected layer updated if layers are populated asynchronously
  React.useEffect(() => {
    if (!layerKeys.includes(selectedLayer)) {
      if (isDualImage && layerKeys.includes('change')) setSelectedLayer('change');
      else if (layerKeys.includes('change')) setSelectedLayer('change');
      else if (layerKeys.includes('builtup')) setSelectedLayer('builtup');
      else if (layerKeys.includes('ndwi')) setSelectedLayer('ndwi');
      else if (layerKeys.includes('overlay')) setSelectedLayer('overlay');
      else if (layerKeys.includes('ndvi')) setSelectedLayer('ndvi');
      else setSelectedLayer('preview');
    }
  }, [layers, overlayUrl]);

  const [overlayOpacity, setOverlayOpacity] = useState<number>(0.75);
  const [showDetections, setShowDetections] = useState<boolean>(true);
  const [zoom, setZoom] = useState<number>(1);
  const [hoverCoord, setHoverCoord] = useState<{ x: number; y: number } | null>(null);

  // Dual image: whether to show Before, After, or Overlay mode
  const [dualMode, setDualMode] = useState<'split' | 'before' | 'after' | 'change'>('split');

  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.round(e.clientX - rect.left);
    const y = Math.round(e.clientY - rect.top);
    setHoverCoord({ x, y });
  };

  const handleMouseLeave = () => {
    setHoverCoord(null);
  };

  const layerLabels: Record<string, string> = {
    preview: 'True Color (RGB)',
    before: 'ðŸ“· Before (T1)',
    after: 'ðŸ“· After (T2)',
    builtup: 'ðŸ™ï¸ Built-up Highlight',
    ndwi: 'ðŸŒŠ Water Highlight',
    ndvi: 'ðŸŒ¿ Vegetation Highlight',
    overlay: 'ðŸ—ºï¸ Land Cover Map',
    change: 'Bi-Temporal Change Mask',
  };

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const getFullUrl = (path: string | null | undefined) => {
    if (!path) return '';
    return path.startsWith('http') ? path : `${apiUrl}${path}`;
  };

  // â”€â”€â”€ DUAL IMAGE LAYOUT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  if (isDualImage) {
    const beforeUrl = getFullUrl(previewUrl);
    const afterUrl = getFullUrl(previewBUrl);
    const changeLayerUrl = getFullUrl(activeLayersMap['change'] || overlayUrl);

    return (
      <div className="flex flex-col bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {/* Top Toolbar */}
        <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-800 text-xs gap-2">
          <div className="flex items-center gap-2">
            <ArrowLeftRight className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold text-slate-300">Change Analysis View:</span>
            <div className="flex gap-1">
              {(['split', 'before', 'after', 'change'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setDualMode(m)}
                  className={`px-2.5 py-1 rounded transition-colors text-[11px] font-medium capitalize ${
                    dualMode === m
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-300 shadow-sm'
                      : 'text-slate-600 hover:text-white hover:bg-slate-200/60'
                  }`}
                >
                  {m === 'split' ? 'â¬› Side by Side' : m === 'before' ? 'ðŸ“· Before (T1)' : m === 'after' ? 'ðŸ“· After (T2)' : 'ðŸ”´ Change Mask'}
                </button>
              ))}
            </div>
          </div>

          {/* Zoom controls */}
          <div className="flex items-center space-x-1 border-l border-slate-800 pl-3">
            <button onClick={() => setZoom((z) => Math.min(2.5, z + 0.25))} className="p-1 hover:bg-slate-200/60 rounded text-slate-600 hover:text-white" title="Zoom In">
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setZoom((z) => Math.max(1.0, z - 0.25))} className="p-1 hover:bg-slate-200/60 rounded text-slate-600 hover:text-white" title="Zoom Out">
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setZoom(1.0)} className="p-1 hover:bg-slate-200/60 rounded text-slate-600 hover:text-white" title="Reset Zoom">
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Dual Image Display */}
        <div
          ref={containerRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          className="relative w-full bg-slate-950 overflow-hidden flex items-center justify-center select-none cursor-crosshair"
          style={{ minHeight: '420px' }}
        >
          {dualMode === 'split' ? (
            // Side-by-side layout
            <div
              style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
              className="flex gap-1 w-full h-full transition-transform duration-150 ease-out"
            >
              {/* Before panel */}
              <div className="flex-1 relative flex flex-col items-center">
                <div className="absolute top-2 left-2 z-10 bg-slate-900/80 text-emerald-300 text-[11px] font-bold px-2 py-0.5 rounded border border-slate-700 backdrop-blur-sm">
                  ðŸ“· BEFORE (T1)
                </div>
                {beforeUrl ? (
                  <img
                    src={beforeUrl}
                    alt="Before (T1)"
                    className="max-h-[500px] w-full object-contain block"
                  />
                ) : (
                  <div className="w-full h-64 flex items-center justify-center text-slate-600 text-sm">No T1 image</div>
                )}
              </div>

              {/* Divider */}
              <div className="w-px bg-emerald-500/40" />

              {/* After panel */}
              <div className="flex-1 relative flex flex-col items-center">
                <div className="absolute top-2 left-2 z-10 bg-slate-900/80 text-amber-300 text-[11px] font-bold px-2 py-0.5 rounded border border-slate-700 backdrop-blur-sm">
                  ðŸ“· AFTER (T2)
                </div>
                {afterUrl ? (
                  <img
                    src={afterUrl}
                    alt="After (T2)"
                    className="max-h-[500px] w-full object-contain block"
                  />
                ) : (
                  <div className="w-full h-64 flex items-center justify-center text-slate-600 text-sm">No T2 image</div>
                )}
              </div>
            </div>
          ) : dualMode === 'before' ? (
            // Before only
            <div style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }} className="relative transition-transform duration-150">
              <div className="absolute top-2 left-2 z-10 bg-slate-900/80 text-emerald-300 text-[11px] font-bold px-2 py-0.5 rounded border border-slate-700 backdrop-blur-sm">
                ðŸ“· BEFORE (T1)
              </div>
              <img src={beforeUrl} alt="Before (T1)" className="max-h-[500px] w-auto object-contain block" />
            </div>
          ) : dualMode === 'after' ? (
            // After only
            <div style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }} className="relative transition-transform duration-150">
              <div className="absolute top-2 left-2 z-10 bg-slate-900/80 text-amber-300 text-[11px] font-bold px-2 py-0.5 rounded border border-slate-700 backdrop-blur-sm">
                ðŸ“· AFTER (T2)
              </div>
              <img src={afterUrl} alt="After (T2)" className="max-h-[500px] w-auto object-contain block" />
            </div>
          ) : (
            // Change mask overlaid on After
            <div style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }} className="relative transition-transform duration-150">
              <div className="absolute top-2 left-2 z-10 bg-slate-900/80 text-red-300 text-[11px] font-bold px-2 py-0.5 rounded border border-slate-700 backdrop-blur-sm">
                ðŸ”´ CHANGE MASK (CVA + Otsu)
              </div>
              <img src={afterUrl} alt="After (T2) base" className="max-h-[500px] w-auto object-contain block" />
              {changeLayerUrl && (
                <img
                  src={changeLayerUrl}
                  alt="Change overlay"
                  style={{ opacity: overlayOpacity }}
                  className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-150"
                />
              )}
              {/* Opacity control for change mask */}
              <div className="absolute bottom-2 left-2 flex items-center gap-2 bg-slate-900/80 px-2 py-1 rounded border border-slate-700 text-[11px] text-slate-300">
                <span>Opacity:</span>
                <input
                  type="range"
                  min="0.1" max="1.0" step="0.05"
                  value={overlayOpacity}
                  onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
                  className="w-16 accent-red-500"
                  onClick={(e) => e.stopPropagation()}
                />
                <span className="font-mono">{Math.round(overlayOpacity * 100)}%</span>
              </div>
            </div>
          )}

          {/* Hover coord */}
          {hoverCoord && (
            <div className="absolute bottom-3 right-3 flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-950/80 border border-slate-700 text-[11px] font-mono text-slate-300 pointer-events-none backdrop-blur-sm">
              <Crosshair className="w-3 h-3 text-emerald-400" />
              <span>X: {hoverCoord.x}px | Y: {hoverCoord.y}px</span>
            </div>
          )}
        </div>

        {/* Footer legend */}
        <div className="px-4 py-2 bg-slate-50 border-t border-slate-800 flex items-center justify-between text-xs text-slate-600">
          <div>
            Dual Image Change Analysis &mdash;{' '}
            <span className="text-white font-semibold">
              {dualMode === 'split' ? 'Side-by-Side Comparison' : dualMode === 'before' ? 'Before Image (T1)' : dualMode === 'after' ? 'After Image (T2)' : 'Change Mask (CVA + Otsu)'}
            </span>
          </div>
          <div className="flex items-center space-x-2 text-[11px]">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            <span className="text-red-600 font-medium">Changed pixels</span>
          </div>
        </div>
      </div>
    );
  }

  // â”€â”€â”€ SINGLE IMAGE LAYOUT (unchanged) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  return (
    <div className="flex flex-col bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-800 text-xs">
        {/* Layer Selector */}
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-emerald-600" />
          <span className="font-semibold text-slate-300">Layer:</span>
          <div className="flex flex-wrap gap-1">
            {layerKeys.map((k) => (
              <button
                key={k}
                onClick={() => setSelectedLayer(k)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  selectedLayer === k
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-300 font-medium shadow-sm'
                    : 'text-slate-600 hover:text-white hover:bg-slate-200/60'
                }`}
              >
                {layerLabels[k] || k.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Controls: Opacity & Detections Toggle */}
        <div className="flex items-center space-x-4 mt-2 sm:mt-0">
          {selectedLayer !== 'preview' && (
            <div className="flex items-center space-x-2">
              <span className="text-slate-600 font-medium">Opacity:</span>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={overlayOpacity}
                onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
                className="w-20 accent-emerald-600 cursor-pointer"
              />
              <span className="text-slate-300 w-8 text-right font-mono text-[11px]">
                {Math.round(overlayOpacity * 100)}%
              </span>
            </div>
          )}

          {detections.length > 0 && (
            <button
              onClick={() => setShowDetections(!showDetections)}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded border transition-colors ${
                showDetections
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200 font-medium'
                  : 'bg-slate-900/80 text-slate-600 border-slate-800 hover:bg-slate-100'
              }`}
            >
              {showDetections ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span>Detections ({detections.length})</span>
            </button>
          )}

          {/* Zoom controls */}
          <div className="flex items-center space-x-1 border-l border-slate-800 pl-3">
            <button
              onClick={() => setZoom((z) => Math.min(2.5, z + 0.25))}
              className="p-1 hover:bg-slate-200/60 rounded text-slate-600 hover:text-white"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(1.0, z - 0.25))}
              className="p-1 hover:bg-slate-200/60 rounded text-slate-600 hover:text-white"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoom(1.0)}
              className="p-1 hover:bg-slate-200/60 rounded text-slate-600 hover:text-white"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>


      {/* Main Visualizer Area */}
      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="relative w-full aspect-video bg-slate-950 overflow-hidden flex items-center justify-center select-none cursor-crosshair"
      >
        <div
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
          className="relative max-w-full max-h-full transition-transform duration-150 ease-out"
        >
          {/* Base True Color Image */}
          {previewUrl ? (
            <img
              src={getFullUrl(previewUrl)}
              alt="Satellite Scene Base"
              className="max-h-[600px] w-auto object-contain block"
            />
          ) : (
            <div className="w-[512px] h-[384px] flex items-center justify-center text-slate-600">
              No base imagery available
            </div>
          )}

          {/* Active Overlay Layer */}
          {selectedLayer !== 'preview' && activeLayersMap[selectedLayer] && (
            <img
              src={getFullUrl(activeLayersMap[selectedLayer])}
              alt={`${selectedLayer} layer`}
              style={{ opacity: overlayOpacity }}
              className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-150"
            />
          )}

          {/* Detections SVG Layer */}
          {showDetections && detections.length > 0 && (
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {detections.map((det, idx) => {
                const [x0, y0, x1, y1] = det.box_xyxy;
                const width = Math.max(0, x1 - x0);
                const height = Math.max(0, y1 - y0);
                return (
                  <g key={idx}>
                    <rect
                      x={x0}
                      y={y0}
                      width={width}
                      height={height}
                      fill="rgba(99, 102, 241, 0.15)"
                      stroke="#818cf8"
                      strokeWidth="2"
                      strokeDasharray="4 2"
                      className="cursor-pointer pointer-events-auto hover:fill-indigo-500/30"
                      onClick={() => onSelectDetection && onSelectDetection(det)}
                    />
                    <text
                      x={x0 + 4}
                      y={Math.max(12, y0 - 4)}
                      fill="#e0e7ff"
                      fontSize="10"
                      fontWeight="bold"
                      className="drop-shadow-md"
                    >
                      {det.label} ({Math.round(det.score * 100)}%)
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>

        {/* Hover Coordinate Inspector Badge */}
        {hoverCoord && (
          <div className="absolute bottom-3 right-3 flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-950/80 border border-slate-700 text-[11px] font-mono text-slate-300 pointer-events-none backdrop-blur-sm">
            <Crosshair className="w-3 h-3 text-emerald-400" />
            <span>
              X: {hoverCoord.x}px | Y: {hoverCoord.y}px
            </span>
          </div>
        )}
      </div>

      {/* Layer legend footer */}
      <div className="px-4 py-2 bg-slate-50 border-t border-slate-800 flex items-center justify-between text-xs text-slate-600">
        <div>
          Active view: <span className="text-white font-semibold">{layerLabels[selectedLayer] || selectedLayer}</span>
        </div>
        {selectedLayer === 'ndvi' && (
          <div className="flex items-center space-x-2 text-[11px]">
            <span className="text-red-500 font-medium">Barren (-1.0)</span>
            <div className="w-24 h-2 rounded bg-gradient-to-r from-red-600 via-yellow-400 to-green-600" />
            <span className="text-green-600 font-medium">Dense Veg (+1.0)</span>
          </div>
        )}
        {selectedLayer === 'change' && (
          <div className="flex items-center space-x-2 text-[11px]">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            <span className="text-red-600 font-medium">Changed Area (CVA + Otsu)</span>
          </div>
        )}
      </div>
    </div>
  );
};

