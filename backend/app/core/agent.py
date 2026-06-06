"""
Agent - 智能代理核心模块
"""
import re
from typing import List, Dict, Tuple, Optional
from app.core.retriever import retriever
from app.core.llm_service import llm_service
from app.core.tools import tool_manager


class Agent:
    def __init__(self):
        self.tools = tool_manager

    def get_tools_schema(self) -> List[Dict]:
        """生成 Function Calling 用的 tools schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "执行数学计算，支持加减乘除等运算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "数学表达式，如 '123+456'"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "quote",
                    "description": "获取一条名人名言或励志格言",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ip",
                    "description": "查询 IP 地址或域名的归属地信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ip": {
                                "type": "string",
                                "description": "IP 地址或域名，留空则查询本机"
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def decide_action_local(self, question: str) -> List[str]:
        """本地关键词匹配决定操作（不消耗 API 配额）"""
        tools_needed = []

        # 计算器：包含数学表达式
        if re.search(r'[\d]+\s*[\+\-\*\/\^]\s*[\d]+', question) or \
           re.search(r'(计算|等于多少|算一下|多少\+多少|多少\-多少|多少\*多少|多少\/多少)', question):
            tools_needed.append("calculator")

        # 名言/名言警句/励志
        if re.search(r'(名言|名言警句|励志|格言|座右铭|一句话|毒鸡汤)', question):
            tools_needed.append("quote")

        # IP 查询
        if re.search(r'(IP地址|IP归属|查.*IP|IP.*查询|IP.*属于|IP.*位置|\d+\.\d+\.\d+\.\d+)', question):
            tools_needed.append("ip")

        return tools_needed

    async def decide_action_with_llm(self, question: str, history: List[Dict] = None) -> List[Dict]:
        """通过 Function Calling 让 LLM 决定调用哪些工具"""
        tools_schema = self.get_tools_schema()
        system_prompt = "你是一个工具调度助手。根据用户问题判断需要调用哪些工具。如果不需要任何工具，返回空列表。"
        return await llm_service.generate_with_tools(
            prompt=question,
            tools_schema=tools_schema,
            system_prompt=system_prompt,
            history=history,
        )

    async def decide_action(self, question: str, history: List[Dict] = None) -> Tuple[List[str], List[Dict]]:
        """
        决定需要执行的操作：先用本地正则，再用 LLM Function Calling 兜底
        """
        local_tools = self.decide_action_local(question)
        if local_tools:
            return local_tools, []

        # 本地未匹配时，用 LLM Function Calling
        try:
            llm_tool_calls = await self.decide_action_with_llm(question, history)
            tool_names = [tc["name"] for tc in llm_tool_calls if tc["name"] in self.tools.tools]
            return [], llm_tool_calls
        except Exception:
            return [], []

    async def extract_parameters(self, question: str, tool_name: str, llm_arguments: Dict = None) -> Dict:
        """提取工具参数，优先使用 LLM 给出的参数"""
        if llm_arguments:
            return llm_arguments

        if tool_name == "calculator":
            # 提取数学表达式
            expr = re.sub(r'.*?(=\s*|\+\s*|\-\s*|\*\s*|\/\s*)', '', question)
            expr = re.sub(r'[等于加减乘除分别是和]', ' ', expr)
            expr = re.sub(r'\s+', '', expr)
            return {"expression": expr or "0"}

        elif tool_name == "quote":
            return {}

        elif tool_name == "ip":
            # 提取 IP 地址
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', question)
            if ip_match:
                return {"ip": ip_match.group(1)}
            # 尝试提取域名
            domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})', question)
            if domain_match:
                return {"ip": domain_match.group(1)}
            return {"ip": ""}  # 空则查询本机 IP

        return {}

    async def _rewrite_query(self, question: str) -> str:
        """将用户问题改写为检索关键词（仅对长问题改写）"""
        if len(question) <= 20:
            return question
        try:
            result = await llm_service.generate(
                prompt=f"将以下问题转换为简短的关键词用于检索（不超过15字，直接输出关键词不要解释）：{question}",
                system_prompt="你是查询改写助手，只输出关键词。",
                temperature=0
            )
            rewritten = result.strip().replace("关键词：", "").replace("检索关键词：", "")
            if rewritten and len(rewritten) <= 30:
                return rewritten
        except Exception:
            pass
        return question

    async def process(self, question: str, history: List[Dict] = None) -> Dict:
        """
        处理用户问题

        Returns:
            {
                "answer": str,           # 最终回答
                "sources": List[dict],    # 检索来源
                "tools_used": List[str]   # 使用的工具
            }
        """
        tools_used = []
        context_docs = []
        tool_results = {}
        relevant_docs = []

        # 1. 决定是否需要检索
        local_tools, llm_tool_calls = await self.decide_action(question, history)

        # 合并本地和 LLM 工具决策
        all_tools = []
        all_tools.extend(local_tools)
        all_tools.extend([tc["name"] for tc in llm_tool_calls])
        llm_args_map = {tc["name"]: tc["arguments"] for tc in llm_tool_calls}

        # 2. 执行工具
        for tool_name in all_tools:
            params = await self.extract_parameters(question, tool_name, llm_args_map.get(tool_name))
            result = await self.tools.execute_tool(tool_name, **params)
            tool_results[tool_name] = result
            tools_used.append(tool_name)

        # 3. 检索知识库（纯工具问题跳过检索，节约 API）
        if not local_tools:
            search_query = await self._rewrite_query(question)
            relevant_docs = await retriever.search(search_query, top_k=3)
            if relevant_docs:
                context_docs = relevant_docs

        # 4. 构建提示词并生成回答
        system_prompt = """你是一个智能问答助手，负责根据知识库内容和对话历史回答用户问题。
