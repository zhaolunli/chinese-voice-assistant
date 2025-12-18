"""快速测试各个模型是否可用"""
import sherpa_onnx
from pathlib import Path
import wave
import numpy as np

print("="*60)
print("🔊 测试 TTS (语音合成)")
print("="*60)

# TTS测试
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

# 生成音频（使用sid而不是speaker_id）
text = "你好，这是测试"
print(f"🎤 生成文本: {text}")
audio = tts.generate(text, sid=0, speed=1.0)

# 保存音频
output_file = "test_output.wav"
with wave.open(output_file, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(tts.sample_rate)
    wf.writeframes((audio.samples * 32767).astype(np.int16).tobytes())

print(f"✅ 已生成: {output_file}")

# 播放
try:
    import winsound
    print("🔊 正在播放...")
    winsound.PlaySound(output_file, winsound.SND_FILENAME)
    print("✅ 播放完成")
except:
    print("⚠️ 无法播放，但文件已生成")

print("\n" + "="*60)
print("🎙️ 测试 STT (语音识别)")
print("="*60)

# STT测试
stt_dir = Path("models/sherpa-onnx-paraformer-zh-2024-03-09")
encoder = list(stt_dir.glob("*encoder*.onnx"))[0]

config = sherpa_onnx.OfflineRecognizerConfig(
    model_config=sherpa_onnx.OfflineModelConfig(
        paraformer=sherpa_onnx.OfflineParaformerModelConfig(
            model=str(encoder),
        ),
        tokens=str(stt_dir / "tokens.txt"),
        num_threads=2,
    )
)

recognizer = sherpa_onnx.OfflineRecognizer(config)
print(f"✅ STT加载成功，采样率: {recognizer.sample_rate} Hz")

# 识别刚才生成的音频
print(f"🎧 识别音频: {output_file}")
with wave.open(output_file, 'rb') as wf:
    samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    samples = samples.astype(np.float32) / 32768.0

stream = recognizer.create_stream()
stream.accept_waveform(tts.sample_rate, samples)
recognizer.decode_stream(stream)

result = stream.result.text
print(f"📝 识别结果: {result}")

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
print("🎉 所有核心功能测试通过！")
print("="*60)
