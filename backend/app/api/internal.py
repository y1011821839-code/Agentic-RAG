"""
内部 API — 仅供 Node.js 接入层调用
不对外暴露，无需处理会话管理（Node.js 负责）
"""
import json
import traceback
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.core.agent import agent
from app.core.retriever import retriever
from app.core.document_processor import document_processor

router = APIRouter(prefix="/internal", tags=["internal"])


# ====== 请求/响应模型 ======

class InternalChatRequest(BaseModel):
    question: str
    history: List[Dict] = []


class InternalChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    tools_used: List[str] = []


class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: str
    chunks_count: int
    message: str


# ====== 对话 ======

@router.post("/chat", response_model=InternalChatResponse)
async def internal_chat(request: InternalChatRequest):
    """非流式对话（内部）"""
    try:
        result = await agent.process(
            question=request.question,
            history=request.history
        )
        return InternalChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            tools_used=result["tools_used"]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="模型层内部错误")


@router.post("/chat/stream")
async def internal_chat_stream(request: InternalChatRequest):
    """流式对话（内部）— 返回 SSE 事件流"""
    async def event_generator():
        try:
            async for event in agent.process_stream(
                question=request.question,
                history=request.history
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ====== 文档管理 ======

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def internal_upload_document(file: UploadFile = File(...)):
    """上传文档（内部）"""
    try:
        content = await file.read()

        if file.filename.endswith('.txt') or file.filename.endswith('.md'):
            text = content.decode('utf-8')
        else:
            try:
                text = content.decode('utf-8')
            except Exception:
                raise HTTPException(status_code=400, detail="暂不支持的文件格式")

        documents = document_processor.process_file(
            file_path=file.filename or "unknown",
            content=text
        )

        if not documents:
            raise HTTPException(status_code=400, detail="文档内容为空")

        await retriever.add_documents(documents)

        return DocumentUploadResponse(
            success=True,
            document_id=documents[0]["id"].split('_')[0],
            chunks_count=len(documents),
            message=f"成功处理 {len(documents)} 个文档块"
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.delete("/documents/clear")
async def internal_clear_documents():
    """清空文档（内部）"""
    try:
        retriever.delete_all()
        return {"success": True, "message": "已清空所有文档"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/count")
async def internal_get_document_count():
    """获取文档数量（内部）"""
    try:
        count = retriever.get_count()
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))