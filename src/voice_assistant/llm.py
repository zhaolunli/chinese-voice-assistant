"""大模型控制器"""
import json
import requests

from .config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL
from .tts import TTSManager
from .system_control import SystemController
from .vision import VisionUnderstanding


class LLMController:
    """大模型控制器"""

    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or DASHSCOPE_API_URL
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.system_controller = SystemController()
        self.vision = VisionUnderstanding(api_url, api_key)
        self.tts = TTSManager(api_key)

    def understand_intent(self, text):
        """理解用户意图"""
        prompt = f"""你是Windows系统助手。用户说："{text}"

可用操作（返回JSON格式）：
1. 打开浏览器: {{"action": "open_browser", "url": "可选网址"}}
2. 打开应用: {{"action": "open_app", "app": "应用名"}}
3. 查看屏幕: {{"action": "understand_screen", "question": "要问的问题", "target": "截图范围"}}

截图范围说明：
- "browser": 优先截取浏览器窗口（Chrome/Edge/Firefox）
- "active": 截取当前激活的窗口
- "full": 截取整个屏幕（仅当用户明确要求"全屏"或"整个屏幕"时使用）

重要规则：
- 当用户提到"浏览器"、"网页"、"页面"时，使用 "target": "browser"
- 当用户说"看看这个"、"当前窗口"时，使用 "target": "active"
- 默认优先使用 "browser" 或 "active"，而不是 "full"

只返回JSON，不要其他内容。"""

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
                        {"role": "system", "content": "你是一个智能助手，返回JSON格式的操作指令。优先使用窗口截图而不是全屏截图。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3
                },
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                content = content.replace("```json", "").replace("```", "").strip()
                intent = json.loads(content)

                # 安全检查：如果没有指定target，默认使用智能截图
                if intent.get("action") == "understand_screen" and "target" not in intent:
                    intent["target"] = "browser"

                return intent
            else:
                return self._simple_match(text)
        except Exception as e:
            print(f"LLM理解失败: {e}")
            return self._simple_match(text)

    def _simple_match(self, text):
        """简单关键词匹配"""
        text = text.lower()

        # 浏览器相关
        if any(w in text for w in ["浏览器", "网页", "页面"]):
            if any(w in text for w in ["看", "查看", "截图", "显示"]):
                return {"action": "understand_screen", "target": "browser", "question": "请描述浏览器中显示的内容"}
            return {"action": "open_browser"}

        # 窗口相关
        if any(w in text for w in ["窗口", "这个", "当前"]):
            return {"action": "understand_screen", "target": "active", "question": "请描述窗口中的内容"}

        # 屏幕相关（只有明确说"屏幕"才用全屏）
        if "全屏" in text or "整个屏幕" in text or "所有屏幕" in text:
            return {"action": "understand_screen", "target": "full", "question": "请描述屏幕上的所有内容"}

        # 默认看看类（优先浏览器）
        if any(w in text for w in ["看看", "查看", "截图"]):
            return {"action": "understand_screen", "target": "browser", "question": "请描述看到的内容"}

        # 应用相关
        if "记事本" in text:
            return {"action": "open_app", "app": "记事本"}
        if "计算器" in text:
            return {"action": "open_app", "app": "计算器"}

        return {"action": "unknown"}

    def execute_action(self, intent, enable_voice=True):
        """执行操作"""
        action = intent.get("action")

        if action == "open_browser":
            url = intent.get("url", "")
            self.system_controller.open_browser(url)
            if enable_voice:
                self.tts.speak_async("好的，已为您打开浏览器")

        elif action == "open_app":
            app = intent.get("app", "")
            self.system_controller.open_app(app)
            if enable_voice:
                self.tts.speak_async(f"好的，已为您打开{app}")

        elif action == "understand_screen":
            target = intent.get("target", "browser")
            print(f"🎯 截图目标: {target}")

            if enable_voice:
                target_name = {
                    "browser": "浏览器窗口",
                    "active": "当前窗口",
                    "full": "整个屏幕"
                }.get(target, "屏幕")
                self.tts.speak_async(f"正在为您查看{target_name}")

            screen_path = self.system_controller.smart_capture(target, "screen.png")
            if screen_path:
                question = intent.get("question", "请详细描述屏幕上的内容。")
                result = self.vision.understand_screen(screen_path, question)
                print(f"🔍 分析结果: {result}")

                if enable_voice:
                    short_result = result[:200] + "..." if len(result) > 200 else result
                    self.tts.speak(short_result)

                return result
        else:
            if enable_voice:
                self.tts.speak_async("抱歉，我不太明白您的意思")
