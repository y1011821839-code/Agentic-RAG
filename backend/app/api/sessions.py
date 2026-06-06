"""
会话管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.session_store import session_store

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SaveMessageRequest(BaseModel):
    question: str
    answer: str


class CreateSessionRequest(BaseModel):
    title: str = "新对话"


@router.get("")
async def list_sessions():
    """获取所有会话列表"""
    return {"sessions": session_store.list_sessions()}


@router.post("")
async def create_session(req: CreateSessionRequest = None):
    """创建新会话，返回 session_id"""
    title = req.title if req else "新对话"
    session_id = session_store.create_session(title)
    return {"session_id": session_id}


@router.get("/{session_id}")
async def get_session(session_id: str):
    """获取指定会话的消息历史"""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = session_store.get_messages(session_id)
    return {"session": session, "messages": messages}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    session_store.delete_session(session_id)
    return {"ok": True}


@router.post("/{session_id}/messages")
async def save_message(session_id: str, req: SaveMessageRequest):
    """保存一轮对话"""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    session_store.save_exchange(session_id, req.question, req.answer)
    return {"ok": True}