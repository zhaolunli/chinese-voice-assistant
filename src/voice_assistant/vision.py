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
        """使用Qwen-VL-Max理解屏幕"""
        try:
            # 直接读取图片，不压缩
            with open(image_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode()

            print(f"[视觉API] 图片大小: {len(img_base64) / 1024:.1f} KB")

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    }
                ]
            }]

            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-vl-max",
                    "messages": messages,
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                # 详细错误信息
                error_msg = f"API错误 {response.status_code}"
                try:
                    error_detail = response.json()
                    print(f"[视觉API错误详情] {error_detail}")
                    error_msg += f": {error_detail.get('message', error_detail)}"
                except:
                    print(f"[视觉API错误] 状态码: {response.status_code}, 响应: {response.text[:200]}")
                return error_msg
        except Exception as e:
            print(f"[视觉理解异常] {e}")
            import traceback
            traceback.print_exc()
            return f"视觉理解失败: {e}"
