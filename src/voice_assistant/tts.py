"""TTS语音播报管理器"""
import threading
import time
import wave
from pathlib import Path
import pyaudio
import requests

from .config import (
    DASHSCOPE_API_KEY,
    ALIYUN_APPKEY,
    ALIYUN_TTS_URL,
    TTS_AUDIO_DIR,
    TTS_SHORT_TEXT_LIMIT,
    TTS_CACHE_TIMEOUT_SHORT,
    TTS_CACHE_TIMEOUT_LONG,
)


class TTSManager:
    """阿里云TTS语音播报管理器 - 支持长文本"""

    def __init__(self, api_key=None, appkey=None):
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.appkey = appkey or ALIYUN_APPKEY
        self.audio_dir = TTS_AUDIO_DIR
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.is_playing = False
        self.should_stop = False  # 打断标志
        self.current_stream = None  # 当前播放的音频流

        # 短文本TTS（dashscope，限制300字）
        try:
            import dashscope
            dashscope.api_key = self.api_key
            dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
            self.dashscope = dashscope
        except ImportError:
            print("⚠️  需要安装 dashscope: pip install dashscope")
            self.dashscope = None

        self.p = pyaudio.PyAudio()

    def _play_audio_file(self, audio_file):
        """使用PyAudio直接播放音频文件"""
        stream = None
        try:
            self.is_playing = True
            self.should_stop = False

            with wave.open(str(audio_file), 'rb') as wf:
                stream = self.p.open(
                    format=self.p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                self.current_stream = stream  # 保存引用以便打断

                chunk_size = 1024
                data = wf.readframes(chunk_size)
                while data and not self.should_stop:  # 检查打断标志
                    stream.write(data)
                    data = wf.readframes(chunk_size)

            if self.should_stop:
                print("   [TTS已打断]")

            time.sleep(0.1)  # 缩短延迟
        except Exception as e:
            if "Broken pipe" not in str(e):  # 忽略打断时的管道错误
                print(f"播放音频失败: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            self.current_stream = None
            self.is_playing = False
            self.should_stop = False

    def speak(self, text, voice="Cherry", wait=True):
        """智能语音播报：自动选择短文本或长文本TTS"""
        if not text or not text.strip():
            return

        text = text.strip()
        text_length = len(text)

        print(f"📝 文本长度: {text_length} 字符")

        # 根据文本长度选择TTS方式
        if text_length <= TTS_SHORT_TEXT_LIMIT:
            print("   使用短文本TTS（dashscope）")
            self._speak_short(text, voice, wait)
        else:
            print("   文本较长，使用长文本TTS（异步接口）")
            self._speak_long(text, voice, wait)

    def _speak_short(self, text, voice, wait):
        """短文本TTS"""
        if not self.dashscope:
            print("⚠️  Dashscope未初始化")
            return

        try:
            response = self.dashscope.MultiModalConversation.call(
                model="qwen3-tts-flash",
                api_key=self.api_key,
                text=text,
                voice=voice,
                language_type="Chinese",
                stream=False
            )

            if response.status_code == 200:
                audio_url = response.output.audio.url
                audio_response = requests.get(audio_url, timeout=10)
                if audio_response.status_code == 200:
                    audio_file = self.audio_dir / f"tts_{int(time.time())}.wav"
                    with open(audio_file, 'wb') as f:
                        f.write(audio_response.content)

                    if wait:
                        self._play_audio_file(audio_file)
                    else:
                        threading.Thread(
                            target=self._play_audio_file,
                            args=(audio_file,),
                            daemon=True
                        ).start()

                    threading.Timer(
                        TTS_CACHE_TIMEOUT_SHORT,
                        lambda: self._delete_file(audio_file)
                    ).start()
            else:
                print(f"TTS错误: {response.status_code} - {response.message}")

        except Exception as e:
            print(f"短文本TTS失败: {e}")

    def _speak_long(self, text, voice, wait):
        """长文本TTS（异步接口）"""
        try:
            # 1. 发起合成请求
            task_id = self._request_long_tts(text, voice)
            if not task_id:
                print("❌ 长文本TTS请求失败")
                return

            print(f"✓ 任务已提交，task_id: {task_id}")

            # 2. 轮询获取结果
            audio_url = self._poll_tts_result(task_id)
            if not audio_url:
                print("❌ 获取TTS结果失败")
                return

            print(f"✓ 音频已生成: {audio_url}")

            # 3. 下载并播放
            audio_response = requests.get(audio_url, timeout=30)
            if audio_response.status_code == 200:
                audio_file = self.audio_dir / f"tts_long_{int(time.time())}.wav"
                with open(audio_file, 'wb') as f:
                    f.write(audio_response.content)

                if wait:
                    self._play_audio_file(audio_file)
                else:
                    threading.Thread(
                        target=self._play_audio_file,
                        args=(audio_file,),
                        daemon=True
                    ).start()

                threading.Timer(
                    TTS_CACHE_TIMEOUT_LONG,
                    lambda: self._delete_file(audio_file)
                ).start()

        except Exception as e:
            print(f"长文本TTS失败: {e}")
            import traceback
            traceback.print_exc()

    def _request_long_tts(self, text, voice):
        """发起长文本TTS请求"""
        voice_map = {
            "Cherry": "xiaoyun",
            "xiaoyun": "xiaoyun",
            "siyue": "siyue",
            "xiaogang": "xiaogang"
        }
        tts_voice = voice_map.get(voice, "xiaoyun")

        body = {
            "header": {
                "appkey": self.appkey,
                "token": self.api_key
            },
            "payload": {
                "enable_notify": False,
                "tts_request": {
                    "text": text,
                    "voice": tts_voice,
                    "format": "wav",
                    "sample_rate": 16000,
                    "enable_subtitle": False
                }
            },
            "context": {
                "device_id": "voice_assistant"
            }
        }

        response = requests.post(
            ALIYUN_TTS_URL,
            headers={"Content-Type": "application/json"},
            json=body,
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("error_code") == 20000000:
                return result["data"]["task_id"]
            else:
                print(f"TTS请求错误: {result.get('error_message')}")
        else:
            print(f"HTTP错误: {response.status_code}")

        return None

    def _poll_tts_result(self, task_id, max_wait=60):
        """轮询获取TTS结果"""
        url = f"{ALIYUN_TTS_URL}?appkey={self.appkey}&task_id={task_id}&token={self.api_key}"

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    result = response.json()

                    if result.get("error_code") == 20000000:
                        audio_address = result.get("data", {}).get("audio_address")

                        if audio_address:
                            return audio_address
                        else:
                            print("   合成中，请稍候...")
                    else:
                        print(f"轮询错误: {result.get('error_message')}")
                        break

                time.sleep(3)  # 每3秒轮询一次

            except Exception as e:
                print(f"轮询异常: {e}")
                break

        print("⚠️  TTS合成超时")
        return None

    def speak_async(self, text, voice="Cherry"):
        """异步播放（不阻塞）"""
        threading.Thread(
            target=self.speak,
            args=(text, voice, False),
            daemon=True
        ).start()

    def stop(self):
        """停止当前播放（立即停止）"""
        if self.is_playing:
            self.should_stop = True
            self.is_playing = False  # 立即标记为已停止
            # 立即停止音频流
            if self.current_stream:
                try:
                    self.current_stream.stop_stream()
                    self.current_stream.close()
                except:
                    pass
            # 清空当前流引用
            self.current_stream = None

    def _delete_file(self, filepath):
        """删除临时文件"""
        try:
            if filepath.exists():
                filepath.unlink()
        except:
            pass

    def __del__(self):
        try:
            self.p.terminate()
        except:
            pass
