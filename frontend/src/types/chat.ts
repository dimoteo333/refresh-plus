export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  query: string;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  context?: string;
  error?: string;
}

export interface ChatbotStats {
  success: boolean;
  data: {
    total_documents: number;
    collection_name: string;
  };
}
