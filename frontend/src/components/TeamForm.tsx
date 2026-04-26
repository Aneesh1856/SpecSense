"use client";

import { useState } from "react";
import { Play } from "lucide-react";

interface TeamFormProps {
  jobId: string | null;
  onRunPipeline: () => void;
}

export default function TeamForm({ jobId, onRunPipeline }: TeamFormProps) {
  const [teamName, setTeamName] = useState("Alpha Engineers");
  const [teamId, setTeamId] = useState("T-100");
  const [members, setMembers] = useState("Alice, Bob, Charlie");
  const [leader, setLeader] = useState("Alice");

  const [options, setOptions] = useState({
    methodStatement: true,
    highlightedPdf: true,
    traceabilityReport: true,
    specBot: true,
  });

  const handleRun = async () => {
    if (!jobId) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/run/${jobId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          team_name: teamName,
          team_id: teamId,
          members: members,
          leader: leader,
          options: Object.keys(options).filter((k) => options[k as keyof typeof options]),
        }),
      });

      if (!res.ok) throw new Error("Failed to start pipeline");

      onRunPipeline();
    } catch (err) {
      console.error(err);
      alert("Failed to start pipeline");
    }
  };

  return (
    <div className="bg-[#111111] border border-white/5 rounded-2xl p-6 shadow-xl flex flex-col h-full">
      <h2 className="text-xl font-semibold text-white mb-6">2. Team & Pipeline Details</h2>

      <div className="space-y-4 flex-grow">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Team Name</label>
            <input
              type="text"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              className="w-full bg-[#0A0A0A] border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Team ID</label>
            <input
              type="text"
              value={teamId}
              onChange={(e) => setTeamId(e.target.value)}
              className="w-full bg-[#0A0A0A] border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>
        </div>

        <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Leader</label>
            <input
              type="text"
              value={leader}
              onChange={(e) => setLeader(e.target.value)}
              className="w-full bg-[#0A0A0A] border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-purple-500 transition-colors"
            />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-medium text-gray-400">Members (comma separated)</label>
          <input
            type="text"
            value={members}
            onChange={(e) => setMembers(e.target.value)}
            className="w-full bg-[#0A0A0A] border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-purple-500 transition-colors"
          />
        </div>

        <div className="pt-4 border-t border-gray-800">
          <label className="text-xs font-medium text-gray-400 mb-3 block">Outputs to Generate</label>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(options).map(([key, value]) => (
              <label key={key} className="flex items-center space-x-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={value}
                  onChange={(e) => setOptions({ ...options, [key]: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-700 text-purple-500 bg-[#0A0A0A] focus:ring-purple-500 focus:ring-offset-0 transition-colors cursor-pointer"
                />
                <span className="text-xs text-gray-300 group-hover:text-gray-100 transition-colors">
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <button
          onClick={handleRun}
          disabled={!jobId}
          className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl font-medium transition-all ${
            jobId
              ? "bg-purple-600 hover:bg-purple-500 text-white shadow-[0_0_20px_rgba(147,51,234,0.3)] hover:shadow-[0_0_30px_rgba(147,51,234,0.5)]"
              : "bg-gray-800 text-gray-500 cursor-not-allowed"
          }`}
        >
          <Play className="w-4 h-4" />
          <span>Run Pipeline</span>
        </button>
      </div>
    </div>
  );
}
