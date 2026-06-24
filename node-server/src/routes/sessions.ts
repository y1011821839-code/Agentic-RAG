/**
 * 会话管理路由 — 处理 /api/sessions/*
 */
import { Router, Request, Response } from 'express';
import { sessionStore } from '../services/sessionStore.js';

interface SaveMessageBody {
  question: string;
  answer: string;
}

interface CreateSessionBody {
  title: string;
}

export const sessionsRouter = Router();

/**
 * GET /api/sessions — 获取所有会话列表
 */
sessionsRouter.get('/sessions', (_req: Request, res: Response) => {
  const sessions = sessionStore.listSessions();
  res.json({ sessions });
});

/**
 * POST /api/sessions — 创建新会话
 */
sessionsRouter.post('/sessions', (req: Request, res: Response) => {
  const body = req.body as CreateSessionBody | undefined;
  const title = body?.title || '新对话';
  const sessionId = sessionStore.createSession(title);
  res.json({ session_id: sessionId });
});

/**
 * GET /api/sessions/:sessionId — 获取指定会话
 */
sessionsRouter.get('/sessions/:sessionId', (req: Request, res: Response) => {
  const session = sessionStore.getSession(req.params.sessionId);
  if (!session) {
    res.status(404).json({ detail: '会话不存在' });
    return;
  }
  const messages = sessionStore.getMessages(req.params.sessionId);
  res.json({ session, messages });
});

/**
 * DELETE /api/sessions/:sessionId — 删除会话
 */
sessionsRouter.delete('/sessions/:sessionId', (req: Request, res: Response) => {
  sessionStore.deleteSession(req.params.sessionId);
  res.json({ ok: true });
});

/**
 * POST /api/sessions/:sessionId/messages — 保存一轮对话
 */
sessionsRouter.post('/sessions/:sessionId/messages', (req: Request, res: Response) => {
  const session = sessionStore.getSession(req.params.sessionId);
  if (!session) {
    res.status(404).json({ detail: '会话不存在' });
    return;
  }
  const body = req.body as SaveMessageBody;
  sessionStore.saveExchange(req.params.sessionId, body.question, body.answer);
  res.json({ ok: true });
});