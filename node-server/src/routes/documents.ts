/**
 * 文档路由 — 处理 /api/documents/*
 */
import { Router, Request, Response } from 'express';
import multer from 'multer';
import { pythonClient } from '../services/pythonClient.js';

export const documentsRouter = Router();

// 使用 multer 处理文件上传（内存存储）
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
});

/**
 * POST /api/documents/upload — 上传文档
 */
documentsRouter.post('/documents/upload', upload.single('file'), async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      res.status(400).json({ detail: '请上传文件' });
      return;
    }

    const result = await pythonClient.uploadDocument(req.file.buffer, req.file.originalname);
    res.json(result);
  } catch (err: any) {
    console.error('[documents/upload] 错误:', err.message);
    res.status(500).json({ detail: '服务器内部错误，请稍后重试' });
  }
});

/**
 * DELETE /api/documents/clear — 清空所有文档
 */
documentsRouter.delete('/documents/clear', async (_req: Request, res: Response) => {
  try {
    const result = await pythonClient.clearDocuments();
    res.json(result);
  } catch (err: any) {
    console.error('[documents/clear] 错误:', err.message);
    res.status(500).json({ detail: err.message });
  }
});

/**
 * GET /api/documents/count — 获取文档数量
 */
documentsRouter.get('/documents/count', async (_req: Request, res: Response) => {
  try {
    const result = await pythonClient.getDocumentCount();
    res.json(result);
  } catch (err: any) {
    console.error('[documents/count] 错误:', err.message);
    res.status(500).json({ detail: err.message });
  }
});