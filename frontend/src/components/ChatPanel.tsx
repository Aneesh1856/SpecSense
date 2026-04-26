"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";

interface ChatPanelProps {
  jobId: string | null;
}

interface Message {
  role: "user" | "bot";
  content: string;
  source_page?: number;
  source_clause?: string;
}

export default function ChatPanel({ jobId }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "bot",
      content: "Hi! I am SpecBot. Ask me any questions about your uploaded specification document.",
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickQuestions = [
    "What cement type?",
    "Max w/c ratio?",
    "Curing duration?",
    "IS codes listed?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || !jobId) return;

    const newMessages = [...messages, { role: "user", content: text } as Message];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      // History could be passed if needed
      const res = await fetch(`${apiUrl}/chat/${jobId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: [] }),
      });

      if (!res.ok) throw new Error("API Error");

      const data = await res.json();
      setMessages([...newMessages, {
        role: "bot",
        content: data.answer,
        source_page: data.source_page,
        source_clause: data.source_clause
      }]);
    } catch (err) {
      console.error(err);
      setMessages([...newMessages, { role: "bot", content: "Sorry, I encountered an error connecting to the server." }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!jobId) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
        <Bot className="w-12 h-12 stroke-1 opacity-20" />
        <p>Upload a file to start chatting with SpecBot.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages */}
      <div className="flex-grow overflow-y-auto pr-2 space-y-4 pb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl p-4 flex space-x-3 ${
              msg.role === "user" 
                ? "bg-purple-600 text-white rounded-br-none" 
                : "bg-[#1A1A1A] border border-gray-800 text-gray-200 rounded-bl-none"
            }`}>
              {msg.role === "bot" && (
                <div className="flex-shrink-0 mt-1">
                  <Bot className="w-5 h-5 text-gray-400" />
                </div>
              )}
              
              <div className="flex flex-col">
                <span className="text-sm leading-relaxed">{msg.content}</span>
                
                {msg.role === "bot" && msg.source_page ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="inline-flex items-center px-2 py-1 rounded bg-[#222222] border border-gray-700 text-[10px] font-semibold text-gray-400">
                      📄 Pg. {msg.source_page} {msg.source_clause ? `· Cl. ${msg.source_clause.substring(0, 15)}...` : ""}
                    </span>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[#1A1A1A] border border-gray-800 rounded-2xl rounded-bl-none p-4 flex space-x-2 items-center">
              <Bot className="w-5 h-5 text-gray-400" />
              <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-auto pt-4 border-t border-gray-800 bg-[#111]">
        <div className="flex flex-wrap gap-2 mb-3">
          {quickQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => sendMessage(q)}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-full bg-[#1A1A1A] border border-gray-700 hover:border-purple-500/50 text-xs text-gray-300 transition-colors whitespace-nowrap"
            >
              {q}
            </button>
          ))}
        </div>
        
        <form 
          onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about the spec..."
            className="flex-grow bg-[#1A1A1A] border border-gray-800 rounded-xl px-4 py-3 text-sm text-gray-200 focus:outline-none focus:border-purple-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="w-12 h-12 flex items-center justify-center rounded-xl bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
