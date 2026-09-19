'use client';

import { useState } from 'react';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { formatFileSize } from '@/lib/upload';
import clsx from 'clsx';

interface UploadCardProps {
  label: string;
  accept: string;
  description?: string;
  onFile: (file: File | null) => void;
}

export default function UploadCard({ label, accept, description, onFile }: UploadCardProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const acceptMap = accept.split(',').reduce((acc: Record<string, string[]>, ext) => {
    // Basic mapping for dropzone
    const extRaw = ext.trim();
    acc[`image/${extRaw.replace('.', '')}`] = [extRaw];
    acc['application/octet-stream'] = ['.tif', '.tiff', '.geotiff']; // generic for tiffs
    return acc;
  }, {});

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: acceptMap,
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
        onFile(acceptedFiles[0]);
      }
    }
  });

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    onFile(null);
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-semibold text-slate-700">{label}</label>
      <div 
        {...getRootProps()} 
        className={clsx(
          "border-2 border-dashed rounded-xl p-6 transition-colors cursor-pointer text-center relative overflow-hidden group flex flex-col items-center justify-center min-h-[160px]",
          isDragActive ? "border-emerald-500 bg-emerald-50/50" : "border-slate-300 hover:border-emerald-500 bg-slate-50/60",
          selectedFile ? "border-emerald-500 bg-emerald-50/30" : ""
        )}
      >
        <input {...getInputProps()} />
        
        {selectedFile ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 shadow-sm">
              <FileIcon className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-900 truncate max-w-[200px]">{selectedFile.name}</p>
              <p className="text-xs text-slate-500 font-medium">{formatFileSize(selectedFile.size)}</p>
            </div>
            <button 
              onClick={clearFile}
              className="absolute top-2 right-2 p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500 group-hover:text-emerald-600 group-hover:border-emerald-300 transition-colors shadow-sm">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-700">
                <span className="text-emerald-600 hover:underline font-semibold">Click to upload</span> or drag and drop
              </p>
              {description && <p className="text-xs text-slate-500">{description}</p>}
            </div>
          </div>
        )}
      </div>
    </div>

  );
}
