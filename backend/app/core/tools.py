"""
Tools - 可调用的工具集（计算器、名言、IP查询）
"""
import ast
import operator
import httpx
import re
from urllib.parse import quote
from typing import Dict, Any
from abc import ABC, abstractmethod


# AST 安全计算器
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval_node(node):
    """递归求值 AST 节点（仅白名单运算符）"""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Num):  # Python 3.7
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的运算符")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval_node(node.operand)
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的运算符")
        return op(operand)
    else:
        raise ValueError("不支持的表达式类型")


def safe_eval(expr_str: str) -> str:
    """AST 白名单安全计算"""
    try:
        cleaned = re.sub(r'[^0-9+\-*/().%^]', '', expr_str)
        if not cleaned:
            return "计算错误: 空表达式"
        tree = ast.parse(cleaned, mode='eval')
        return str(_safe_eval_node(tree.body))
    except ZeroDivisionError:
        return "错误: 除数不能为零"
    except Exception as e:
        return f"计算错误: {str(e)}"


class BaseTool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行工具"""
        pass


class CalculatorTool(BaseTool):
    """计算器工具"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "用于数学计算，输入数学表达式，返回计算结果"

    async def execute(self, expression: str) -> str:
        """执行数学计算"""
        return safe_eval(expression)


class QuoteTool(BaseTool):
    """随机名言工具 - 使用 hitokoto API"""

    @property
    def name(self) -> str:
        return "quote"

    @property
    def description(self) -> str:
        return "获取一句随机名言或励志语录"

    async def execute(self, category: str = "") -> str:
        """获取随机名言"""
        try:
            url = "https://v1.hitokoto.cn/"
            params = {"c": category} if category else {}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    quote = data.get("hitokoto", "")
                    source = data.get("from", "未知")
                    return f"「{quote}」\n—— {source}"
                else:
                    return "名言获取失败"

        except Exception as e:
            return f"名言获取失败: {str(e)}"


class IPTool(BaseTool):
    """IP 信息查询工具 - 使用 ip-api.com"""

    @property
    def name(self) -> str:
        return "ip"

    @property
    def description(self) -> str:
        return "查询 IP 地址或域名的归属地信息"

    async def execute(self, ip: str = "") -> str:
        """查询 IP 归属地"""
        try:
            target = ip.strip() if ip.strip() else ""
            url = f"http://ip-api.com/json/{quote(target)}?lang=zh-CN"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return (
                            f"IP 信息查询结果：\n"
                            f"- IP 地址：{data.get('query', 'N/A')}\n"
                            f"- 国家：{data.get('country', 'N/A')}\n"
                            f"- 城市：{data.get('city', 'N/A')}\n"
                            f"- ISP：{data.get('isp', 'N/A')}\n"
                            f"- 经纬度：{data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}"
                        )
                    else:
                        return f"查询失败: {data.get('message', '未知错误')}"
                else:
                    return "IP 查询服务暂时不可用"

        except Exception as e:
            return f"IP 查询失败: {str(e)}"


class ToolManager:
    """工具管理器"""

    def __init__(self):
        self.tools = {
            "calculator": CalculatorTool(),
            "quote": QuoteTool(),
            "ip": IPTool()
        }

    def get_tool(self, name: str) -> BaseTool:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> Dict[str, str]:
        """列出所有工具"""
        return {
            name: tool.description
            for name, tool in self.tools.items()
        }

    async def execute_tool(self, tool_name: str, **kwargs) -> str:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if tool:
            return await tool.execute(**kwargs)
        return f"未找到工具: {tool_name}"


# 全局实例
tool_manager = ToolManager()
