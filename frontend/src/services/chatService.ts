import api from "@/lib/api";

export interface ChatSource {
  source: string;
  score: number;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  sources?: ChatSource[];
}

interface ChatResponse {
  report_id: number;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  sources?: ChatSource[];
}

interface ChatHistoryResponse {
  report_id: number;
  messages: ChatMessage[];
}

interface DeleteChatResponse {
  report_id: number;
  message: string;
  deleted_count: number;
}

// Send a message to the report chatbot.
export const sendChatMessage = async (
  reportId: number,
  message: string
): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>(
    `/reports/${reportId}/chat`,
    {
      message,
      // The user's timezone, e.g. "Asia/Kolkata", so the backend
      // can show upload times in local time.
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    }
  );

  return response.data;
};

// Retrieve previous conversation messages.
export const getChatHistory = async (
  reportId: number
): Promise<ChatHistoryResponse> => {

  const response = await api.get<ChatHistoryResponse>(
    `/reports/${reportId}/chat`
  );

  return response.data;
};

// Delete the conversation history.
export const deleteChatHistory = async (
  reportId: number
): Promise<DeleteChatResponse> => {
  const response = await api.delete<DeleteChatResponse>(
    `/reports/${reportId}/chat`
  );

  return response.data;
};