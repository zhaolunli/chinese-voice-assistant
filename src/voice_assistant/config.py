"""配置文件"""
import os
from pathlib import Path

# API配置 - 建议使用环境变量
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-49d20b6630984acabb4f28aa0bc7ab17")
ALIYUN_APPKEY = os.getenv("ALIYUN_APPKEY", "YOUR_APPKEY")

# API URL
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ALIYUN_TTS_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/rest/v1/tts/async"

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
TTS_AUDIO_DIR = DATA_DIR / "tts_audio"

# 音频配置
SAMPLE_RATE = 16000
CHUNK_SIZE = 512

# TTS配置
TTS_SHORT_TEXT_LIMIT = 280  # 短文本TTS字符限制
TTS_CACHE_TIMEOUT_SHORT = 10  # 短文本缓存清理时间（秒）
TTS_CACHE_TIMEOUT_LONG = 30   # 长文本缓存清理时间（秒）

# 录音配置
RECORD_SECONDS = 5
SILENCE_THRESHOLD = 0.02
MAX_SILENCE_FRAMES = 40

# 唤醒词配置（格式：拼音音节 @中文）
DEFAULT_WAKE_WORDS = [
    "x iǎo zh ì @小智",
    "n ǐ h ǎo zh ù sh ǒu @你好助手",
    "zh ì n éng zh ù sh ǒu @智能助手"
]
