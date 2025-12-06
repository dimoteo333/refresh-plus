"use client";

import { useState, useCallback } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { chatbotApi } from "@/lib/api";
import { ChatMessage, ChatResponse, ChatbotStats } from "@/types/chat";

interface UseChatOptions {
  token: string;
}

export function useChat({ token }: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  // 챗봇 통계 조회
  const { data: stats } = useQuery<ChatbotStats>({
    queryKey: ["chatbot-stats"],
    queryFn: async () => {
      const response = await chatbotApi.getStats(token);
      return response.data;
    },
    enabled: !!token,
  });

  // 채팅 메시지 전송
  const chatMutation = useMutation({
    mutationFn: async (query: string) => {
      const response = await chatbotApi.chat(token, query);
      return response.data as ChatResponse;
    },
    onSuccess: (data, query) => {
      // 봇 응답 추가
      const botMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
      setIsTyping(false);
    },
    onError: (error) => {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "assistant",
        content: "죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsTyping(false);
    },
  });

  // 메시지 전송 함수
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || chatMutation.isPending) return;

      // 사용자 메시지 추가
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "user",
        content: content.trim(),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);

      // API 호출
      chatMutation.mutate(content.trim());
    },
    [chatMutation]
  );

  // 메시지 초기화
  const clearMessages = useCallback(() => {
    setMessages([]);
    setIsTyping(false);
  }, []);

  // 환영 메시지 추가
  const addWelcomeMessage = useCallback(() => {
    const welcomeMessage: ChatMessage = {
      id: "welcome",
      role: "assistant",
      content:
        "안녕하세요! 👋\n\n저는 Refresh Plus 연성소 예약 플랫폼의 AI 도우미입니다.\n\n숙소 예약, 포인트 시스템, 이용 방법 등에 대해 궁금하신 점을 물어보세요!",
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, []);

  return {
    messages,
    isTyping,
    sendMessage,
    clearMessages,
    addWelcomeMessage,
    stats,
    isLoading: chatMutation.isPending,
  };
}
