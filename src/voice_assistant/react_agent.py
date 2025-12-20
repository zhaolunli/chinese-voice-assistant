"""React Agent - 使用 MCP 工具的智能代理（同步版本）"""
import json
import logging
import re
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL
from .mcp_client import MCPClientSync, MCPResponse
from .tts import TTSManager


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

                        # 修复：将 Python 布尔值转换为 JSON 格式
                        json_str = json_str.replace('True', 'true').replace('False', 'false').replace('None', 'null')

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

        # MCP Client（同步封装）
        self.mcp = MCPClientSync()

        # TTS
        self.tts = TTSManager(api_key)

        # React 历史记录
        self.history: List[ReActStep] = []

        # 可用工具列表
        self.available_tools: List[Dict[str, Any]] = []

        # 最大步数（防止死循环，降低以提升响应速度）
        self.max_steps = 5

    def start(self) -> bool:
        """启动 Agent（启动 MCP Server）"""
        success = self.mcp.start()
        if success:
            # 获取工具列表
            self.available_tools = self.mcp.list_tools()
            self.logger.info(f"✓ 已获取 {len(self.available_tools)} 个工具")

            # 显示所有工具名称
            print(f"✓ 已获取 {len(self.available_tools)} 个 MCP 工具:")
            if self.available_tools:
                for i, tool in enumerate(self.available_tools, 1):
                    name = tool['name']
                    desc = tool.get('description', '')[:50]  # 只显示前50字符
                    print(f"  {i}. {name}: {desc}")
                print()

        return success

    def stop(self):
        """停止 Agent"""
        self.mcp.stop()

    def execute_command(self, user_command: str, enable_voice: bool = True) -> Dict:
        """
        执行用户命令（使用 React 循环）

        Args:
            user_command: 用户指令
            enable_voice: 是否语音播报

        Returns:
            执行结果
        """
        self.logger.info(f"🤖 开始执行: {user_command}")

        if enable_voice:
            self.tts.speak_async("好的，让我来处理")

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

        return f"""你是一个智能助手，使用 Windows-MCP 工具完成用户任务。

按照 ReAct (Reasoning and Acting) 框架思考和行动：
1. Thought: 分析当前情况，思考下一步
2. Action: 选择一个工具执行
3. Action Input: 提供工具参数
4. Observation: 观察执行结果（由系统提供）
5. 重复以上步骤直到完成

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
2. 优先使用快捷键和简单操作，避免复杂流程
3. 如果任务不清晰或无法理解，直接返回 Final Answer 说明原因
4. 最多 5 步必须完成，保持高效
5. 如果连续失败 2 次，立即停止并返回 Final Answer"""

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
