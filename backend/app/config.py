"""
配置管理 - 从环境变量读取
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

# 阿里千问 (DashScope) 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v2")

# API 端点（兼容 OpenAI 格式）
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Debug
if not DASHSCOPE_API_KEY:
    print("⚠️  警告: DASHSCOPE_API_KEY 未设置！请在 .env 文件中配置。")
else:
    print("✅ DASHSCOPE_API_KEY 已加载")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
