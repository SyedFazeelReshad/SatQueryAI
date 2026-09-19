'use client';

import { RasterInfo } from '@/types/raster';
import { formatFileSize } from '@/lib/upload';
import { Info, AlertTriangle } from 'lucide-react';

interface MetadataPanelProps {
  metadata: RasterInfo;
  title?: string;
}

export default function MetadataPanel({ metadata, title = "Image Metadata" }: MetadataPanelProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
        <Info className="w-4 h-4 text-primary" />
        {title}
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <p className="text-gray-500 text-xs mb-1">Dimensions</p>
          <p className="font-medium text-gray-200">{metadata.width} &times; {metadata.height}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs mb-1">Bands</p>
          <p className="font-medium text-gray-200">{metadata.count} ({metadata.dtype})</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs mb-1">CRS</p>
          <p className="font-medium text-gray-200 truncate">{metadata.crs || 'Unknown'}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs mb-1">File Size</p>
          <p className="font-medium text-gray-200">{formatFileSize(metadata.file_size_bytes)}</p>
        </div>
        {metadata.gsd_m && (
          <div>
            <p className="text-gray-500 text-xs mb-1">GSD</p>
            <p className="font-medium text-gray-200">{metadata.gsd_m.toFixed(2)}m/px</p>
          </div>
        )}
      </div>

      {metadata.warnings && metadata.warnings.length > 0 && (
        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-500 flex flex-col gap-1">
          <div className="flex items-center gap-1.5 font-semibold">
            <AlertTriangle className="w-3.5 h-3.5" />
            Metadata Warnings
          </div>
          <ul className="list-disc list-inside ml-1">
            {metadata.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
