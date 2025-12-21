"""下载 Piper TTS 中文模型"""
import requests
from pathlib import Path

MODEL_DIR = Path("models/piper")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# 中文模型（huayan - 华燕）
MODEL_NAME = "zh_CN-huayan-medium"
BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium"

files = [
    f"{MODEL_NAME}.onnx",
    f"{MODEL_NAME}.onnx.json"
]

print("开始下载 Piper 中文模型...")
for filename in files:
    url = f"{BASE_URL}/{filename}"
    output_path = MODEL_DIR / filename

    print(f"  下载: {filename}...", end="", flush=True)

    try:
        response = requests.get(url, timeout=300, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            if total_size > 0:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / total_size) * 100
                    print(f"\r  下载: {filename}... {progress:.1f}%", end="", flush=True)
            else:
                f.write(response.content)

        print(f"\r  ✓ {filename} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")
    except Exception as e:
        print(f"\r  ✗ {filename} 下载失败: {e}")

print("\n✓ 模型下载完成！")
print(f"模型路径: {MODEL_DIR.absolute()}")