请基于提供的文档内容进行回答，如果文档中没有相关信息，请如实说明。
回答要准确、简洁、有条理。"""

        # 添加工具结果到提示词
        additional_context = ""
        if tool_results:
            additional_context = "\n\n工具执行结果：\n" + "\n".join([
                f"- {name}: {result}"
                for name, result in tool_results.items()
            ])

        # 构建用户提示
        user_prompt = question
        if additional_context:
            user_prompt += additional_context

        # 5. 生成回答
        answer = await llm_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            context_docs=context_docs,
            history=history
        )

        return {
            "answer": answer,
            "sources": relevant_docs,
            "tools_used": tools_used
        }

    async def process_stream(self, question: str, history: List[Dict] = None):
        """
        流式处理用户问题，逐 token 返回，并发送思考状态事件

        Yields:
            dict: {"type": "thinking"|"token"|"done", "content": str, ...}
        """
        tools_used = []
        context_docs = []
        tool_results = {}
        relevant_docs = []

        # 1. 决定是否需要检索
        yield {"type": "thinking", "content": "正在分析问题..."}
        local_tools, llm_tool_calls = await self.decide_action(question, history)

        # 合并工具
        all_tools = []
        all_tools.extend(local_tools)
        all_tools.extend([tc["name"] for tc in llm_tool_calls])
        llm_args_map = {tc["name"]: tc["arguments"] for tc in llm_tool_calls}

        # 2. 执行工具
        for tool_name in all_tools:
            tool_labels = {
                "calculator": "正在计算...",
                "quote": "正在获取名言...",
                "ip": "正在查询 IP 信息..."
            }
            yield {"type": "thinking", "content": tool_labels.get(tool_name, f"正在执行: {tool_name}")}
            params = await self.extract_parameters(question, tool_name, llm_args_map.get(tool_name))
            result = await self.tools.execute_tool(tool_name, **params)
            tool_results[tool_name] = result
            tools_used.append(tool_name)
            yield {"type": "thinking", "content": f"工具执行完成：{tool_name}"}

        # 3. 检索知识库（纯工具问题跳过检索，节约 API）
        if not local_tools:
            yield {"type": "thinking", "content": "正在检索知识库..."}
            search_query = await self._rewrite_query(question)
            relevant_docs = await retriever.search(search_query, top_k=3)
            if relevant_docs:
                context_docs = relevant_docs
                yield {"type": "thinking", "content": f"找到 {len(relevant_docs)} 篇相关文档"}

        # 4. 构建提示词
        system_prompt = """你是一个智能问答助手，负责根据知识库内容和对话历史回答用户问题。
请基于提供的文档内容进行回答，如果文档中没有相关信息，请如实说明。
回答要准确、简洁、有条理。"""

        additional_context = ""
        if tool_results:
            additional_context = "\n\n工具执行结果：\n" + "\n".join([
                f"- {name}: {result}"
                for name, result in tool_results.items()
            ])

        user_prompt = question
        if additional_context:
            user_prompt += additional_context

        # 5. 流式生成回答
        yield {"type": "thinking", "content": "正在生成回答..."}

        async for token in llm_service.stream_generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            context_docs=context_docs,
            history=history
        ):
            yield {"type": "token", "content": token}

        # 6. 完成
        yield {
            "type": "done",
            "sources": relevant_docs,
            "tools_used": tools_used
        }


# 全局实例
agent = Agent()
