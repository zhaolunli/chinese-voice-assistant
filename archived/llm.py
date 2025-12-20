"""大模型控制器"""
import json
import requests

from .config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL
from .tts import TTSManager
from .system_control import SystemController
from .vision import VisionUnderstanding
from .vision_agent import VisionGuidedAgent


class LLMController:
    """大模型控制器"""

    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or DASHSCOPE_API_URL
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.system_controller = SystemController()
        self.vision = VisionUnderstanding(api_url, api_key)
        self.tts = TTSManager(api_key)
        # 新增：视觉引导代理
        self.vision_agent = VisionGuidedAgent(self.api_url, self.api_key, self.system_controller)

    def understand_intent(self, text):
        """理解用户意图"""
        prompt = f"""你是Windows系统助手。用户说："{text}"

可用操作（返回JSON格式）：
1. 打开浏览器: {{"action": "open_browser", "url": "可选网址"}}
2. 打开应用: {{"action": "open_app", "app": "应用名"}}
3. 点击元素: {{"action": "click_element", "element": "要点击的元素描述"}}
4. 输入内容: {{"action": "input_text", "content": "要输入的内容"}}
5. 查看屏幕: {{"action": "understand_screen", "question": "要问的问题", "target": "截图范围"}}
6. 窗口管理: {{"action": "window_control", "operation": "maximize/minimize/close", "target": "窗口标题模式"}}

重要规则：
- 当用户说"点击XX"、"点XX"时，使用 click_element
- 当用户说"输入XX"、"搜索XX"时，使用 input_text（会先点击聚焦再输入）
- 当用户说"打开XX网站"、"打开浏览器"时，使用 open_browser
- 当用户说"最大化"、"最小化"、"关闭"窗口时，使用 window_control
- 当用户问"浏览器显示什么"、"查看网页"时，使用 understand_screen
- click_element 和 input_text 都会使用视觉识别自动定位元素

示例：
- "点击搜索框" → {{"action": "click_element", "element": "搜索框"}}
- "点击按钮" → {{"action": "click_element", "element": "按钮"}}
- "输入百度" → {{"action": "input_text", "content": "百度"}}
- "搜索天气" → {{"action": "input_text", "content": "天气"}}
- "打开浏览器" → {{"action": "open_browser", "url": ""}}
- "查看浏览器" → {{"action": "understand_screen", "target": "browser", "question": "描述内容"}}

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
                        {"role": "system", "content": "你是一个智能助手，返回JSON格式的操作指令。准确识别用户的操作意图。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.1
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
        text_lower = text.lower()

        # 点击相关（最高优先级）
        if any(w in text_lower for w in ["点击", "点一下", "点", "按"]):
            for prefix in ["点击", "点一下", "点", "按"]:
                if prefix in text:
                    element = text.split(prefix, 1)[1].strip()
                    if element:
                        return {"action": "click_element", "element": element}
            return {"action": "click_element", "element": text}

        # 输入相关（优先级次高）
        if any(w in text_lower for w in ["输入", "搜索", "访问", "打开网址", "打开网站"]):
            for prefix in ["输入", "搜索", "访问", "打开网址", "打开网站"]:
                if prefix in text:
                    content = text.split(prefix, 1)[1].strip()
                    if content:
                        return {"action": "input_text", "content": content}
            return {"action": "input_text", "content": text}

        # 窗口管理
        if "最大化" in text:
            return {"action": "window_control", "operation": "maximize", "target": ".*"}
        if "最小化" in text:
            return {"action": "window_control", "operation": "minimize", "target": ".*"}
        if any(w in text for w in ["关闭窗口", "关闭程序"]):
            return {"action": "window_control", "operation": "close", "target": ".*"}

        # 查看屏幕相关
        if any(w in text_lower for w in ["浏览器", "网页", "页面"]):
            if any(w in text_lower for w in ["看", "查看", "截图", "显示"]):
                return {"action": "understand_screen", "target": "browser", "question": "请描述浏览器中显示的内容"}
            # 如果只说"浏览器"没有其他动词，默认打开
            return {"action": "open_browser"}

        # 窗口相关
        if any(w in text_lower for w in ["窗口", "这个", "当前"]):
            return {"action": "understand_screen", "target": "active", "question": "请描述窗口中的内容"}

        # 屏幕相关（只有明确说"屏幕"才用全屏）
        if "全屏" in text or "整个屏幕" in text or "所有屏幕" in text:
            return {"action": "understand_screen", "target": "full", "question": "请描述屏幕上的所有内容"}

        # 默认看看类（优先浏览器）
        if any(w in text_lower for w in ["看看", "查看", "截图"]):
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
            success = self.system_controller.open_browser(url)
            if success:
                if enable_voice:
                    self.tts.speak_async("好的，已为您打开浏览器")
            else:
                print("✗ 打开浏览器失败")
                if enable_voice:
                    self.tts.speak_async("抱歉，打开浏览器失败")

        elif action == "open_app":
            app = intent.get("app", "")
            success = self.system_controller.open_app(app)
            if success:
                if enable_voice:
                    self.tts.speak_async(f"好的，已为您打开{app}")
            else:
                print(f"✗ 打开应用失败: {app}")
                if enable_voice:
                    self.tts.speak_async(f"抱歉，打开{app}失败")

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

        elif action == "browser_input":
            content = intent.get("content", "")
            print(f"🌐 浏览器操作: {content}")

            if enable_voice:
                self.tts.speak_async("好的，让我看看界面")

            # 使用视觉引导执行
            success = self.vision_agent.execute_with_vision(
                user_command=f"在浏览器中输入: {content}",
                target="browser"
            )

            if success:
                if enable_voice:
                    self.tts.speak_async(f"好的，已输入完成")
            else:
                print(f"✗ 浏览器操作失败")
                if enable_voice:
                    self.tts.speak_async("抱歉，操作失败，请检查浏览器是否打开")

        elif action == "click_element":
            element = intent.get("element", "")
            print(f"👆 点击元素: {element}")

            if enable_voice:
                self.tts.speak_async("好的，让我定位元素")

            # 智能选择截图目标
            # 如果当前有浏览器在运行，优先使用浏览器截图
            target = "browser"  # 默认浏览器

            # 使用视觉引导点击
            success = self.vision_agent.execute_with_vision(
                user_command=f"点击: {element}",
                target=target
            )

            if success:
                if enable_voice:
                    self.tts.speak_async("已完成点击")
            else:
                print(f"✗ 点击失败")
                if enable_voice:
                    self.tts.speak_async("抱歉，未找到该元素")

        elif action == "input_text":
            content = intent.get("content", "")
            print(f"⌨️ 输入内容: {content}")

            if enable_voice:
                self.tts.speak_async("好的，开始输入")

            # 使用视觉引导输入（会先找到并点击输入框，再输入）
            success = self.vision_agent.execute_with_vision(
                user_command=f"输入文字: {content}",
                target="browser"  # 输入通常在浏览器中
            )

            if success:
                if enable_voice:
                    self.tts.speak_async("输入完成")
            else:
                print(f"✗ 输入失败")
                if enable_voice:
                    self.tts.speak_async("抱歉，操作失败")

        elif action == "window_control":
            operation = intent.get("operation", "")
            target = intent.get("target", "")
            print(f"🪟 窗口操作: {operation} - {target}")

            success = False
            if operation == "maximize":
                success = self.system_controller.maximize_window(target)
            elif operation == "minimize":
                success = self.system_controller.minimize_window(target)
            elif operation == "close":
                success = self.system_controller.close_window(target)

            if success:
                if enable_voice:
                    self.tts.speak_async(f"好的，已{operation}窗口")
            else:
                print(f"✗ 窗口操作失败")
                if enable_voice:
                    self.tts.speak_async("抱歉，窗口操作失败")

        else:
            if enable_voice:
                self.tts.speak_async("抱歉，我不太明白您的意思")
