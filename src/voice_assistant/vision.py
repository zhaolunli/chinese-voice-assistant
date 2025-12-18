"""视觉理解模块"""
import base64
import requests

from .config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL


class VisionUnderstanding:
    """视觉理解模块"""

    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or DASHSCOPE_API_URL
        self.api_key = api_key or DASHSCOPE_API_KEY

    def understand_screen(self, image_path, question="屏幕上有什么内容？请详细描述。"):
        """使用Qwen3-VL-Plus理解屏幕"""
        try:
            with open(image_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode()

            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
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
                    "temperature": 0.7
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API错误 {response.status_code}"
        except Exception as e:
            return f"视觉理解失败: {e}"
