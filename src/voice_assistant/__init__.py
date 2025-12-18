"""
智能语音助手 - 双阶段识别版
阶段1: KWS轻量级关键词检测（持续监听）
阶段2: ASR完整语音识别（唤醒后）
"""

from .wake_word import SmartWakeWordSystem
from .tts import TTSManager
from .system_control import SystemController
from .vision import VisionUnderstanding
from .llm import LLMController

__version__ = "1.0.0"
__all__ = [
    "SmartWakeWordSystem",
    "TTSManager",
    "SystemController",
    "VisionUnderstanding",
    "LLMController",
]
