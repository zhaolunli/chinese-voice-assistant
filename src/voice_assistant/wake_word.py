"""智能语音唤醒系统 - 双阶段识别版"""
import time
import threading
import numpy as np
import pyaudio
import sherpa_onnx
from pathlib import Path

from .config import (
    MODELS_DIR,
    SAMPLE_RATE,
    CHUNK_SIZE,
    RECORD_SECONDS,
    SILENCE_THRESHOLD,
    MAX_SILENCE_FRAMES,
    MIN_RECORD_FRAMES,
    DEFAULT_WAKE_WORDS,
    CONFIG_DIR,
)
from .react_agent import ReactAgent


class SmartWakeWordSystem:
    """智能语音唤醒系统 - 双阶段识别版"""

    def __init__(self, models_dir=None, enable_voice=True):
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR
        self.running = False
        self.sample_rate = SAMPLE_RATE
        self.enable_voice = enable_voice

        # 执行线程锁（确保同一时间只有一个命令在执行）
        self.execution_lock = threading.Lock()

        print("正在初始化智能语音助手...")

        # 阶段1: KWS模型（轻量级）
        self.kws_model = self.create_kws_model()

        # 阶段2: ASR模型（重量级）
        self.asr_model = self.create_asr_model()

        # React Agent (集成 MCP)
        self.agent = ReactAgent()
        print("正在启动 MCP Servers...")
        if not self.agent.start():
            raise RuntimeError("启动 MCP Server 失败")

        print(f"✓ KWS模型已加载")
        print(f"✓ ASR模型已加载")
        print(f"✓ MCP Servers 已启动")
        print(f"语音播报: {'开启' if enable_voice else '关闭'}")

    def create_kws_model(self):
        """创建KWS关键词检测模型"""
        kws_dir = self.models_dir / "sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01"

        if not kws_dir.exists():
            raise FileNotFoundError(f"KWS模型目录不存在: {kws_dir}")

        # 创建关键词文件（格式：拼音音节 @中文）
        keywords_file = CONFIG_DIR / "keywords.txt"
        if not keywords_file.exists():
            print("⚠️  创建默认关键词文件...")
            keywords_file.parent.mkdir(parents=True, exist_ok=True)
            with open(keywords_file, 'w', encoding='utf-8') as f:
                # 格式：拼音音节(空格分隔) @中文
                # 使用带声调的拼音韵母，空格分隔
                f.write("x iǎo zh ì @小智\n")
                f.write("n ǐ h ǎo zh ù sh ǒu @你好助手\n")
                f.write("zh ì n éng zh ù sh ǒu @智能助手\n")

        kws = sherpa_onnx.KeywordSpotter(
            tokens=str(kws_dir / "tokens.txt"),
            encoder=str(kws_dir / "encoder-epoch-12-avg-2-chunk-16-left-64.onnx"),
            decoder=str(kws_dir / "decoder-epoch-12-avg-2-chunk-16-left-64.onnx"),
            joiner=str(kws_dir / "joiner-epoch-12-avg-2-chunk-16-left-64.onnx"),
            num_threads=2,
            keywords_file=str(keywords_file),
            provider="cpu",
        )

        print(f"📋 加载关键词: {keywords_file}")
        return kws

    def create_asr_model(self):
        """创建ASR完整识别模型"""
        model_file = self.models_dir / "sherpa-onnx-paraformer-zh-2024-03-09" / "model.int8.onnx"
        tokens_file = self.models_dir / "sherpa-onnx-paraformer-zh-2024-03-09" / "tokens.txt"

        if not model_file.exists():
            raise FileNotFoundError(f"ASR模型文件不存在: {model_file}")

        recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
            str(model_file),
            str(tokens_file),
            num_threads=2,
            sample_rate=self.sample_rate,
            feature_dim=80,
            decoding_method="greedy_search",
            debug=False,
            provider="cpu"
        )
        return recognizer

    def _play_beep_fast(self):
        """播放快速提示音（非阻塞）"""
        def beep():
            try:
                import winsound
                winsound.Beep(1000, 80)  # 更短更快的提示音
            except:
                pass

        # 在单独线程播放，不阻塞主循环
        threading.Thread(target=beep, daemon=True).start()

    def start_listening(self):
        """开始监听"""
        print("\n" + "="*60)
        print("🎤 智能语音助手已启动 - 双阶段识别模式")
        print("阶段1: 持续监听关键词（轻量级KWS）")
        print("阶段2: 唤醒后录音识别（重量级ASR）")
        print("按 Ctrl+C 停止")
        print("="*60)

        self.running = True

        try:
            p = pyaudio.PyAudio()
            device_info = p.get_default_input_device_info()
            print(f"麦克风: {device_info['name']}")

            # 打开音频流
            stream = p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )

            print("✓ 开始监听关键词...\n")

            # 创建KWS流
            kws_stream = self.kws_model.create_stream()

            while self.running:
                try:
                    # 读取音频
                    audio_bytes = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    audio_data = np.frombuffer(audio_bytes, dtype=np.float32)

                    # TTS播放期间仍然监听（允许打断）
                    if self.agent.tts.is_playing:
                        # 检测音量峰值，判断是否是真实的语音打断
                        volume = np.sqrt(np.mean(audio_data**2))
                        # 如果音量过低（可能是TTS回声），跳过检测
                        if volume < 0.02:  # 降低阈值，更容易打断
                            continue  # ✓ 移除 sleep，立即继续检测
                        # 音量足够高，可能是用户打断，继续检测

                    # 喂给KWS
                    kws_stream.accept_waveform(self.sample_rate, audio_data)

                    # 检测关键词
                    while self.kws_model.is_ready(kws_stream):
                        self.kws_model.decode_stream(kws_stream)

                    # 获取结果
                    result = self.kws_model.get_result(kws_stream)

                    if result:
                        print(f"\n✨ 检测到唤醒词: {result}")

                        # 立即播放本地提示音（无延迟）
                        self._play_beep_fast()

                        # 检查是否正在执行任务
                        if self.agent.is_executing:
                            print("⚠️ 正在执行任务中，发送中断请求...")
                            print("   （等待当前步骤完成后中断...）")
                            self.agent.interrupt_flag = True

                            # 立即打断正在播放的TTS
                            if self.agent.tts.is_playing:
                                self.agent.tts.stop()

                            # 快速等待任务中断（最多3秒）
                            wait_count = 0
                            while self.agent.is_executing and wait_count < 30:
                                time.sleep(0.1)
                                wait_count += 1

                            if self.agent.is_executing:
                                print("⚠️ 当前步骤仍在执行，将在下一步中断")
                            else:
                                print("✓ 任务已中断")

                            # 重置KWS流，等待下一次唤醒
                            kws_stream = self.kws_model.create_stream()
                            continue

                        # 立即打断正在播放的TTS
                        if self.agent.tts.is_playing:
                            self.agent.tts.stop()

                        # 启动命令处理线程（非阻塞）
                        command_thread = threading.Thread(
                            target=self._handle_command_in_thread,
                            daemon=True
                        )
                        command_thread.start()

                        # 重置KWS流
                        kws_stream = self.kws_model.create_stream()

                except Exception as e:
                    print(f"⚠️ 音频处理错误: {e}")
                    # 重新创建流，继续运行
                    try:
                        kws_stream = self.kws_model.create_stream()
                    except:
                        pass
                    continue

            stream.stop_stream()
            stream.close()
            p.terminate()

        except KeyboardInterrupt:
            print("\n停止中...")
        finally:
            self.running = False
            # 停止 MCP Server
            print("正在停止 MCP Servers...")
            self.agent.stop()
            print("✓ MCP Servers 已停止")

    def _handle_command_in_thread(self):
        """在单独线程中处理命令（非阻塞）"""
        # 尝试获取执行锁（如果已有命令在执行，直接返回）
        if not self.execution_lock.acquire(blocking=False):
            print("⚠️ 已有命令正在执行，忽略本次唤醒")
            return

        try:
            # 创建独立的PyAudio实例（避免与主循环冲突）
            p = pyaudio.PyAudio()
            self._enter_command_mode(p)
            p.terminate()
        except KeyboardInterrupt:
            print("⚠️ 用户中断命令处理")
        except Exception as e:
            print(f"⚠️ 命令处理错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 释放锁
            self.execution_lock.release()

    def _enter_command_mode(self, pyaudio_instance):
        """阶段2: 录音识别"""
        print("💬 请说出指令...")

        # 短暂延迟，让用户听到Beep后准备说话
        time.sleep(0.3)

        # 录音参数
        audio_buffer = []

        try:
            stream = pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )

            print("🎙️ 录音中...")
            silence_count = 0
            frame_count = 0  # 记录总帧数
            has_speech = False  # 是否检测到有效语音

            for i in range(0, int(self.sample_rate / 1024 * RECORD_SECONDS)):
                audio_bytes = stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
                audio_buffer.append(audio_data)
                frame_count += 1

                # 音量检测
                volume = np.sqrt(np.mean(audio_data**2))

                # 检测到有效语音（音量超过阈值）
                if volume >= SILENCE_THRESHOLD:
                    has_speech = True
                    silence_count = 0
                else:
                    # 静音帧
                    silence_count += 1

                    # 只有在检测到有效语音后，才开始静音计数停止逻辑
                    if has_speech and silence_count > MAX_SILENCE_FRAMES:
                        print("   检测到静音，停止录音")
                        break

            stream.stop_stream()
            stream.close()

            # 拼接音频
            full_audio = np.concatenate(audio_buffer)

            # ASR识别
            print("🤔 正在识别...")
            asr_stream = self.asr_model.create_stream()
            asr_stream.accept_waveform(self.sample_rate, full_audio)
            self.asr_model.decode_stream(asr_stream)
            text = asr_stream.result.text.strip()

            if text:
                print(f"📝 识别结果: {text}")
                self._execute_command(text)
            else:
                print("   未识别到内容")
                if self.enable_voice:
                    self.agent.tts.speak_async("抱歉，我没听清")

        except Exception as e:
            print(f"录音识别错误: {e}")

    def _execute_command(self, text):
        """执行命令（使用 React Agent）"""
        print(f"🤖 开始执行: {text}")

        try:
            # 使用 React Agent 执行（自动多轮推理）
            result = self.agent.execute_command(text, enable_voice=self.enable_voice)

            if result.get("success"):
                print(f"✓ 执行完成 (共 {result.get('steps', 0)} 步)\n")
            else:
                print(f"✗ 执行失败: {result.get('message', '未知错误')}\n")
        except Exception as e:
            print(f"⚠️ 命令执行异常: {e}\n")
            import traceback
            traceback.print_exc()
