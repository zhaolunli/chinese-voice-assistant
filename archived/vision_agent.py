"""视觉引导的操作代理"""
import json
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class VisionGuidedAgent:
    """
    视觉引导的操作代理

    流程：
    1. 截图当前界面
    2. Vision 分析界面元素和布局
    3. 根据用户指令，Vision 指导如何操作
    4. 执行操作（点击坐标、输入文字等）
    """

    def __init__(self, api_url: str, api_key: str, system_controller):
        self.api_url = api_url
        self.api_key = api_key
        self.system_controller = system_controller

    def analyze_screen_elements(self, screenshot_path: str) -> Dict:
        """
        分析屏幕上的可操作元素

        让 Vision 识别：
        - 有哪些输入框（位置描述）
        - 有哪些按钮（位置描述）
        - 当前焦点在哪
        - 页面是什么（Google、百度等）

        Returns:
            {
                "page_type": "Google搜索首页",
                "elements": [
                    {"type": "search_box", "description": "页面中央的搜索框", "position": "center"},
                    {"type": "button", "description": "Google搜索按钮", "position": "below_search"}
                ],
                "current_focus": "无焦点"
            }
        """
        prompt = """请详细分析这个界面，返回JSON格式：

{
    "page_type": "页面类型（如：Google首页、百度搜索、记事本等）",
    "window_size": {"width": 窗口宽度像素, "height": 窗口高度像素},
    "elements": [
        {
            "type": "元素类型（search_box/button/input/text_area/link等）",
            "label": "元素标签或文字",
            "description": "详细描述位置（如：页面顶部中央、左上角、底部等）",
            "position": {
                "x_percent": X轴位置百分比（0-100，表示从左到右）,
                "y_percent": Y轴位置百分比（0-100，表示从上到下）,
                "region": "区域描述（如：top-center、middle-left等）"
            },
            "is_focused": true/false
        }
    ],
    "current_state": "当前页面状态描述"
}

重要：
1. 尽可能多地识别可交互元素
2. 位置描述要清晰（顶部/中央/底部、左/中/右）
3. **必须提供position坐标**：x_percent和y_percent是元素中心点的屏幕位置百分比
   - 例如：页面中央的搜索框 → x_percent: 50, y_percent: 40
   - 例如：右上角的按钮 → x_percent: 90, y_percent: 10
4. 如果是搜索引擎，说明是哪个（Google/百度/Bing等）
5. 如果已经有文字输入，说明内容

只返回JSON，不要其他内容。"""

        try:
            # 读取图片
            with open(screenshot_path, 'rb') as f:
                import base64
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # 使用与 vision.py 相同的 API 格式
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            }]

            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-vl-plus",
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.1
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                # 提取JSON
                content = content.replace("```json", "").replace("```", "").strip()
                elements_info = json.loads(content)
                return elements_info
            else:
                print(f"Vision 分析失败: {response.status_code} - {response.text}")
                return {}

        except Exception as e:
            print(f"分析屏幕元素失败: {e}")
            return {}

    def plan_action(self, user_intent: str, screen_analysis: Dict) -> Dict:
        """
        根据用户意图和屏幕分析，规划具体操作

        Args:
            user_intent: 用户原始指令（如："输入百度"）
            screen_analysis: Vision 的屏幕分析结果

        Returns:
            {
                "actions": [
                    {"type": "click", "target": "搜索框", "method": "keyboard_shortcut"},
                    {"type": "input", "text": "百度"}
                ],
                "explanation": "我看到Google搜索页面，将使用快捷键聚焦搜索框，然后输入'百度'"
            }
        """
        prompt = f"""你是一个操作规划助手。

用户意图："{user_intent}"

当前界面分析：
{json.dumps(screen_analysis, ensure_ascii=False, indent=2)}

请规划具体操作步骤，返回JSON格式：
{{
    "understanding": "我的理解（用户想做什么）",
    "actions": [
        {{
            "type": "操作类型（click_element/click_shortcut/input_text/press_key/wait）",
            "description": "操作描述",
            "params": {{
                "element": "元素标签（如果是 click_element，使用界面分析中的元素label）",
                "keys": "快捷键（如果是 click_shortcut）",
                "text": "要输入的文字（如果是 input_text）",
                "key": "按键名（如果是 press_key）",
                "duration": 等待时长秒数（如果是 wait）
            }}
        }}
    ],
    "explanation": "详细解释操作步骤"
}}

可用操作类型：
1. click_element: 鼠标点击元素（使用元素的position坐标，最精确）
   - params.element 应设置为界面分析中识别到的元素的 label 或 type
   - 例如：{{"type": "click_element", "params": {{"element": "搜索框"}}}}
2. click_shortcut: 使用快捷键（如：Ctrl+L 聚焦地址栏、Tab 切换焦点、Ctrl+F 搜索等）
3. input_text: 输入文字（需要先确保焦点在正确位置）
4. press_key: 按单个键（如：Enter、Escape、Tab等）
5. wait: 等待（如：等待页面加载）

重要规则：
1. **优先使用 click_element**：如果界面分析中提供了元素的position坐标，直接点击最可靠
2. 如果没有坐标信息，才使用快捷键（click_shortcut）作为备选
3. 输入文字前，必须先确保焦点在正确元素上（通过点击或快捷键）
4. 如果是浏览器地址栏，可以用 Ctrl+L 或点击地址栏元素
5. 操作步骤要详细，一步一步来

示例：
用户说"输入百度"，界面分析显示有搜索框（label: "搜索", position: {{x_percent: 50, y_percent: 40}}）：
→ actions: [
    {{"type": "click_element", "params": {{"element": "搜索"}}, "description": "点击搜索框"}},
    {{"type": "input_text", "params": {{"text": "百度"}}, "description": "输入'百度'"}}
]

只返回JSON。"""

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
                        {"role": "system", "content": "你是一个精确的操作规划助手，根据界面元素规划操作步骤。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.1
                },
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                content = content.replace("```json", "").replace("```", "").strip()
                plan = json.loads(content)
                return plan
            else:
                return {"actions": [], "explanation": "规划失败"}

        except Exception as e:
            print(f"规划操作失败: {e}")
            return {"actions": [], "explanation": f"规划失败: {e}"}

    def execute_plan(self, plan: Dict, screen_analysis: Dict = None, target: str = "browser") -> bool:
        """
        执行操作计划

        Args:
            plan: 操作计划
            screen_analysis: 屏幕分析结果（用于获取窗口尺寸和元素坐标）
            target: 截图目标（用于确定窗口对象）

        Returns:
            是否成功
        """
        actions = plan.get("actions", [])

        print(f"\n📋 操作计划：{plan.get('explanation', '')}")
        print(f"   共 {len(actions)} 步操作")

        for i, action in enumerate(actions, 1):
            action_type = action.get("type")
            params = action.get("params", {})
            description = action.get("description", "")

            print(f"\n   步骤 {i}: {description}")

            try:
                if action_type == "click_element":
                    # 鼠标点击元素
                    element_label = params.get("element", "")
                    success = self._click_element_by_label(element_label, screen_analysis, target)

                elif action_type == "click_shortcut":
                    # 使用快捷键
                    keys = params.get("keys", "")
                    success = self._send_keys_to_active_window(keys)

                elif action_type == "input_text":
                    # 输入文字
                    text = params.get("text", "")
                    success = self._type_text_to_active_window(text)

                elif action_type == "press_key":
                    # 按键
                    key = params.get("key", "")
                    success = self._send_keys_to_active_window(f"{{{key}}}")

                elif action_type == "wait":
                    # 等待
                    import time
                    duration = params.get("duration", 0.5)
                    time.sleep(duration)
                    success = True

                else:
                    print(f"      ⚠️ 未知操作类型: {action_type}")
                    success = False

                if not success:
                    print(f"      ❌ 操作失败")
                    return False
                else:
                    print(f"      ✓ 完成")

                # 短暂延迟确保操作生效
                import time
                time.sleep(0.3)

            except Exception as e:
                print(f"      ❌ 执行失败: {e}")
                return False

        return True

    def _click_element_by_label(self, element_label: str, screen_analysis: Dict, target: str = "browser") -> bool:
        """
        通过元素标签点击元素

        Args:
            element_label: 元素标签或描述
            screen_analysis: 屏幕分析结果
            target: 截图目标（用于确定窗口对象）

        Returns:
            是否成功
        """
        if not screen_analysis or "elements" not in screen_analysis:
            print(f"      ⚠️ 无屏幕分析数据，无法点击")
            return False

        # 查找匹配的元素
        target_element = None
        for element in screen_analysis.get("elements", []):
            label = element.get("label", "")
            elem_type = element.get("type", "")
            description = element.get("description", "")

            # 模糊匹配：标签、类型或描述中包含目标文本
            if (element_label.lower() in label.lower() or
                element_label.lower() in elem_type.lower() or
                element_label.lower() in description.lower()):
                target_element = element
                break

        if not target_element:
            print(f"      ⚠️ 未找到元素: {element_label}")
            return False

        # 获取位置信息
        position = target_element.get("position", {})
        x_percent = position.get("x_percent")
        y_percent = position.get("y_percent")

        if x_percent is None or y_percent is None:
            print(f"      ⚠️ 元素缺少坐标信息: {element_label}")
            return False

        # 根据 target 获取正确的窗口对象
        window = None
        if target == "browser":
            # 查找浏览器窗口
            browser_patterns = [r".*Chrome.*", r".*Edge.*", r".*Firefox.*"]
            for pattern in browser_patterns:
                window = self.system_controller.window_manager.find_window_by_title(pattern)
                if window:
                    break
        elif target == "active":
            window = self.system_controller.window_manager.get_active_window()
        else:
            # 默认使用激活窗口
            window = self.system_controller.window_manager.get_active_window()

        if not window:
            print(f"      ⚠️ 无法获取窗口对象 (target={target})")
            return False

        try:
            rect = window.rectangle()
            window_width = rect.width()
            window_height = rect.height()

            # 计算全局屏幕坐标（窗口左上角 + 相对坐标）
            absolute_x = rect.left + int(window_width * x_percent / 100)
            absolute_y = rect.top + int(window_height * y_percent / 100)

            print(f"      🎯 全局坐标: ({absolute_x}, {absolute_y}) - {element_label}")

            # 使用 pywinauto.mouse 进行全局坐标点击（更可靠）
            import pywinauto.mouse as mouse
            mouse.click(button='left', coords=(absolute_x, absolute_y))

            print(f"      ✓ 已点击")
            return True

        except Exception as e:
            print(f"      ❌ 点击失败: {e}")
            return False

    def _send_keys_to_active_window(self, keys: str) -> bool:
        """向激活窗口发送按键"""
        window = self.system_controller.window_manager.get_active_window()
        if not window:
            return False

        try:
            window.type_keys(keys)
            return True
        except Exception as e:
            print(f"发送按键失败: {e}")
            return False

    def _type_text_to_active_window(self, text: str) -> bool:
        """向激活窗口输入文字"""
        window = self.system_controller.window_manager.get_active_window()
        if not window:
            return False

        try:
            window.type_keys(text, with_spaces=True)
            return True
        except Exception as e:
            print(f"输入文字失败: {e}")
            return False

    def execute_with_vision(self, user_command: str, target: str = "browser") -> bool:
        """
        使用视觉引导执行用户命令

        完整流程：
        1. 截图
        2. Vision 分析界面
        3. LLM 规划操作
        4. 执行操作

        Args:
            user_command: 用户指令
            target: 截图目标

        Returns:
            是否成功
        """
        print(f"\n🔍 使用视觉引导执行: {user_command}")

        # 1. 截图
        print("   📸 截取屏幕...")
        screenshot_path = self.system_controller.smart_capture(target, "vision_temp.png")
        if not screenshot_path:
            print("   ❌ 截图失败")
            return False

        # 2. 分析界面
        print("   👁️ 分析界面元素...")
        screen_analysis = self.analyze_screen_elements(screenshot_path)
        if not screen_analysis:
            print("   ❌ 界面分析失败")
            return False

        print(f"   ✓ 识别到页面: {screen_analysis.get('page_type', '未知')}")
        elements = screen_analysis.get('elements', [])
        print(f"   ✓ 发现 {len(elements)} 个可交互元素")

        # 3. 规划操作
        print("   🤔 规划操作步骤...")
        plan = self.plan_action(user_command, screen_analysis)

        # 4. 执行
        print("   🚀 开始执行...")
        success = self.execute_plan(plan, screen_analysis, target)  # 传递 target

        if success:
            print("   ✅ 执行完成！")
        else:
            print("   ❌ 执行失败")

        return success
