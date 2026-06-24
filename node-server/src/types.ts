// 共享类型定义

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  question: string;
  session_id?: string | null;
  history: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  session_id: string;
  sources: SourceDoc[];
  tools_used: string[];
}

export interface SourceDoc {
  content: string;
  metadata: Record<string, unknown>;
  similarity?: number;
  id?: string;
}

export interface SessionInfo {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  success: boolean;
  document_id: string;
  chunks_count: number;
  message: string;
}

// Python 模型层内部 API 响应类型
export interface PythonChatResponse {
  answer: string;
  sources: SourceDoc[];
  tools_used: string[];
}

export interface PythonStreamEvent {
  type: 'thinking' | 'token' | 'done' | 'error';
  content?: string;
  sources?: SourceDoc[];
  tools_used?: string[];
}