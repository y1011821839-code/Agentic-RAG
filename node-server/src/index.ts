/**
 * Node.js 接入层 — API 网关入口
 *
 * 职责：
 * 1. 请求路由和校验
 * 2. SSE 流式代理到 Python 模型层
 * 3. 会话管理 (SQLite)
 * 4. 限流保护
 * 5. CORS 处理
 */
import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { chatRouter } from './routes/chat.js';
import { documentsRouter } from './routes/documents.js';
import { sessionsRouter } from './routes/sessions.js';
import { requestLogger } from './middleware/logger.js';

const PORT = parseInt(process.env.ACCESS_PORT || '3001', 10);

const app = express();

// ========== 中间件 ==========

// CORS
app.use(cors({
  origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
  credentials: true,
}));

// 请求日志
app.use(requestLogger);

// JSON 解析
app.use(express.json({ limit: '1mb' }));

// 全局限流 — 每 IP 每分钟最多 60 次请求
app.use(rateLimit({
  windowMs: 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
  message: { detail: '请求过于频繁，请稍后再试' },
}));

// 聊天接口单独限流 — 每分钟 20 次
const chatLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { detail: '对话请求过于频繁，请稍后再试' },
});

// ========== 路由 ==========

// 健康检查
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', service: 'agentic-rag-access-layer' });
});

// 聊天路由（带限流）
app.use('/api', chatLimiter, chatRouter);

// 文档路由
app.use('/api', documentsRouter);

// 会话路由
app.use('/api', sessionsRouter);

// ========== 启动 ==========

app.listen(PORT, () => {
  console.log('========================================');
  console.log(`  Node.js 接入层已启动: http://localhost:${PORT}`);
  console.log(`  Python 模型层: ${process.env.PYTHON_MODEL_URL || 'http://localhost:8000'}`);
  console.log('========================================');
});