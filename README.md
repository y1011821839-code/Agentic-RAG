# Agentic RAG 智能问答系统

基于 **RAG（检索增强生成）+ Agent（智能代理）** 架构的本地智能问答系统。支持知识库文档问答、混合检索、工具调用（计算器/名言/IP查询）、流式输出、多轮对话持久化。

## 功能特性

- **知识库管理**：上传文档自动向量化存储（阿里千问 Embedding）
- **混合检索**：向量检索（ChromaDB）+ BM25 关键词检索，RRF 融合排序
- **语义分割**：按标点边界智能切分文档，避免 chunk 截断
- **查询改写**：长问题自动提炼为检索关键词，提升命中率
- **智能问答**：基于知识库内容精准回答，流式输出（SSE）
- **工具调用**：计算器（AST 安全沙箱）、名言（hitokoto API）、IP 查询（ip-api.com）
- **两级工具决策**：本地正则匹配优先（零 API 消耗），未命中时 LLM Function Calling 兜底
- **多轮对话**：对话历史注入 LLM 上下文，支持上下文记忆
- **对话持久化**：SQLite 存储会话，刷新页面恢复历史
- **思考状态**：前端实时显示"正在检索/正在计算/正在生成"等过程

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python + FastAPI |
| LLM | 阿里千问（DashScope），兼容 OpenAI 格式 |
| 向量数据库 | ChromaDB（本地持久化） |
| 混合检索 | 向量检索 + 自实现 BM25（中文 bigram 分词） |
| 前端 | React + TypeScript + TailwindCSS |
| 流式输出 | Server-Sent Events (SSE) |
| 会话存储 | SQLite |
| 工具集成 | hitokoto API、ip-api.com、AST 安全计算器 |

## 项目架构

```
agentic-rag/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py              # 对话接口（流式 + 非流式）
│   │   │   ├── documents.py         # 文档上传/管理
│   │   │   └── sessions.py          # 会话持久化 API
│   │   ├── core/
│   │   │   ├── agent.py             # Agent 决策（工具调度 + 查询改写）
│   │   │   ├── retriever.py         # 混合检索（向量 + BM25 + RRF）
│   │   │   ├── llm_service.py       # LLM 服务（对话 + Embedding + Function Calling）
│   │   │   ├── tools.py             # 工具集（计算器/名言/IP）
│   │   │   ├── document_processor.py # 语义分割
│   │   │   └── session_store.py     # SQLite 会话存储
│   │   ├── models/schemas.py        # 数据模型
│   │   ├── main.py                  # FastAPI 入口
│   │   └── config.py                # 环境变量配置
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/              # React 组件
│   │   ├── utils/api.ts             # API 封装（含 SSE 流式解析）
│   │   ├── App.tsx                  # 主组件（会话管理 + 流式渲染）
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
├── .env.example
└── README.md
```

## 核心设计

### Agent 决策流程

```
用户问题 → 正则匹配（免费） → 命中？→ 执行工具 → 跳过检索
                ↓ 未命中
         LLM Function Calling → 命中？→ 执行工具 + 检索知识库
                ↓ 未命中
         仅检索知识库 → 查询改写 → 混合检索 → LLM 生成回答
```

### 混合检索

```
用户查询 → 向量检索 (ChromaDB) ──┐
         → BM25 检索 (自实现)  ──┤
                                 ↓
                            RRF 融合排序
                                 ↓
                            Top-K 结果
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- 阿里千问 API Key（[获取地址](https://dashscope.console.aliyun.com/apiKey)）

### 2. 配置环境变量

```bash
cd backend
cp ../.env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY
```

### 3. 安装依赖 & 启动

**后端：**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

### 4. 访问系统

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs

## 使用说明

1. **上传文档**：左侧面板上传 .txt / .md 文件，自动语义分割并向量化
2. **提问**：在对话框输入问题，系统自动检索知识库并生成回答
3. **工具调用**：
   - 计算："123 + 456 等于多少"
   - 名言："来一句格言"
   - IP："查一下 8.8.8.8"
4. **多轮对话**：支持上下文连续问答，刷新页面历史不丢失

## 注意事项

- 阿里千问 API 按量计费，建议使用 `qwen-plus` 模型控制成本
- ChromaDB 数据存储在 `backend/chroma_db/`，清空知识库会删除此目录
- 会话数据存储在 `backend/sessions.db`（SQLite）