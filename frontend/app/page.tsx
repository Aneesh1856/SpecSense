"use client";

import { useState } from "react";
import UploadZone from "@/components/UploadZone";
import TeamForm from "@/components/TeamForm";
import ProgressPanel from "@/components/ProgressPanel";
import OutputsPanel from "@/components/OutputsPanel";
import ChatPanel from "@/components/ChatPanel";
import { Activity, FileOutput, MessageSquare } from "lucide-react";

export default function Home() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"progress" | "outputs" | "chat">("progress");
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineFinished, setPipelineFinished] = useState(false);

  const handleUploadSuccess = (id: string, name: string) => {
    setJobId(id);
    setFilename(name);
    setPipelineRunning(false);
    setPipelineFinished(false);
    setActiveTab("progress");
  };

  const handleRunPipeline = () => {
    setPipelineRunning(true);
    setPipelineFinished(false);
    setActiveTab("progress");
  };

  const handlePipelineComplete = () => {
    setPipelineFinished(true);
    setPipelineRunning(false);
    // Switch to outputs tab after a short delay so user can see 100% and confetti
    setTimeout(() => {
      setActiveTab("outputs");
    }, 2500);
  };

  return (
    <main className="min-h-screen bg-[#0A0A0A] text-gray-200 p-6">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Upload & Config */}
        <div className="lg:col-span-5 space-y-6 flex flex-col">
          <UploadZone onUploadSuccess={handleUploadSuccess} />
          
          <div className="flex-grow">
            <TeamForm 
              jobId={jobId} 
              onRunPipeline={handleRunPipeline} 
            />
          </div>
        </div>

        {/* Right Column: Execution & Results */}
        <div className="lg:col-span-7 bg-[#111111] border border-white/5 rounded-2xl shadow-xl flex flex-col h-[85vh]">
          
          {/* Header/Tabs */}
          <div className="flex items-center border-b border-white/10 p-2">
            <button
              onClick={() => setActiveTab("progress")}
              className={`flex items-center space-x-2 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                activeTab === "progress" 
                  ? "bg-[#1A1A1A] text-purple-400 border border-white/5 shadow-sm" 
                  : "text-gray-500 hover:text-gray-300 hover:bg-[#151515]"
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Pipeline Status</span>
            </button>
            <button
              onClick={() => setActiveTab("outputs")}
              className={`flex items-center space-x-2 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                activeTab === "outputs" 
                  ? "bg-[#1A1A1A] text-purple-400 border border-white/5 shadow-sm" 
                  : "text-gray-500 hover:text-gray-300 hover:bg-[#151515]"
              }`}
            >
              <FileOutput className="w-4 h-4" />
              <span>Generated Artifacts</span>
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`flex items-center space-x-2 px-4 py-3 rounded-xl text-sm font-medium transition-all ml-auto ${
                activeTab === "chat" 
                  ? "bg-purple-600/10 text-purple-400 border border-purple-500/20 shadow-sm" 
                  : "text-gray-500 hover:text-purple-400 hover:bg-[#151515]"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>SpecBot</span>
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-grow p-6 overflow-hidden">
            {activeTab === "progress" && (
              <ProgressPanel 
                jobId={jobId} 
                pipelineRunning={pipelineRunning} 
                onComplete={handlePipelineComplete} 
              />
            )}
            
            {activeTab === "outputs" && (
              <OutputsPanel 
                jobId={jobId} 
                pipelineFinished={pipelineFinished} 
              />
            )}

            {activeTab === "chat" && (
              <ChatPanel 
                jobId={jobId} 
              />
            )}
          </div>
        </div>

      </div>
    </main>
  );
}
