  const API_BASE_URL = '/api';

export async function sendChat(
  question: string,
  history: any[],
  sessionId?: string
): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      history,
      session_id: sessionId || null,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || '发送消息失败');
  }

  return response.json();
}

/**
 * 流式发送消息，接收 SSE 事件流
 * 回调参数 event: { type: 'thinking'|'token'|'done'|'session_id'|'error', content?: string, sources?, tools_used? }
 */
export async function sendChatStream(
  question: string,
  history: any[],
  onEvent: (event: any) => void,
  sessionId?: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      history,
      session_id: sessionId || null,
    }),
  });

  if (!response.ok) {
    throw new Error('发送消息失败');
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('无法读取响应流');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6));
          onEvent(event);
        } catch {
          // 忽略解析失败的行
        }
      }
    }
  }
}

export async function uploadDocument(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || '上传文档失败');
  }

  return response.json();
}

export async function getDocumentCount(): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/documents/count`);
  if (!response.ok) {
    throw new Error('获取文档数量失败');
  }
  const data = await response.json();
  return data.count;
}

export async function clearDocuments(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/documents/clear`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('清空文档失败');
  }
}

// ========== 会话管理 ==========

export async function createSession(title?: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: title || '新对话' }),
  });
  if (!response.ok) throw new Error('创建会话失败');
  const data = await response.json();
  return data.session_id;
}

export async function listSessions(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/sessions`);
  if (!response.ok) throw new Error('获取会话列表失败');
  const data = await response.json();
  return data.sessions || [];
}

export async function getSession(sessionId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
  if (!response.ok) throw new Error('获取会话失败');
  return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('删除会话失败');
}
