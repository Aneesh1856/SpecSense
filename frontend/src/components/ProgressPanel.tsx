"use client";

import { useEffect, useState } from "react";
import { Check, Loader2, Circle } from "lucide-react";
import confetti from "canvas-confetti";

interface ProgressPanelProps {
  jobId: string | null;
  pipelineRunning: boolean;
  onComplete: () => void;
}

interface StepData {
  step: number;
  label: string;
  status: "idle" | "running" | "done" | "error";
  detail: string;
  grounding_score?: number | null;
}

export default function ProgressPanel({ jobId, pipelineRunning, onComplete }: ProgressPanelProps) {
  const [steps, setSteps] = useState<StepData[]>([]);
  const [overallProgress, setOverallProgress] = useState(0);
  const [groundingScore, setGroundingScore] = useState<number | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Reset state when job changes
    setSteps([]);
    setOverallProgress(0);
    setGroundingScore(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const eventSource = new EventSource(`${apiUrl}/progress/${jobId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const eventData: StepData = data.data;

        setSteps((prev) => {
          const newSteps = [...prev];
          const existingIndex = newSteps.findIndex((s) => s.step === eventData.step);
          if (existingIndex >= 0) {
            newSteps[existingIndex] = eventData;
          } else {
            newSteps.push(eventData);
          }
          newSteps.sort((a, b) => a.step - b.step);
          return newSteps;
        });

        if (eventData.grounding_score !== undefined && eventData.grounding_score !== null) {
          setGroundingScore(eventData.grounding_score);
        }

        const maxStep = 5;
        const currentStep = eventData.status === "done" ? eventData.step : eventData.step - 0.5;
        setOverallProgress(Math.min((currentStep / maxStep) * 100, 100));

        if (eventData.step === maxStep && eventData.status === "done") {
          eventSource.close();
          onComplete();
          confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#a855f7', '#3b82f6', '#10b981']
          });
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [jobId, pipelineRunning, onComplete]);

  // Static list of steps for rendering the skeleton
  const defaultSteps = [
    { num: 1, label: "Parsing Document" },
    { num: 2, label: "Building Index" },
    { num: 3, label: "Multi-agent extraction" },
    { num: 4, label: "Grounding Validation" },
    { num: 5, label: "Generating Output" },
  ];

  if (!jobId) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
        <Circle className="w-12 h-12 stroke-1 opacity-20" />
        <p>Upload a file and run the pipeline to see progress.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full relative">
      {/* Grounding Score Badge */}
      {groundingScore !== null && (
        <div className="absolute top-0 right-0 animate-in fade-in zoom-in duration-500">
          <div className="flex items-center space-x-2 bg-[#1A1A1A] border border-gray-800 rounded-xl p-3 shadow-lg">
            <div className="flex flex-col">
              <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Grounding Score</span>
              <span className={`text-xl font-bold ${
                groundingScore >= 90 ? "text-green-400" : groundingScore >= 70 ? "text-yellow-400" : "text-red-400"
              }`}>
                {groundingScore.toFixed(1)}%
              </span>
            </div>
            <div className="w-10 h-10 rounded-full border-[3px] flex items-center justify-center text-xs font-bold border-green-500/20 text-green-500 bg-green-500/10">
              🛡️
            </div>
          </div>
        </div>
      )}

      <div className="space-y-8 flex-grow mt-4">
        {defaultSteps.map((ds) => {
          const activeStep = steps.find((s) => s.step === ds.num);
          const status = activeStep?.status || "idle";
          const detail = activeStep?.detail || "";

          return (
            <div key={ds.num} className="flex items-start space-x-4">
              {/* Icon */}
              <div className="mt-1">
                {status === "done" ? (
                  <div className="w-8 h-8 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center">
                    <Check className="w-4 h-4 text-green-400" />
                  </div>
                ) : status === "running" ? (
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
                    <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                  </div>
                ) : status === "error" ? (
                  <div className="w-8 h-8 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center">
                    <span className="text-red-400 text-sm font-bold">!</span>
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center">
                    <span className="text-gray-500 text-sm">{ds.num}</span>
                  </div>
                )}
              </div>

              {/* Text */}
              <div className="flex flex-col">
                <span className={`text-sm font-semibold transition-colors ${
                  status === "done" ? "text-gray-200" : status === "running" ? "text-white" : "text-gray-600"
                }`}>
                  {ds.label}
                </span>
                {detail && (
                  <span className={`text-xs mt-1 transition-colors ${
                    status === "error" ? "text-red-400" : "text-gray-400"
                  }`}>
                    {detail}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Progress Bar */}
      <div className="mt-8 pt-6 border-t border-gray-800">
        <div className="flex justify-between text-xs text-gray-400 mb-2">
          <span>Overall Progress</span>
          <span>{Math.round(overallProgress)}%</span>
        </div>
        <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-purple-600 to-blue-500 transition-all duration-500 ease-out"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
