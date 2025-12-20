"""MCP Client - 连接到 Windows-MCP Server（使用官方 SDK）"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class MCPResponse:
    """MCP 响应标准化格式"""
    success: bool
    content: str = ""
    error: Optional[str] = None
    raw: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error
        }


class MCPClient:
    """
    MCP (Model Context Protocol) Client

    连接到 Windows-MCP Server 并调用其提供的工具

    使用官方 mcp SDK 进行异步通信
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools: List[Dict[str, Any]] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def start_server(self) -> bool:
        """
        启动并连接到 Windows-MCP Server

        Returns:
            是否成功启动
        """
        try:
            self.logger.info("正在连接到 Windows-MCP Server...")

            # 配置服务器参数（通过 uvx 启动）
            server_params = StdioServerParameters(
                command="uvx",
                args=["windows-mcp"],
                env=None
            )

            # 建立 stdio 传输通道
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport

            # 创建客户端会话
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            # 初始化连接（三步握手）
            await self.session.initialize()

            # 获取工具列表
            await self.refresh_tools()

            self.logger.info(f"✓ Windows-MCP Server 已启动")
            self.logger.info(f"✓ 可用工具数量: {len(self.available_tools)}")
            return True

        except Exception as e:
            self.logger.error(f"启动 MCP Server 失败: {e}")
            return False

    async def refresh_tools(self):
        """刷新工具列表"""
        if not self.session:
            return

        response = await self.session.list_tools()
        self.available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in response.tools
        ]

    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表"""
        return self.available_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> MCPResponse:
        """
        调用 MCP 工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            MCPResponse 对象
        """
        if not self.session:
            return MCPResponse(success=False, error="MCP Server 未连接")

        try:
            args = arguments or {}
            self.logger.debug(f"调用工具: {tool_name}, 参数: {args}")
            result = await self.session.call_tool(tool_name, args)

            # 解析结果
            if hasattr(result, 'content') and result.content:
                # 提取文本内容
                text_content = []
                for item in result.content:
                    if hasattr(item, 'type') and item.type == "text":
                        text_content.append(item.text)

                is_error = getattr(result, 'isError', False)
                content_str = "\n".join(text_content) if text_content else str(result)

                return MCPResponse(
                    success=not is_error,
                    content=content_str,
                    error=content_str if is_error else None,
                    raw=result
                )
            else:
                return MCPResponse(
                    success=True,
                    content=str(result),
                    raw=result
                )

        except Exception as e:
            self.logger.error(f"调用工具失败 {tool_name}: {e}")
            return MCPResponse(success=False, error=str(e))

    async def stop_server(self):
        """停止 MCP Server"""
        try:
            await self.exit_stack.aclose()
            self.logger.info("✓ Windows-MCP Server 已停止")
        except Exception as e:
            self.logger.error(f"停止服务器失败: {e}")

    # ==================== 高级封装（基于 Windows-MCP 工具）====================

    async def get_state(self, use_vision: bool = False, use_dom: bool = False) -> MCPResponse:
        """
        获取屏幕状态（State-Tool）

        Args:
            use_vision: 是否包含截图
            use_dom: 是否使用 DOM 模式

        Returns:
            屏幕状态信息
        """
        return await self.call_tool("State-Tool", {
            "use_vision": use_vision,
            "use_dom": use_dom
        })

    async def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> MCPResponse:
        """
        点击屏幕（Click-Tool）
        """
        return await self.call_tool("Click-Tool", {
            "x": x,
            "y": y,
            "button": button,
            "clicks": clicks
        })

    async def type_text(self, text: str, clear: bool = False) -> MCPResponse:
        """
        输入文字（Type-Tool）
        """
        return await self.call_tool("Type-Tool", {
            "text": text,
            "clear": clear
        })

    async def shortcut(self, keys: str) -> MCPResponse:
        """
        按快捷键（Shortcut-Tool）
        """
        return await self.call_tool("Shortcut-Tool", {
            "keys": keys
        })

    async def scroll(self, direction: str, amount: int = 3) -> MCPResponse:
        """
        滚动（Scroll-Tool）
        """
        return await self.call_tool("Scroll-Tool", {
            "direction": direction,
            "amount": amount
        })

    async def launch_app(self, app_name: str) -> MCPResponse:
        """
        启动应用（App-Tool）
        """
        return await self.call_tool("App-Tool", {
            "action": "launch",
            "app_name": app_name
        })

    async def scrape_webpage(self) -> MCPResponse:
        """
        抓取网页（Scrape-Tool）
        """
        return await self.call_tool("Scrape-Tool", {})


# ==================== 同步封装器 ====================

class MCPClientSync:
    """
    MCP Client 的同步封装

    在同步代码中使用异步 MCP Client
    """

    def __init__(self):
        self.client = MCPClient()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._started = False

    def start(self) -> bool:
        """启动 MCP Server（同步）"""
        if self._started:
            return True

        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 启动服务器
        success = self.loop.run_until_complete(self.client.start_server())
        self._started = success
        return success

    def stop(self):
        """停止 MCP Server（同步）"""
        if not self._started or not self.loop:
            return

        # 停止服务器
        self.loop.run_until_complete(self.client.stop_server())
        self.loop.close()
        self._started = False

    def list_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表（同步）"""
        if not self._started:
            return []
        return self.loop.run_until_complete(self.client.list_tools())

    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> MCPResponse:
        """调用工具（同步）"""
        if not self._started:
            return MCPResponse(success=False, error="MCP Server 未启动")
        return self.loop.run_until_complete(self.client.call_tool(tool_name, arguments))

    def get_state(self, use_vision: bool = False, use_dom: bool = False) -> MCPResponse:
        """获取屏幕状态（同步）"""
        return self.call_tool("State-Tool", {
            "use_vision": use_vision,
            "use_dom": use_dom
        })

    def click(self, x: int, y: int) -> MCPResponse:
        """点击（同步）"""
        return self.call_tool("Click-Tool", {"x": x, "y": y})

    def type_text(self, text: str) -> MCPResponse:
        """输入文字（同步）"""
        return self.call_tool("Type-Tool", {"text": text})

    def shortcut(self, keys: str) -> MCPResponse:
        """快捷键（同步）"""
        return self.call_tool("Shortcut-Tool", {"keys": keys})


# ==================== 测试代码 ====================

async def test_mcp_client():
    """测试 MCP Client"""
    client = MCPClient()

    try:
        # 启动服务器
        print("启动 MCP Server...")
        success = await client.start_server()
        if not success:
            print("❌ 启动失败")
            return

        # 列出工具
        print("\n可用工具:")
        tools = await client.list_tools()
        for tool in tools[:10]:  # 只显示前10个
            print(f"  - {tool['name']}: {tool['description']}")

        # 测试获取状态
        print("\n测试 State-Tool:")
        state = await client.get_state()
        print(f"成功: {state.get('success')}")

        # 测试快捷键
        print("\n测试快捷键 (Win+R):")
        result = await client.shortcut("Win+r")
        print(f"结果: {result}")

    finally:
        await client.stop_server()


if __name__ == "__main__":
    asyncio.run(test_mcp_client())
