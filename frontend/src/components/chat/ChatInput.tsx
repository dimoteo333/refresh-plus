"use client";

import { useState } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    onSendMessage(input);
    setInput("");
  };

  return (
    <div className="border-t-2 border-sky-100 bg-gradient-to-b from-sky-50/80 to-white px-4 py-4 shadow-[0_-4px_12px_rgba(0,0,0,0.05)]">
      <form onSubmit={handleSubmit} className="flex gap-3 items-center max-w-5xl mx-auto">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="궁금한 점을 물어보세요..."
          disabled={isLoading}
          className="flex-1 rounded-2xl border border-sky-100 bg-white/80 px-5 py-3 text-sm text-slate-900 placeholder-slate-500 shadow-sm backdrop-blur transition-all focus:border-sky-300 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-lg transition-all hover:shadow-xl active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg disabled:active:scale-100"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
}
