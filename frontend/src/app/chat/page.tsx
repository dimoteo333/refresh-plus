"use client";

import { useEffect } from "react";
import Image from "next/image";
import { Bot, Menu, Bell, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import BottomNav from "@/components/layout/BottomNav";
import ChatInterface from "@/components/chat/ChatInterface";
import { useChat } from "@/hooks/useChat";

// 임시 토큰 (실제로는 인증 시스템에서 가져와야 함)
const TEMP_TOKEN = "user-id-1";

export default function ChatPage() {
  const {
    messages,
    isTyping,
    sendMessage,
    addWelcomeMessage,
    stats,
    isLoading,
  } = useChat({ token: TEMP_TOKEN });

  // 페이지 로드 시 환영 메시지 추가
  useEffect(() => {
    if (messages.length === 0) {
      addWelcomeMessage();
    }
  }, [messages.length, addWelcomeMessage]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50/70 to-white text-gray-900">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-28 pt-6 sm:px-6 lg:px-8">
        {/* 헤더 */}
        <header className="flex items-center justify-between gap-3 px-1 py-2 sm:px-2 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="flex items-center gap-3">
            <div className="relative h-12 w-12 overflow-hidden rounded-2xl border border-sky-100 bg-white shadow-sm">
              <Image
                src="/images/sol-bear.svg"
                alt="SOL 캐릭터 로고"
                width={48}
                height={48}
                className="h-full w-full object-cover"
              />
            </div>
            <div>
              <p className="text-sm font-semibold text-sky-700">Refresh Plus</p>
              <p className="text-xs text-gray-600">AI 챗봇</p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            {stats?.data?.total_documents && (
              <Badge className="bg-sky-100 text-sky-800 hidden sm:flex">
                <Sparkles className="h-3.5 w-3.5 mr-1" />
                {stats.data.total_documents}개 FAQ 학습
              </Badge>
            )}
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-900 transition hover:bg-sky-100/40"
              aria-label="알림"
            >
              <Bell className="h-6 w-6" />
            </button>
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-900 transition hover:bg-sky-100/40"
              aria-label="전체 메뉴"
            >
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </header>

        {/* 메인 채팅 영역 */}
        <main className="mt-6 flex flex-1 flex-col animate-in fade-in slide-in-from-bottom-6 duration-700 [animation-delay:100ms]">
          <div className="flex flex-1 flex-col overflow-hidden rounded-3xl border border-sky-100/60 bg-white/80 shadow-lg backdrop-blur-lg">
            {/* 채팅 헤더 */}
            <div className="flex items-center gap-3 border-b border-sky-100/60 bg-gradient-to-r from-sky-50/80 to-blue-50/80 px-6 py-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-lg">
                <Bot className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  AI 도우미
                </h2>
                <p className="text-xs text-slate-600">
                  숙소 예약, 포인트 시스템 등에 대해 물어보세요
                </p>
              </div>
            </div>

            {/* 채팅 인터페이스 */}
            <ChatInterface
              messages={messages}
              isTyping={isTyping}
              onSendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>

          {/* 하단 도움말 */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2 px-4 text-xs text-slate-600 animate-in fade-in duration-1000 [animation-delay:300ms]">
            <Sparkles className="h-4 w-4 text-sky-500" />
            <span>FAQ 기반 RAG 챗봇으로 정확한 답변을 제공합니다</span>
          </div>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
