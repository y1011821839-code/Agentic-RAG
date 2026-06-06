"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat_router, documents_router
from app.api.sessions import router as sessions_router
from app.config import HOST, PORT

# 创建FastAPI应用
app = FastAPI(
    title="Agentic RAG API",
    description="Agentic RAG 智能问答系统 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(sessions_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Agentic RAG API",
        "docs": "/docs",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
