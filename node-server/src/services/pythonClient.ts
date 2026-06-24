/**
 * Python 模型层 HTTP 客户端
 * 调用 Python FastAPI 内部 API（非流式 + 流式）
 */
import type { PythonChatResponse, PythonStreamEvent, ChatMessage } from '../types.js';

const PYTHON_BASE_URL = process.env.PYTHON_MODEL_URL || 'http://localhost:8000';

interface ChatPayload {
  question: string;
  history: ChatMessage[];
}

class PythonModelClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = PYTHON_BASE_URL;
  }

  /**
   * 非流式聊天
   */
  async chat(payload: ChatPayload): Promise<PythonChatResponse> {
    const response = await fetch(`${this.baseUrl}/internal/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(120_000),
    });

    if (!response.ok) {
      const err = await response.text().catch(() => '');
      throw new Error(`Python 模型层错误 (${response.status}): ${err}`);
    }

    return response.json();
  }

  /**
   * 流式聊天 — 返回 ReadableStream 供 SSE 代理
   */
  async chatStream(payload: ChatPayload): Promise<ReadableStream<Uint8Array>> {
    const response = await fetch(`${this.baseUrl}/internal/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(300_000),
    });

    if (!response.ok) {
      const err = await response.text().catch(() => '');
      throw new Error(`Python 模型层错误 (${response.status}): ${err}`);
    }

    if (!response.body) {
      throw new Error('Python 模型层未返回流式响应');
    }

    return response.body;
  }

  /**
   * 上传文档
   */
  async uploadDocument(fileBuffer: Buffer, fileName: string): Promise<{
    success: boolean;
    document_id: string;
    chunks_count: number;
    message: string;
  }> {
    const formData = new FormData();
    const blob = new Blob([new Uint8Array(fileBuffer)], { type: 'application/octet-stream' });
    formData.append('file', blob, fileName);

    const response = await fetch(`${this.baseUrl}/internal/documents/upload`, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(60_000),
    });

    if (!response.ok) {
      const err = await response.text().catch(() => '');
      throw new Error(`Python 模型层错误 (${response.status}): ${err}`);
    }

    return response.json();
  }

  /**
   * 清空文档
   */
  async clearDocuments(): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/internal/documents/clear`, {
      method: 'DELETE',
      signal: AbortSignal.timeout(10_000),
    });

    if (!response.ok) {
      const err = await response.text().catch(() => '');
      throw new Error(`Python 模型层错误 (${response.status}): ${err}`);
    }

    return response.json();
  }

  /**
   * 获取文档数量
   */
  async getDocumentCount(): Promise<{ count: number }> {
    const response = await fetch(`${this.baseUrl}/internal/documents/count`, {
      signal: AbortSignal.timeout(10_000),
    });

    if (!response.ok) {
      const err = await response.text().catch(() => '');
      throw new Error(`Python 模型层错误 (${response.status}): ${err}`);
    }

    return response.json();
  }
}

export const pythonClient = new PythonModelClient();