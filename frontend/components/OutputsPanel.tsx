"use client";

import { useState, useEffect } from "react";
import { FileText, Download, CheckCircle, TableProperties } from "lucide-react";

interface OutputsPanelProps {
  jobId: string | null;
  pipelineFinished: boolean;
}

interface OutputFile {
  id: string;
  filename: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

export default function OutputsPanel({ jobId, pipelineFinished }: OutputsPanelProps) {
  const [downloading, setDownloading] = useState<string | null>(null);

  if (!pipelineFinished || !jobId) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
        <CheckCircle className="w-12 h-12 stroke-1 opacity-20" />
        <p>Run the pipeline to generate outputs.</p>
      </div>
    );
  }

  const files: OutputFile[] = [
    {
      id: "method_statement",
      filename: `method_statement_${jobId}.docx`,
      title: "Method Statement",
      description: "Standardized construction procedure document (DOCX)",
      icon: <FileText className="w-5 h-5" />,
      color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    },
    {
      id: "highlighted_spec",
      filename: `highlighted_spec_${jobId}.pdf`,
      title: "Annotated Specification",
      description: "Original PDF with facts highlighted for traceability",
      icon: <FileText className="w-5 h-5" />,
      color: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    },
    {
      id: "traceability_report",
      filename: `traceability_report_${jobId}.xlsx`,
      title: "Traceability Report",
      description: "Excel matrix of extracted facts and clauses",
      icon: <TableProperties className="w-5 h-5" />,
      color: "bg-green-500/20 text-green-400 border-green-500/30",
    }
  ];

  const handleDownload = async (filename: string, id: string) => {
    setDownloading(id);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/download/${jobId}/${filename}`);
      
      if (!res.ok) {
        // Just fail silently for dummy files or show alert
        throw new Error("File not found");
      }
      
      // Trigger download
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename.split("_").slice(0, -1).join("_") + "." + filename.split(".").pop(); // clean up job id
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(err);
      alert(`Could not download ${filename}`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white">Generated Documents</h3>
        <p className="text-sm text-gray-400 mt-1">
          Your pipeline has finished successfully. Download your artifacts below.
        </p>
      </div>

      <div className="space-y-4">
        {files.map((file) => (
          <div 
            key={file.id} 
            className="flex items-center justify-between p-4 rounded-xl bg-[#1A1A1A] border border-gray-800 hover:border-gray-700 transition-colors"
          >
            <div className="flex items-center space-x-4">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${file.color}`}>
                {file.icon}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-gray-200">{file.title}</span>
                <span className="text-xs text-gray-500">{file.description}</span>
              </div>
            </div>

            <button
              onClick={() => handleDownload(file.filename, file.id)}
              disabled={downloading === file.id}
              className="flex items-center justify-center w-10 h-10 rounded-lg bg-[#222222] hover:bg-[#333333] text-gray-300 transition-colors border border-gray-700"
              title="Download"
            >
              {downloading === file.id ? (
                <div className="w-4 h-4 border-2 border-gray-400 border-t-white rounded-full animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
