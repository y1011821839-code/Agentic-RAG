from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class Message(BaseModel):
    """对话消息"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = datetime.now()


class Document(BaseModel):
    """文档模型"""
    id: str
    content: str
    metadata: dict = {}


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str
    session_id: Optional[str] = None
    history: List[Message] = []


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    session_id: str = ""
    sources: List[dict] = []
    tools_used: List[str] = []


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool
    document_id: str
    chunks_count: int
    message: str
