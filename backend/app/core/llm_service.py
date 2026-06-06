"""
LLM Service - 阿里千问 DashScope（对话 + Embedding）
"""
import asyncio
import json
import httpx
from typing import List, Dict, AsyncIterator
from app.config import DASHSCOPE_API_KEY, LLM_MODEL, EMBEDDING_MODEL, BASE_URL


class LLMService:
    def __init__(self):
        self.api_key = DASHSCOPE_API_KEY
        self.model = LLM_MODEL
        self.embedding_model = EMBEDDING_MODEL
        self.chat_url = f"{BASE_URL}/chat/completions"
        self.embedding_url = f"{BASE_URL}/embeddings"

    def _build_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_messages(self, prompt: str, system_prompt: str, context_docs: List[Dict] = None, history: List[Dict] = None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if context_docs:
            context_text = "\n\n".join([
                f"文档{i+1}: {doc['content']}"
                for i, doc in enumerate(context_docs)
            ])
            messages.append({
                "role": "system",
                "content": f"以下是相关的知识库内容：\n{context_text}"
            })

        # 注入历史对话（最多保留最近 5 轮）
        if history:
            for msg in history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": prompt})
        return messages

    async def _post_with_retry(
        self, url: str, headers: dict, payload: dict, max_retries: int = 3
    ) -> dict:
        """带重试的 POST 请求，自动处理 429 限流"""
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 429:
                    wait_time = (attempt + 1) * 3
                    print(f"⚠️ API 限流 (429)，第 {attempt + 1}/{max_retries} 次重试，等待 {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

        raise Exception("API 调用失败：超过最大重试次数（速率限制）")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        context_docs: List[Dict] = None,
        history: List[Dict] = None,
        temperature: float = 0.7
    ) -> str:
        """生成回答（非流式）"""
        messages = self._build_messages(prompt, system_prompt, context_docs, history)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        data = await self._post_with_retry(self.chat_url, self._build_headers(), payload)
        return data["choices"][0]["message"]["content"]

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "",
        context_docs: List[Dict] = None,
        history: List[Dict] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """流式生成回答，逐 token 返回（含连接重试）"""
        messages = self._build_messages(prompt, system_prompt, context_docs, history)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST", self.chat_url,
                        headers=self._build_headers(),
                        json=payload
                    ) as response:
                        if response.status_code == 429:
                            wait_time = (attempt + 1) * 3
                            print(f"⚠️ 流式 API 限流 (429)，第 {attempt + 1}/3 次重试，等待 {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    return
                                try:
                                    data = json.loads(data_str)
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                                except json.JSONDecodeError:
                                    continue
                        return  # 正常完成
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = (attempt + 1) * 3
                    print(f"⚠️ 流式 API 限流 (429)，第 {attempt + 1}/3 次重试，等待 {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
                if attempt < 2:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ 流式连接失败: {e}，第 {attempt + 1}/3 次重试，等待 {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise

        raise Exception("流式 API 调用失败：超过最大重试次数")

    async def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict],
        system_prompt: str = "",
        history: List[Dict] = None,
    ) -> List[Dict]:
        """Function Calling：让 LLM 决定调用哪些工具"""
        messages = self._build_messages(prompt, system_prompt, None, history)

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools_schema,
            "temperature": 0.1  # 低温度提高决策稳定性
        }

        data = await self._post_with_retry(self.chat_url, self._build_headers(), payload)
        choice = data["choices"][0]
        msg = choice.get("message", {})

        tool_calls = msg.get("tool_calls", [])
        result = []
        for tc in tool_calls:
            try:
                result.append({
                    "name": tc["function"]["name"],
                    "arguments": json.loads(tc["function"]["arguments"])
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return result

    async def get_embedding(self, text: str) -> List[float]:
        """获取文本向量"""
        payload = {
            "model": self.embedding_model,
            "input": text
        }

        data = await self._post_with_retry(
            self.embedding_url, self._build_headers(), payload
        )
        return data["data"][0]["embedding"]


# 全局实例
llm_service = LLMService()
