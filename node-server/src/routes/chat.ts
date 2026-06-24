/**
 * 对话路由 — 处理 /api/chat 和 /api/chat/stream
 */
import { Router, Request, Response } from 'express';
import { pythonClient } from '../services/pythonClient.js';
import { sessionStore } from '../services/sessionStore.js';
import type { ChatRequest, ChatMessage } from '../types.js';

export const chatRouter = Router();

function getHistory(body: ChatRequest): ChatMessage[] {
  if (body.session_id) {
    const stored = sessionStore.getHistoryForLLM(body.session_id);
    if (stored.length > 0) return stored;
  }
  return body.history || [];
}

/**
 * POST /api/chat — 非流式对话
 */
chatRouter.post('/chat', async (req: Request, res: Response) => {
  try {
    const body = req.body as ChatRequest;
    const sessionId = body.session_id || sessionStore.createSession();
    const history = getHistory(body);

    const result = await pythonClient.chat({ question: body.question, history });

    // 持久化本轮对话
    sessionStore.saveExchange(sessionId, body.question, result.answer);

    res.json({
      answer: result.answer,
      session_id: sessionId,
      sources: result.sources || [],
      tools_used: result.tools_used || [],
    });
  } catch (err: any) {
    console.error('[chat] 错误:', err.message);
    res.status(500).json({ detail: '服务器内部错误，请稍后重试' });
  }
});

/**
 * POST /api/chat/stream — 流式对话（SSE 代理）
 */
chatRouter.post('/chat/stream', async (req: Request, res: Response) => {
  const body = req.body as ChatRequest;
  const sessionId = body.session_id || sessionStore.createSession();
  const history = getHistory(body);

  // 设置 SSE 响应头
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no'); // 禁用 nginx 缓冲

  let fullAnswer = '';

  try {
    const stream = await pythonClient.chatStream({ question: body.question, history });

    const reader = stream.getReader();
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
          // 透传 Python 模型层的 SSE 事件
          const data = line.slice(6);
          res.write(`data: ${data}\n\n`);

          // 累积回答文本
          try {
            const event = JSON.parse(data);
            if (event.type === 'token' && event.content) {
              fullAnswer += event.content;
            }
          } catch {}
        }
      }
    }

    // 持久化本轮对话
    sessionStore.saveExchange(sessionId, body.question, fullAnswer);
    res.write(`data: ${JSON.stringify({ type: 'session_id', content: sessionId })}\n\n`);
  } catch (err: any) {
    console.error('[chat/stream] 错误:', err.message);
    res.write(`data: ${JSON.stringify({ type: 'error', content: err.message })}\n\n`);
  } finally {
    res.end();
  }
});