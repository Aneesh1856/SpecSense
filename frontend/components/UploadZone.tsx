"use client";

import { useState, useRef } from "react";
import { UploadCloud, File as FileIcon, Loader2 } from "lucide-react";

interface UploadZoneProps {
  onUploadSuccess: (jobId: string, filename: string) => void;
}

export default function UploadZone({ onUploadSuccess }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [fileInfo, setFileInfo] = useState<{ name: string; size: string } | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleFile = async (file: File) => {
    setError(null);
    if (!file.name.endsWith(".pdf") && !file.name.endsWith(".docx")) {
      setError("Only .pdf and .docx files are supported");
      return;
    }

    setFileInfo({ name: file.name, size: formatSize(file.size) });
    setIsUploading(true);
    setSuccessMessage(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();
      setSuccessMessage(`${data.pages} pages indexed`);
      onUploadSuccess(data.job_id, data.filename);
      
      // Save to history
      const history = JSON.parse(localStorage.getItem("specsense_history") || "[]");
      history.push({
        job_id: data.job_id,
        filename: data.filename,
        date: new Date().toISOString(),
      });
      localStorage.setItem("specsense_history", JSON.stringify(history));

    } catch (err) {
      console.error(err);
      setError("Failed to upload file. Check API connection.");
      setFileInfo(null);
    } finally {
      setIsUploading(false);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-[#111111] border border-white/5 rounded-2xl p-6 shadow-xl">
      <h2 className="text-xl font-semibold text-white mb-4">1. Upload Specification</h2>
      
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? "border-purple-500 bg-purple-500/10"
            : fileInfo
            ? "border-green-500/50 bg-green-500/5"
            : "border-gray-700 bg-[#0A0A0A] hover:border-gray-500 hover:bg-[#151515]"
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          accept=".pdf,.docx"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        {isUploading ? (
          <div className="flex flex-col items-center justify-center space-y-4">
            <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
            <p className="text-sm text-gray-400">Uploading and indexing document...</p>
          </div>
        ) : fileInfo ? (
          <div className="flex flex-col items-center justify-center space-y-2">
            <FileIcon className="w-10 h-10 text-green-400 mb-2" />
            <p className="text-sm font-medium text-gray-200">{fileInfo.name}</p>
            <p className="text-xs text-gray-500">{fileInfo.size}</p>
            {successMessage && (
              <p className="text-xs font-semibold text-green-400 mt-2 bg-green-400/10 px-3 py-1 rounded-full">
                ✓ {successMessage}
              </p>
            )}
            <p className="text-xs text-gray-600 mt-4 underline decoration-dotted cursor-pointer">
              Click to replace file
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-3 cursor-pointer">
            <div className="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center mb-2">
              <UploadCloud className="w-6 h-6 text-gray-400" />
            </div>
            <p className="text-sm font-medium text-gray-300">
              Drag & drop your file here
            </p>
            <p className="text-xs text-gray-500">
              Only .pdf and .docx files are supported
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
