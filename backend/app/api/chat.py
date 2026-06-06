"""
API Routes - 对话接口
"""
import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse
from app.core.agent import agent
from app.core.session_store import session_store

router = APIRouter(prefix="/api", tags=["chat"])


def _get_history(request: ChatRequest) -> list:
    """获取对话历史：优先从 session_store 加载，其次用请求中的 history"""
    if request.session_id:
        stored = session_store.get_history_for_llm(request.session_id)
        if stored:
            return stored
    return [msg.model_dump() for msg in request.history]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理用户对话（非流式）"""
    try:
        # 自动创建或复用会话
        session_id = request.session_id or session_store.create_session()
        history = _get_history(request)

        result = await agent.process(
            question=request.question,
            history=history
        )

        # 持久化本轮对话
        session_store.save_exchange(session_id, request.question, result["answer"])

        return ChatResponse(
            answer=result["answer"],
            session_id=session_id,
            sources=result["sources"],
            tools_used=result["tools_used"]
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="服务器内部错误，请稍后重试")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """处理用户对话（流式输出 + 思考状态）"""
    async def event_generator():
        try:
            session_id = request.session_id or session_store.create_session()
            history = _get_history(request)

            full_answer = ""
            async for event in agent.process_stream(
                question=request.question,
                history=history
            ):
                if event.get("type") == "token":
                    full_answer += event["content"]
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # 持久化本轮对话
            session_store.save_exchange(session_id, request.question, full_answer)
            yield f"data: {json.dumps({'type': 'session_id', 'content': session_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            traceback.print_exc()
            error_msg = str(e) if str(e) else type(e).__name__
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
