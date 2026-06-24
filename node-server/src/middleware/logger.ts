/**
 * 请求日志中间件
 */
import { Request, Response, NextFunction } from 'express';

export function requestLogger(req: Request, _res: Response, next: NextFunction) {
  const timestamp = new Date().toISOString().slice(11, 19);
  console.log(`[${timestamp}] ${req.method} ${req.path}`);
  next();
}