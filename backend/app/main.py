"""
FastAPI 模型层 — 仅供 Node.js 接入层内部调用
"""
from fastapi import FastAPI
from app.api.internal import router as internal_router
from app.config import HOST, PORT

app = FastAPI(
    title="Agentic RAG 模型层",
    description="Agentic RAG 模型层 — 内部 API（LLM / 检索 / Agent）",
    version="1.0.0"
)

# 注册内部路由
app.include_router(internal_router)


@app.get("/")
async def root():
    return {
        "service": "agentic-rag-model-layer",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)