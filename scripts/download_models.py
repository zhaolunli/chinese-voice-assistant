"""
下载Sherpa-ONNX所需的模型文件
适用于：语音唤醒(KWS) + 语音识别(STT) + 语音合成(TTS)
"""

import os
import urllib.request
import tarfile
from pathlib import Path

# 模型下载配置
MODELS = {
    # 语音唤醒模型（小巧，3.3MB）
    "kws": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01.tar.bz2",
        "filename": "kws.tar.bz2",
        "description": "语音唤醒模型 (支持自定义唤醒词)"
    },
    
    # 中文语音识别模型（Paraformer，最优，120MB）
    "stt_zh": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-2024-03-09.tar.bz2",
        "filename": "stt-zh.tar.bz2",
        "description": "中文语音识别模型 (Paraformer)"
    },
    
    # 英文语音识别模型（Whisper Tiny，快速，75MB）
    "stt_en": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.en.tar.bz2",
        "filename": "stt-en.tar.bz2",
        "description": "英文语音识别模型 (Whisper Tiny)"
    },
    
    # 中文语音合成模型（MeloTTS，50MB）
    "tts_zh": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2",
        "filename": "tts-zh.tar.bz2",
        "description": "中文语音合成模型 (MeloTTS 中英混合)"
    },
    
    # VAD模型（语音活动检测，1MB）
    "vad": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx",
        "filename": "silero_vad.onnx",
        "description": "语音活动检测模型 (VAD)",
        "is_single_file": True
    }
}

def download_file(url: str, save_path: str, description: str):
    """下载文件并显示进度"""
    print(f"\n📥 正在下载: {description}")
    print(f"    链接: {url}")
    print(f"    保存到: {save_path}")
    
    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100.0 / total_size, 100)
        print(f"\r    进度: {percent:.1f}% ({downloaded / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB)", end="")
    
    try:
        urllib.request.urlretrieve(url, save_path, show_progress)
        print("\n    ✅ 下载完成！")
        return True
    except Exception as e:
        print(f"\n    ❌ 下载失败: {e}")
        return False

def extract_tar(tar_path: str, extract_to: str):
    """解压tar.bz2文件"""
    print(f"\n📦 正在解压: {tar_path}")
    try:
        with tarfile.open(tar_path, 'r:bz2') as tar:
            tar.extractall(extract_to)
        print(f"    ✅ 解压完成！")
        
        # 删除压缩包
        os.remove(tar_path)
        print(f"    🗑️  已删除压缩包")
        return True
    except Exception as e:
        print(f"    ❌ 解压失败: {e}")
        return False

def main():
    print("""
    ╔══════════════════════════════════════════════╗
    ║   Sherpa-ONNX 模型下载工具                    ║
    ║   支持: KWS + STT + TTS + VAD                ║
    ╚══════════════════════════════════════════════╝
    """)
    
    # 创建models目录
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    print(f"📁 模型保存目录: {models_dir.absolute()}\n")
    
    # 选择要下载的模型
    print("请选择要下载的模型：")
    print("1. 全部下载（推荐，约250MB）")
    print("2. 仅核心功能（KWS + STT中文 + TTS中文，约173MB）")
    print("3. 自定义选择")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    if choice == "1":
        selected_models = list(MODELS.keys())
    elif choice == "2":
        selected_models = ["kws", "stt_zh", "tts_zh", "vad"]
    elif choice == "3":
        print("\n可选模型：")
        for i, (key, info) in enumerate(MODELS.items(), 1):
            print(f"{i}. {key} - {info['description']}")
        
        selected_nums = input("\n请输入模型编号（用逗号分隔，如: 1,2,4): ").strip()
        selected_models = [list(MODELS.keys())[int(n)-1] for n in selected_nums.split(",")]
    else:
        print("❌ 无效选项，退出")
        return
    
    print(f"\n将下载以下模型: {', '.join(selected_models)}")
    input("按Enter键开始下载...")
    
    # 开始下载
    success_count = 0
    for model_key in selected_models:
        model_info = MODELS[model_key]
        save_path = models_dir / model_info["filename"]
        
        # 下载
        if download_file(model_info["url"], str(save_path), model_info["description"]):
            # 如果是压缩包，解压
            if not model_info.get("is_single_file", False):
                if extract_tar(str(save_path), str(models_dir)):
                    success_count += 1
            else:
                success_count += 1
        
        print("-" * 60)
    
    # 总结
    print(f"\n{'='*60}")
    print(f"✅ 下载完成! 成功: {success_count}/{len(selected_models)}")
    print(f"📁 模型目录: {models_dir.absolute()}")
    print(f"\n目录结构:")
    
    for item in models_dir.iterdir():
        if item.is_dir():
            print(f"  📂 {item.name}/")
        else:
            print(f"  📄 {item.name}")
    
    print(f"\n下一步: 运行 'python test_models.py' 测试模型")

if __name__ == "__main__":
    main()
