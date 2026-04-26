"use client";

import { useState, useEffect } from "react";
import ChatPanel from "@/components/ChatPanel";
import { Bot, AlertCircle } from "lucide-react";

export default function SpecBotPage() {
  const [jobId, setJobId] = useState<string | null>(null);

  useEffect(() => {
    // Attempt to load the most recent job ID from history
    const history = JSON.parse(localStorage.getItem("specsense_history") || "[]");
    if (history.length > 0) {
      setJobId(history[history.length - 1].job_id);
    }
  }, []);

  return (
    <main className="min-h-screen bg-[#0A0A0A] p-6 flex flex-col items-center">
      <div className="max-w-4xl w-full">
        <div className="mb-8 text-center">
          <div className="w-16 h-16 mx-auto bg-purple-500/20 rounded-2xl flex items-center justify-center mb-4 border border-purple-500/30 shadow-[0_0_30px_rgba(168,85,247,0.2)]">
            <Bot className="w-8 h-8 text-purple-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">SpecBot Dedicated Interface</h1>
          <p className="text-gray-400 max-w-lg mx-auto">
            Interact with your most recently processed specification document. All answers are strictly grounded in the text to prevent hallucinations.
          </p>
        </div>

        {!jobId ? (
          <div className="bg-[#111111] border border-red-500/20 rounded-2xl p-8 text-center flex flex-col items-center">
            <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No Active Specification Found</h2>
            <p className="text-gray-400 mb-6">
              You haven't uploaded or processed any documents yet. Please go to the Generate tab to upload a specification before using SpecBot.
            </p>
            <a href="/" className="px-6 py-2 bg-white text-black font-semibold rounded-lg hover:bg-gray-200 transition-colors">
              Go to Generate
            </a>
          </div>
        ) : (
          <div className="bg-[#111111] border border-white/5 rounded-2xl shadow-xl h-[600px] p-6">
            <ChatPanel jobId={jobId} />
          </div>
        )}
      </div>
    </main>
  );
}
