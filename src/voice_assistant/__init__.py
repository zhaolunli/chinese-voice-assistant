"""
智能语音助手 - 双阶段识别版
阶段1: KWS轻量级关键词检测（持续监听）
阶段2: ASR完整语音识别（唤醒后）
集成: Windows-MCP + React Agent + Vision
"""

from .wake_word import SmartWakeWordSystem
from .tts import TTSManager
from .vision import VisionUnderstanding
from .mcp_client import MCPClient, MCPClientSync, MCPManager, MCPManagerSync, MCPResponse
from .react_agent import ReactAgent, ReActParser, ReActStep

__version__ = "2.0.0"
__all__ = [
    "SmartWakeWordSystem",
    "TTSManager",
    "VisionUnderstanding",
    "MCPClient",
    "MCPClientSync",
    "MCPManager",
    "MCPManagerSync",
    "MCPResponse",
    "ReactAgent",
    "ReActParser",
    "ReActStep",
]
