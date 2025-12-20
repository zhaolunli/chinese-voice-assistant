"""React Agent - 使用 MCP 工具的智能代理（同步版本）"""
import json
import logging
import re
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from PIL import ImageGrab
import tempfile
import ctypes
from ctypes import wintypes

from .config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL
from .mcp_client import MCPManagerSync, MCPResponse
from .tts import TTSManager
from .vision import VisionUnderstanding


@dataclass
class ReActStep:
    """React 单步执行结果"""
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str
    success: bool


class ReActParser:
    """
    ReAct 响应解析器

    解析 LLM 返回的 Thought/Action/Action Input 格式
    """

    THOUGHT_PATTERN = r"Thought:\s*(.*?)(?=\n(?:Action|Final Answer)|\Z)"
    ACTION_PATTERN = r"Action:\s*(.*?)(?=\nAction Input|\n|$)"
    ACTION_INPUT_PATTERN = r"Action Input:\s*(\{.*?\})"
    FINAL_ANSWER_PATTERN = r"Final Answer:\s*(.*)"

    @staticmethod
    def parse(response: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 响应

        Returns:
            {
                "thought": "思考内容",
                "action": "工具名称",
                "action_input": {...},
                "done": False/True
            }
        """
        try:
            # 检查是否完成
            final_match = re.search(ReActParser.FINAL_ANSWER_PATTERN, response, re.DOTALL)
            if final_match:
                return {
                    "thought": "任务已完成",
                    "action": None,
                    "action_input": {},
                    "done": True,
                    "final_answer": final_match.group(1).strip()
                }

            # 提取 Thought
            thought_match = re.search(ReActParser.THOUGHT_PATTERN, response, re.DOTALL)
            thought = thought_match.group(1).strip() if thought_match else ""

            # 提取 Action
            action_match = re.search(ReActParser.ACTION_PATTERN, response)
            action = action_match.group(1).strip() if action_match else ""

            # 提取 Action Input - 使用更智能的方法提取 JSON
            action_input = {}
            action_input_index = response.find("Action Input:")
            if action_input_index != -1:
                try:
                    # 找到第一个 {
                    start_idx = response.find("{", action_input_index)
                    if start_idx != -1:
                        # 使用栈来找到匹配的 }
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response)):
                            if response[i] == '{':
                                brace_count += 1
                            elif response[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break

                        json_str = response[start_idx:end_idx]

                        # 修复1：将 Python 布尔值转换为 JSON 格式
                        json_str = json_str.replace('True', 'true').replace('False', 'false').replace('None', 'null')

                        # 修复2：将 Python 单引号字典转换为 JSON 双引号格式
                        # 简单替换可能不完美，但对于大多数情况有效
                        if json_str.startswith("{'") or "': '" in json_str:
                            # 使用 ast.literal_eval 先转为 Python dict，再转 JSON
                            import ast
                            try:
                                python_dict = ast.literal_eval(json_str)
                                json_str = json.dumps(python_dict, ensure_ascii=False)
                            except:
                                # 降级：简单替换单引号为双引号
                                json_str = json_str.replace("'", '"')

                        action_input = json.loads(json_str)

                        print(f"[调试] 解析到的参数: {action_input}")

                except json.JSONDecodeError as e:
                    print(f"[调试] JSON 解析失败: {e}")
                    print(f"[调试] 原始字符串: {response[start_idx:end_idx]}")
                    print(f"[调试] 处理后字符串: {json_str}")
                except Exception as e:
                    print(f"[调试] 提取 JSON 失败: {e}")
            else:
                print(f"[调试] 未找到 Action Input")

            return {
                "thought": thought,
                "action": action,
                "action_input": action_input,
                "done": False
            }

        except Exception as e:
            logging.error(f"解析 ReAct 响应失败: {e}")
            import traceback
            traceback.print_exc()
            return None


class ReactAgent:
    """
    React (Reasoning and Acting) Agent

    基于 ReAct 框架的智能代理（同步版本）：
    1. Thought: 分析当前状态，思考下一步
    2. Action: 选择并执行 MCP 工具
    3. Observation: 观察执行结果
    4. 循环直到任务完成
    """

    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or DASHSCOPE_API_URL
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.logger = logging.getLogger(__name__)

        # MCP Manager（管理多个 MCP Server）
        self.mcp = MCPManagerSync()

        # TTS
        self.tts = TTSManager(api_key)

        # Vision（视觉理解）
        self.vision = VisionUnderstanding(api_url, api_key)

        # React 历史记录
        self.history: List[ReActStep] = []

        # 可用工具列表
        self.available_tools: List[Dict[str, Any]] = []

        # 最大步数（防止死循环，降低以提升响应速度）
        self.max_steps = 5

    def start(self) -> bool:
        """启动 Agent（启动 MCP Servers）"""
        print("\n⏳ 正在启动 MCP Servers...")

        # 配置 MCP Servers
        servers = [
            # Windows-MCP: 系统级操作（必需）
            ("windows", "uvx", ["windows-mcp"], 60),
            # Playwright-MCP: 浏览器操作（可选，首次启动较慢）
            ("playwright", "npx", ["@playwright/mcp@latest"], 120)  # 增加到120秒
        ]

        success = self.mcp.start(servers)
        if success:
            # 获取所有工具列表
            self.available_tools = self.mcp.list_all_tools()

            # 统计工具数量
            windows_tools = self.mcp.get_tools_by_server("windows")
            playwright_tools = self.mcp.get_tools_by_server("playwright")

            if windows_tools:
                print(f"  ✓ Windows-MCP: {len(windows_tools)} 个工具")
                self.logger.info(f"✓ Windows-MCP: {len(windows_tools)} 个工具")

            if playwright_tools:
                print(f"  ✓ Playwright-MCP: {len(playwright_tools)} 个工具")
                self.logger.info(f"✓ Playwright-MCP: {len(playwright_tools)} 个工具")
            else:
                print(f"  ⚠️ Playwright-MCP 未启动（浏览器操作将使用 Windows 工具）")
                self.logger.warning("Playwright-MCP 未启动")

            print(f"  📊 总计: {len(self.available_tools)} 个工具")
            self.logger.info(f"✓ 总计 {len(self.available_tools)} 个工具")

        return success

    def stop(self):
        """停止 Agent"""
        self.mcp.stop()

    def execute_command(self, user_command: str, enable_voice: bool = True) -> Dict:
        """
        执行用户命令（智能判断使用 Vision 或 React 循环）

        Args:
            user_command: 用户指令
            enable_voice: 是否语音播报

        Returns:
            执行结果
        """
        self.logger.info(f"🤖 开始执行: {user_command}")

        if enable_voice:
            self.tts.speak_async("好的，让我来处理")

        # 判断是否需要视觉理解
        if self._needs_vision_understanding(user_command):
            self.logger.info("使用 Vision 模式（视觉理解）")
            print("💡 检测到视觉理解任务，使用 Vision API...")
            return self._vision_mode(user_command, enable_voice)
        else:
            self.logger.info("使用 React 模式（操作执行）")
            return self._react_mode(user_command, enable_voice)

    def _needs_vision_understanding(self, command: str) -> bool:
        """
        判断是否需要视觉理解

        视觉理解关键词：看、查看、讲解、描述、显示、分析、识别
        操作关键词：点击、输入、打开、关闭、滚动、搜索
        """
        vision_keywords = [
            "看", "查看", "讲解", "描述", "显示什么", "显示的",
            "分析", "识别", "内容是", "画面", "截图", "图片"
        ]

        operation_keywords = [
            "点击", "输入", "打开", "关闭", "启动", "切换",
            "滚动", "搜索", "执行", "运行", "按"
        ]

        # 如果包含操作关键词，优先使用 React 模式
        if any(kw in command for kw in operation_keywords):
            return False

        # 如果包含视觉关键词，使用 Vision 模式
        if any(kw in command for kw in vision_keywords):
            return True

        # 默认使用 React 模式
        return False

    def _vision_mode(self, user_command: str, enable_voice: bool) -> Dict:
        """
        视觉理解模式

        Args:
            user_command: 用户指令
            enable_voice: 是否语音播报

        Returns:
            执行结果
        """
        try:
            # 智能判断截图范围
            target = self._determine_screenshot_target(user_command)

            # 1. 截图
            print(f"📸 正在截图 ({target})...")
            screenshot_path = self._take_screenshot(target)

            # 2. 调用 Vision API
            print("🔍 正在分析图像...")
            analysis = self.vision.understand_screen(
                screenshot_path,
                question=user_command
            )

            # 输出分析结果
            if analysis:
                print(f"\n📊 分析结果:\n{analysis}\n")
            else:
                print("⚠️ 未获取到分析结果")

            # 3. 语音播报
            if enable_voice and analysis:
                self.tts.speak_async(analysis)

            # 4. 清理临时文件
            try:
                Path(screenshot_path).unlink()
            except:
                pass

            return {
                "success": True,
                "message": analysis,
                "mode": "vision"
            }

        except Exception as e:
            error_msg = f"视觉理解失败: {e}"
            self.logger.error(error_msg)
            if enable_voice:
                self.tts.speak_async("抱歉，视觉理解失败")
            return {
                "success": False,
                "message": error_msg,
                "mode": "vision"
            }

    def _determine_screenshot_target(self, command: str) -> str:
        """
        根据指令判断截图范围

        Returns:
            "window" - 当前窗口
            "screen" - 全屏
        """
        # 明确指定窗口的关键词
        window_keywords = ["窗口", "浏览器", "chrome", "应用"]

        # 如果包含窗口相关关键词，优先截取窗口
        if any(kw in command.lower() for kw in window_keywords):
            return "window"

        # 默认窗口截图（节省 Vision API token）
        return "window"

    def _get_foreground_window_rect(self) -> Optional[tuple]:
        """
        获取前台窗口坐标（DPI感知）

        Returns:
            (left, top, right, bottom) 或 None
        """
        try:
            # 设置 DPI 感知
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                # 可能已经设置过，忽略错误
                pass

            # 获取前台窗口句柄
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None

            # 获取窗口矩形
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

            # 修正：去除边框和阴影（Windows 10/11 典型值）
            padding = 8
            bbox = (
                rect.left + padding,
                rect.top,
                rect.right - padding,
                rect.bottom - padding
            )

            self.logger.debug(f"窗口坐标: 原始{(rect.left, rect.top, rect.right, rect.bottom)} -> 修正{bbox}")
            return bbox

        except Exception as e:
            self.logger.warning(f"获取窗口坐标失败: {e}")
            return None

    def _take_screenshot(self, target: str = "window") -> str:
        """
        智能截图

        Args:
            target: "window" (当前窗口，默认) 或 "screen" (全屏)

        Returns:
            截图文件路径
        """
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.png',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()

        if target == "window":
            # 尝试窗口截图
            bbox = self._get_foreground_window_rect()
            if bbox:
                self.logger.info(f"使用窗口截图: {bbox}")
                screenshot = ImageGrab.grab(bbox=bbox)
            else:
                # 降级到全屏
                self.logger.warning("窗口坐标获取失败，降级到全屏截图")
                print("⚠️ 窗口截图失败，使用全屏模式")
                screenshot = ImageGrab.grab()
        else:
            # 全屏截图
            screenshot = ImageGrab.grab()

        screenshot.save(temp_path)
        return temp_path

    def _react_mode(self, user_command: str, enable_voice: bool) -> Dict:
        """
        React 操作模式（使用 MCP 工具）

        Args:
            user_command: 用户指令
            enable_voice: 是否语音播报

        Returns:
            执行结果
        """
        # 重置历史
        self.history = []

        # React 循环
        for step in range(self.max_steps):
            print(f"\n--- 步骤 {step + 1} ---")
            self.logger.info(f"\n--- Step {step + 1} ---")

            # 1. LLM 思考：下一步做什么
            parsed_action = self._think(user_command)

            if not parsed_action:
                print("❌ 思考失败")
                self.logger.error("❌ 思考失败")
                break

            # 2. 判断是否完成
            if parsed_action.get("done", False):
                print("✅ 任务完成")
                self.logger.info("✅ 任务完成")
                if enable_voice:
                    final_answer = parsed_action.get("final_answer", "已完成")
                    self.tts.speak_async(final_answer)
                return {
                    "success": True,
                    "message": parsed_action.get("final_answer", "任务完成"),
                    "steps": step + 1
                }

            # 3. 执行动作
            print(f"🎯 执行: {parsed_action['action']}")
            print(f"   参数: {parsed_action['action_input']}")
            observation = self._execute_action(
                parsed_action["action"],
                parsed_action["action_input"]
            )

            # 4. 显示结果
            if observation and observation.success:
                print(f"✓ 成功: {observation.content[:100] if observation.content else '执行成功'}")
            else:
                error_msg = observation.error if observation else '未知错误'
                print(f"✗ 失败: {error_msg}")

            # 5. 记录历史
            self.history.append(ReActStep(
                thought=parsed_action["thought"],
                action=parsed_action["action"],
                action_input=parsed_action["action_input"],
                observation=observation.content if observation else "执行失败",
                success=observation.success if observation else False
            ))

            # 6. 如果失败，继续尝试调整策略
            if not (observation and observation.success):
                self.logger.warning(f"⚠️ 步骤失败: {observation.error if observation else '未知错误'}")
                # 继续尝试下一个策略

        # 超过最大步数
        self.logger.warning("⚠️ 超过最大步数，任务未完成")
        if enable_voice:
            self.tts.speak_async("抱歉，任务未能完成")

        return {
            "success": False,
            "message": "超过最大步数",
            "steps": self.max_steps
        }

    def _think(self, user_command: str) -> Optional[Dict[str, Any]]:
        """
        思考：根据用户命令和历史记录，决定下一步动作

        Returns:
            {
                "thought": "我的思考...",
                "action": "Click-Tool",
                "action_input": {"x": 100, "y": 200},
                "done": False
            }
        """
        # 构造提示词
        prompt = self._build_react_prompt(user_command)

        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-plus",
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.1
                },
                timeout=30  # 增加超时时间：15秒 → 30秒
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # 调试：显示 LLM 原始响应
                print(f"\n[调试] LLM 响应:\n{content}\n")

                # 使用 ReActParser 解析
                parsed = ReActParser.parse(content)

                if parsed:
                    # 显示思考内容
                    print(f"💭 思考: {parsed.get('thought', '')[:100]}")
                    self.logger.info(f"💭 思考: {parsed.get('thought', '')}")
                    if not parsed.get("done"):
                        self.logger.info(f"🎯 动作: {parsed.get('action')} {parsed.get('action_input', {})}")
                else:
                    print("[调试] ❌ 解析失败")

                return parsed
            else:
                self.logger.error(f"LLM 请求失败: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"思考失败: {e}")
            return None

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        tool_descriptions = self._format_tool_descriptions()

        # 临时调试：显示工具描述（只在第一次调用时）
        if not hasattr(self, '_prompt_shown'):
            print("\n[调试] 工具参数格式示例:")
            lines = tool_descriptions.split('\n')
            for line in lines[:20]:  # 只显示前20行
                print(f"  {line}")
            if len(lines) > 20:
                print(f"  ... (共 {len(lines)} 行)")
            print()
            self._prompt_shown = True

        return f"""你是一个智能助手，同时使用 Windows-MCP 和 Playwright-MCP 工具完成用户任务。

按照 ReAct (Reasoning and Acting) 框架思考和行动：
1. Thought: 分析当前情况，思考下一步
2. Action: 选择一个工具执行
3. Action Input: 提供工具参数
4. Observation: 观察执行结果（由系统提供）
5. 重复以上步骤直到完成

工具选择策略：
• 浏览器操作（导航、点击网页元素、填写表单等）→ **必须使用 Playwright 工具**（browser_*）
  - 例如：browser_navigate、browser_click、browser_type、browser_snapshot
  - ⚠️ 浏览器操作前必须先调用 browser_snapshot 获取页面元素
  - ⚠️ 只能使用 browser_snapshot 返回的 ref（格式：e38、e77等），不能使用 State-Tool 的 ref（格式：49、50等）
  - Playwright 更快、更可靠、理解网页结构
• 桌面操作（打开应用、系统快捷键、窗口管理等）→ 使用 Windows 工具
  - 例如：App-Tool、Shortcut-Tool、Desktop-Tool
  - State-Tool 只用于了解桌面状态，不用于浏览器内操作

可用工具：
{tool_descriptions}

输出格式：
Thought: [你的思考过程]
Action: [工具名称]
Action Input: {{"param": "value"}}

如果任务完成，输出：
Thought: 任务已完成
Final Answer: [总结结果]

重要规则：
1. 每次只执行一个动作
2. 浏览器操作必须使用 Playwright 工具（browser_*），先 browser_snapshot 再操作
3. 不要混用 State-Tool 和 browser_* 的 ref 系统
4. 优先使用快捷键和简单操作，避免复杂流程
5. 如果任务不清晰或无法理解，直接返回 Final Answer 说明原因
6. 最多 5 步必须完成，保持高效
7. 如果连续失败 2 次，立即停止并返回 Final Answer"""

    def _format_tool_descriptions(self) -> str:
        """格式化工具描述"""
        if not self.available_tools:
            return "暂无可用工具"

        descriptions = []
        # 不再限制数量，显示所有工具
        for tool in self.available_tools:
            name = tool.get("name", "")
            desc = tool.get("description", "")
            schema = tool.get("input_schema", {})

            # 提取必需参数
            required = schema.get("required", [])
            properties = schema.get("properties", {})

            # 构造参数说明
            params = []
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                is_required = param_name in required
                param_desc = param_info.get("description", "")

                if is_required:
                    params.append(f"    - {param_name} ({param_type}, 必需): {param_desc}")
                else:
                    params.append(f"    - {param_name} ({param_type}, 可选): {param_desc}")

            if params:
                descriptions.append(f"- {name}: {desc}\n  参数:\n" + "\n".join(params))
            else:
                descriptions.append(f"- {name}: {desc}")

        return "\n".join(descriptions)

    def _build_react_prompt(self, user_command: str) -> str:
        """构造 ReAct 提示词"""

        # 历史记录
        history_text = ""
        if self.history:
            history_text = "\n已执行步骤:\n"
            for i, step in enumerate(self.history[-3:], 1):  # 只显示最近3步
                history_text += f"\nStep {i}:\n"
                history_text += f"Thought: {step.thought}\n"
                history_text += f"Action: {step.action}\n"
                history_text += f"Action Input: {step.action_input}\n"
                history_text += f"Observation: {step.observation}\n"

        prompt = f"""用户任务: {user_command}
{history_text}

请分析当前情况，决定下一步动作。"""

        return prompt

    def _execute_action(self, action: str, action_input: Dict[str, Any]) -> Optional[MCPResponse]:
        """
        执行动作

        Args:
            action: 工具名称
            action_input: 工具参数

        Returns:
            MCPResponse 对象
        """
        if not action:
            return MCPResponse(success=False, error="未指定工具")

        try:
            # 确保参数不为空
            if not action_input:
                print(f"[警告] 参数为空，使用空字典")
                action_input = {}

            print(f"[调试] 实际传递参数: {action_input}")
            self.logger.debug(f"执行工具: {action}, 参数: {action_input}")

            result = self.mcp.call_tool(action, action_input)
            return result

        except Exception as e:
            self.logger.error(f"执行动作失败: {e}")
            import traceback
            traceback.print_exc()
            return MCPResponse(success=False, error=str(e))
