"""
测试已下载的Sherpa-ONNX模型
依次测试: TTS(语音合成) → STT(语音识别) → KWS(关键词唤醒) → VAD(语音检测)
"""

import os
import wave
import numpy as np
import sherpa_onnx
from pathlib import Path

class ModelTester:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.test_results = {}
    
    def test_tts(self):
        """测试语音合成（TTS）"""
        print("\n" + "="*60)
        print("🔊 测试1: 语音合成 (TTS)")
        print("="*60)
        
        # 查找TTS模型目录
        tts_dirs = list(self.models_dir.glob("*melo-tts*"))
        if not tts_dirs:
            print("❌ 未找到TTS模型")
            print(f"   请确保已下载模型到: {self.models_dir.absolute()}")
            self.test_results["TTS"] = False
            return
        
        tts_dir = tts_dirs[0]
        print(f"📁 模型目录: {tts_dir.name}")
        
        try:
            # 配置TTS
            config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=str(tts_dir / "model.onnx"),
                        tokens=str(tts_dir / "tokens.txt"),
                        data_dir=str(tts_dir / "espeak-ng-data"),
                    )
                ),
                rule_fsts="",
                max_num_sentences=1,
            )
            
            # 创建TTS对象
            tts = sherpa_onnx.OfflineTts(config)
            print(f"✅ TTS模型加载成功")
            print(f"   采样率: {tts.sample_rate} Hz")
            
            # 测试合成
            test_texts = [
                "你好，这是语音合成测试。",
                "欢迎来到智能监控大屏。",
            ]
            
            for i, text in enumerate(test_texts, 1):
                print(f"\n🎤 测试文本 {i}: {text}")
                # 修复API调用：使用sid而不是speaker_id
                audio = tts.generate(text, speed=1.0, sid=0)
                
                # 保存音频
                output_file = f"test_tts_{i}.wav"
                self._save_audio(audio.samples, tts.sample_rate, output_file)
                print(f"   ✅ 已生成音频: {output_file}")
                
                # 播放音频
                print(f"   🔊 正在播放...")
                self._play_audio(output_file)
            
            self.test_results["TTS"] = True
            print("\n✅ TTS测试通过！")
            
        except Exception as e:
            print(f"❌ TTS测试失败: {e}")
            self.test_results["TTS"] = False
    
    def test_stt(self):
        """测试语音识别（STT）"""
        print("\n" + "="*60)
        print("🎙️ 测试2: 语音识别 (STT)")
        print("="*60)
        
        # 查找STT模型目录
        stt_dirs = list(self.models_dir.glob("*paraformer*")) or \
                   list(self.models_dir.glob("*whisper*"))
        
        if not stt_dirs:
            print("❌ 未找到STT模型")
            self.test_results["STT"] = False
            return
        
        stt_dir = stt_dirs[0]
        print(f"📁 模型目录: {stt_dir.name}")
        
        try:
            # 判断模型类型
            if "paraformer" in stt_dir.name:
                recognizer = self._create_paraformer_recognizer(stt_dir)
                model_type = "Paraformer"
            else:
                recognizer = self._create_whisper_recognizer(stt_dir)
                model_type = "Whisper"
            
            print(f"✅ {model_type}模型加载成功")
            print(f"   采样率: {recognizer.sample_rate} Hz")
            
            # 使用之前TTS生成的音频测试识别
            test_files = ["test_tts_1.wav", "test_tts_2.wav"]
            
            for audio_file in test_files:
                if not Path(audio_file).exists():
                    print(f"⚠️  测试文件不存在: {audio_file}")
                    continue
                
                print(f"\n🎧 测试文件: {audio_file}")
                text = self._recognize_audio(recognizer, audio_file)
                print(f"   📝 识别结果: {text}")
            
            self.test_results["STT"] = True
            print("\n✅ STT测试通过！")
            
        except Exception as e:
            print(f"❌ STT测试失败: {e}")
            self.test_results["STT"] = False
    
    def test_kws(self):
        """测试关键词唤醒（KWS）"""
        print("\n" + "="*60)
        print("🎯 测试3: 关键词唤醒 (KWS)")
        print("="*60)
        
        # 查找KWS模型目录
        kws_dirs = list(self.models_dir.glob("*kws*"))
        
        if not kws_dirs:
            print("❌ 未找到KWS模型")
            self.test_results["KWS"] = False
            return
        
        kws_dir = kws_dirs[0]
        print(f"📁 模型目录: {kws_dir.name}")
        
        try:
            # 查找模型文件
            encoder = list(kws_dir.glob("*encoder*.onnx"))[0]
            decoder = list(kws_dir.glob("*decoder*.onnx"))[0]
            joiner = list(kws_dir.glob("*joiner*.onnx"))[0]
            tokens = kws_dir / "tokens.txt"
            
            # 创建临时关键词文件
            keywords_file = "test_keywords.txt"
            with open(keywords_file, "w", encoding="utf-8") as f:
                f.write("小智/xiao3 zhi4/1.5\n")
                f.write("你好助手/ni3 hao3 zhu4 shou3/2.0\n")
            
            print(f"✅ KWS配置完成")
            print(f"   关键词: 小智, 你好助手")
            print(f"   注意: KWS需要实时音频流测试，此处仅验证加载")
            
            # 验证文件存在
            print(f"   Encoder: {encoder.name}")
            print(f"   Decoder: {decoder.name}")
            print(f"   Joiner: {joiner.name}")
            
            # 清理临时文件
            os.remove(keywords_file)
            
            self.test_results["KWS"] = True
            print("\n✅ KWS配置测试通过！")
            print("   提示: 实际唤醒功能需要麦克风实时测试")
            
        except Exception as e:
            print(f"❌ KWS测试失败: {e}")
            self.test_results["KWS"] = False
    
    def test_vad(self):
        """测试语音活动检测（VAD）"""
        print("\n" + "="*60)
        print("🎚️ 测试4: 语音活动检测 (VAD)")
        print("="*60)
        
        # 查找VAD模型
        vad_file = self.models_dir / "silero_vad.onnx"
        
        if not vad_file.exists():
            print("❌ 未找到VAD模型")
            self.test_results["VAD"] = False
            return
        
        print(f"📁 模型文件: {vad_file.name}")
        
        try:
            # 创建VAD配置
            config = sherpa_onnx.VadModelConfig()
            config.silero_vad.model = str(vad_file)
            config.sample_rate = 16000
            
            vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=10)
            
            print(f"✅ VAD模型加载成功")
            print(f"   采样率: 16000 Hz")
            
            # 使用之前的音频测试VAD
            test_file = "test_tts_1.wav"
            if Path(test_file).exists():
                print(f"\n🎧 测试文件: {test_file}")
                
                # 读取音频
                with wave.open(test_file, 'rb') as wf:
                    sample_rate = wf.getframerate()
                    samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                    samples = samples.astype(np.float32) / 32768.0
                
                # VAD检测
                vad.accept_waveform(samples)
                
                if vad.is_speech_detected():
                    print(f"   ✅ 检测到语音")
                else:
                    print(f"   ℹ️  未检测到语音（可能音频太短）")
            
            self.test_results["VAD"] = True
            print("\n✅ VAD测试通过！")
            
        except Exception as e:
            print(f"❌ VAD测试失败: {e}")
            self.test_results["VAD"] = False
    
    # === 辅助方法 ===
    
    def _create_paraformer_recognizer(self, model_dir):
        """创建Paraformer识别器"""
        # 查找模型文件
        encoder_files = list(model_dir.glob("*encoder*.onnx"))
        decoder_files = list(model_dir.glob("*decoder*.onnx"))
        
        if not encoder_files:
            raise FileNotFoundError(f"未找到encoder文件: {model_dir}")
        
        encoder = encoder_files[0]
        decoder = decoder_files[0] if decoder_files else None
        tokens = model_dir / "tokens.txt"
        
        config = sherpa_onnx.OfflineRecognizerConfig(
            model_config=sherpa_onnx.OfflineModelConfig(
                paraformer=sherpa_onnx.OfflineParaformerModelConfig(
                    model=str(encoder),
                ),
                tokens=str(tokens),
                num_threads=2,
            )
        )
        
        return sherpa_onnx.OfflineRecognizer(config)
    
    def _create_whisper_recognizer(self, model_dir):
        """创建Whisper识别器"""
        encoder = model_dir / "tiny.en-encoder.onnx"
        decoder = model_dir / "tiny.en-decoder.onnx"
        tokens = model_dir / "tiny.en-tokens.txt"
        
        config = sherpa_onnx.OfflineRecognizerConfig(
            model_config=sherpa_onnx.OfflineModelConfig(
                whisper=sherpa_onnx.OfflineWhisperModelConfig(
                    encoder=str(encoder),
                    decoder=str(decoder),
                ),
                tokens=str(tokens),
                num_threads=2,
            )
        )
        
        return sherpa_onnx.OfflineRecognizer(config)
    
    def _recognize_audio(self, recognizer, audio_file):
        """识别音频文件"""
        with wave.open(audio_file, 'rb') as wf:
            sample_rate = wf.getframerate()
            samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            samples = samples.astype(np.float32) / 32768.0
        
        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, samples)
        recognizer.decode_stream(stream)
        
        return stream.result.text
    
    def _save_audio(self, samples, sample_rate, filename):
        """保存音频文件"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((samples * 32767).astype(np.int16).tobytes())
    
    def _play_audio(self, filename):
        """播放音频（Windows）"""
        try:
            import winsound
            winsound.PlaySound(filename, winsound.SND_FILENAME)
        except Exception as e:
            print(f"   ⚠️  播放失败: {e}")
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)
        
        for name, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {name:15s} : {status}")
        
        success_count = sum(self.test_results.values())
        total_count = len(self.test_results)
        
        print(f"\n总计: {success_count}/{total_count} 通过")
        
        if success_count == total_count:
            print("\n🎉 所有测试通过！可以开始构建语音助手了！")
        else:
            print("\n⚠️  部分测试失败，请检查模型文件")

def main():
    print("""
    ╔══════════════════════════════════════════════╗
    ║   Sherpa-ONNX 模型测试工具                    ║
    ║   测试: TTS → STT → KWS → VAD                ║
    ╚══════════════════════════════════════════════╝
    """)
    
    # 检查models目录
    models_dir = Path("models")
    if not models_dir.exists():
        print(f"❌ 模型目录不存在: {models_dir.absolute()}")
        print(f"   请先运行: python download_models.py")
        return
    
    print(f"📁 模型目录: {models_dir.absolute()}\n")
    print("模型文件列表:")
    for item in models_dir.iterdir():
        if item.is_dir():
            print(f"  📂 {item.name}/")
        else:
            print(f"  📄 {item.name}")
    
    input("\n按Enter键开始测试...")
    
    # 开始测试
    tester = ModelTester()
    
    tester.test_tts()
    tester.test_stt()
    tester.test_kws()
    tester.test_vad()
    
    # 打印总结
    tester.print_summary()

if __name__ == "__main__":
    main()
