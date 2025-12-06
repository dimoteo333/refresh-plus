"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Send, User } from "lucide-react";
import { ChatMessage } from "@/types/chat";

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isTyping: boolean;
  onSendMessage: (content: string) => void;
  isLoading: boolean;
}

export default function ChatInterface({
  messages,
  isTyping,
  onSendMessage,
  isLoading,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // 메시지가 추가되면 스크롤을 아래로
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    onSendMessage(input);
    setInput("");
  };

  return (
    <div className="flex h-full flex-col">
      {/* 메시지 목록 */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6 space-y-4"
      >
        {messages.map((message, index) => (
          <div
            key={message.id}
            className={`flex items-start gap-3 animate-in fade-in slide-in-from-bottom-4 duration-500`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {message.role === "assistant" ? (
              <>
                {/* 봇 아이콘 */}
                <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-lg">
                  <Bot className="h-5 w-5" />
                </div>
                {/* 봇 메시지 */}
                <div className="flex-1 rounded-3xl rounded-tl-lg bg-white/80 px-5 py-4 shadow-sm backdrop-blur-sm border border-sky-100/60">
                  <p className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
              </>
            ) : (
              <>
                {/* 사용자 메시지 */}
                <div className="flex-1 flex justify-end">
                  <div className="max-w-[80%] rounded-3xl rounded-tr-lg bg-gradient-to-br from-sky-500 to-blue-600 px-5 py-4 shadow-lg">
                    <p className="text-sm leading-relaxed text-white whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                </div>
                {/* 사용자 아이콘 */}
                <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-2xl bg-white/75 text-sky-700 shadow-inner ring-1 ring-white/50">
                  <User className="h-5 w-5" />
                </div>
              </>
            )}
          </div>
        ))}

        {/* 타이핑 인디케이터 */}
        {isTyping && (
          <div className="flex items-start gap-3 animate-in fade-in slide-in-from-bottom-4 duration-300">
            <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-lg">
              <Bot className="h-5 w-5" />
            </div>
            <div className="rounded-3xl rounded-tl-lg bg-white/80 px-5 py-4 shadow-sm backdrop-blur-sm border border-sky-100/60">
              <div className="flex gap-1.5">
                <div className="h-2 w-2 rounded-full bg-sky-500 animate-bounce [animation-delay:-0.3s]" />
                <div className="h-2 w-2 rounded-full bg-sky-500 animate-bounce [animation-delay:-0.15s]" />
                <div className="h-2 w-2 rounded-full bg-sky-500 animate-bounce" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력창 */}
      <div className="border-t border-sky-100/60 bg-white/50 backdrop-blur-sm px-4 py-4">
        <form onSubmit={handleSubmit} className="flex gap-3 items-center">
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
    </div>
  );
}
