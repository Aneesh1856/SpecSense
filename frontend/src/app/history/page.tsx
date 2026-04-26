"use client";

import { useState, useEffect } from "react";
import { Clock, FileText, Download } from "lucide-react";

interface HistoryItem {
  job_id: string;
  filename: string;
  date: string;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    const data = JSON.parse(localStorage.getItem("specsense_history") || "[]");
    // Sort descending
    data.sort((a: HistoryItem, b: HistoryItem) => new Date(b.date).getTime() - new Date(a.date).getTime());
    setHistory(data);
  }, []);

  const handleDownload = async (filename: string, jobId: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/download/${jobId}/${filename}`);
      
      if (!res.ok) throw new Error("File not found");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(err);
      alert(`Could not download ${filename}. It might have expired from the server.`);
    }
  };

  return (
    <main className="min-h-screen bg-[#0A0A0A] p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center space-x-3 mb-8">
          <Clock className="w-6 h-6 text-purple-400" />
          <h1 className="text-2xl font-bold text-white tracking-tight">Processing History</h1>
        </div>

        {history.length === 0 ? (
          <div className="bg-[#111111] border border-white/5 rounded-2xl p-12 text-center text-gray-400">
            No processing history found.
          </div>
        ) : (
          <div className="space-y-4">
            {history.map((item, idx) => {
              const date = new Date(item.date);
              const formattedDate = date.toLocaleDateString() + " " + date.toLocaleTimeString();

              return (
                <div key={idx} className="bg-[#111111] border border-white/5 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between transition-colors hover:border-gray-700">
                  <div className="flex items-start space-x-4">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-purple-400" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold text-gray-200">{item.filename}</span>
                      <span className="text-xs text-gray-500 mt-1">{formattedDate}</span>
                      <span className="text-[10px] text-gray-600 font-mono mt-1">ID: {item.job_id}</span>
                    </div>
                  </div>

                  <div className="mt-4 sm:mt-0 flex space-x-2">
                    <button
                      onClick={() => handleDownload(`method_statement_${item.job_id}.docx`, item.job_id)}
                      className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#222222] hover:bg-[#333333] border border-gray-700 text-xs font-medium transition-colors"
                    >
                      <Download className="w-3 h-3" />
                      <span>DOCX</span>
                    </button>
                    <button
                      onClick={() => handleDownload(`highlighted_spec_${item.job_id}.pdf`, item.job_id)}
                      className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#222222] hover:bg-[#333333] border border-gray-700 text-xs font-medium transition-colors"
                    >
                      <Download className="w-3 h-3" />
                      <span>PDF</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
