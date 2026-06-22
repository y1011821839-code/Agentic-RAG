export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: any[];
  toolsUsed?: string[];
}

export interface ChatResponse {
  answer: string;
  sources: any[];
  tools_used: string[];
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}
