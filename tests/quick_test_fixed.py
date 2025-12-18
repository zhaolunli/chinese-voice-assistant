"""快速测试各个模型 - 完全修复版"""
import sherpa_onnx
from pathlib import Path
import wave
import numpy as np

print("="*60)
print("🔊 测试 TTS (语音合成) - 中文测试")
print("="*60)

# TTS测试 - 使用中文（MeloTTS是为中文设计的）
tts_dir = Path("models/vits-melo-tts-zh_en")
config = sherpa_onnx.OfflineTtsConfig(
    model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(
            model=str(tts_dir / "model.onnx"),
            tokens=str(tts_dir / "tokens.txt"),
            data_dir=str(tts_dir / "espeak-ng-data"),
        )
    ),
    max_num_sentences=1,
)

tts = sherpa_onnx.OfflineTts(config)
print(f"✅ TTS加载成功，采样率: {tts.sample_rate} Hz")

# 使用拼音测试（避免编码问题）
text = "ni hao shi jie"  # 你好世界的拼音
print(f"🎤 生成文本: {text}")
audio = tts.generate(text, sid=0, speed=1.0)

# 修复: 将list转换为numpy数组
if isinstance(audio.samples, list):
    audio_samples = np.array(audio.samples, dtype=np.float32)
else:
    audio_samples = audio.samples

# 保存音频
output_file = "test_output.wav"
with wave.open(output_file, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(tts.sample_rate)
    wf.writeframes((audio_samples * 32767).astype(np.int16).tobytes())

print(f"✅ 已生成: {output_file}")
print(f"   文件大小: {Path(output_file).stat().st_size / 1024:.1f} KB")

# 播放
try:
    import winsound
    print("🔊 正在播放...")
    winsound.PlaySound(output_file, winsound.SND_FILENAME)
    print("✅ 播放完成")
except Exception as e:
    print(f"⚠️ 播放失败: {e}")

print("\n" + "="*60)
print("🎙️ 测试 STT (语音识别) - Paraformer")
print("="*60)

# STT测试 - 修复Paraformer配置
stt_dir = Path("models/sherpa-onnx-paraformer-zh-2024-03-09")
print(f"📁 STT目录: {stt_dir}")

# 使用int8量化模型（更快）
model_file = stt_dir / "model.int8.onnx"
tokens_file = stt_dir / "tokens.txt"

print(f"✅ 使用模型: {model_file.name}")

try:
    # 修复: 使用正确的Paraformer配置方式
    recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
        paraformer=str(model_file),
        tokens=str(tokens_file),
        num_threads=2,
        sample_rate=16000,
        feature_dim=80,
        decoding_method="greedy_search",
    )
    
    print(f"✅ STT加载成功")

    # 识别刚才生成的音频
    print(f"🎧 识别音频: {output_file}")
    with wave.open(output_file, 'rb') as wf:
        sample_rate = wf.getframerate()
        samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        samples = samples.astype(np.float32) / 32768.0
    
    print(f"   原始采样率: {sample_rate} Hz")
    print(f"   音频长度: {len(samples) / sample_rate:.2f} 秒")

    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, samples)
    recognizer.decode_stream(stream)

    result = stream.result.text
    print(f"📝 识别结果: '{result}'")
    
    if result.strip():
        print("✅ STT识别成功！")
    else:
        print("⚠️ 识别结果为空（可能音频内容不是中文语音）")
        
except Exception as e:
    print(f"❌ STT测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🎚️ 测试 VAD (语音活动检测)")
print("="*60)

vad_file = Path("models/silero_vad.onnx")
config = sherpa_onnx.VadModelConfig()
config.silero_vad.model = str(vad_file)
config.sample_rate = 16000

vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=10)
print(f"✅ VAD加载成功")

print("\n" + "="*60)
print("🎉 核心功能测试完成！")
print("="*60)
print("\n💡 提示:")
print("1. TTS使用拼音输入可避免中文编码问题")
print("2. 也可以直接在Python中使用中文字符串")
print("3. 测试音频文件已保存: test_output.wav")
print("4. 可以用Windows Media Player等播放器打开查看")
