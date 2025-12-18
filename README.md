# 智能语音助手

<div align="center">

**双阶段语音识别 + 视觉理解 + 系统控制**

基于 Sherpa-ONNX + Qwen + 阿里云 DashScope 的中文语音助手

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## ✨ 特性

### 🎯 双阶段识别架构
- **阶段1 - 唤醒词检测（KWS）**: 轻量级关键词检测，持续监听，CPU占用低
- **阶段2 - 语音识别（ASR）**: 唤醒后启动完整语音识别，准确率高

### 🚀 核心功能
- **🎤 语音唤醒**: 支持自定义唤醒词（默认：小智、你好助手、智能助手）
- **🗣️ 语音识别**: 基于 Paraformer 的中文 ASR，识别准确
- **🔊 语音合成**: 阿里云 TTS，支持长短文本自适应
- **👁️ 视觉理解**: Qwen-VL-Plus 多模态理解，可分析屏幕内容
- **🖥️ 系统控制**: Windows 应用控制、浏览器操作、智能截图

### 🎨 技术亮点
- 📦 模块化架构，代码结构清晰
- ⚡ 高性能本地推理（ONNX）
- 🌐 云端大模型集成（Qwen）
- 🔇 智能静音检测，自动停止录音
- 🎵 TTS播放期间自动暂停监听

---

## 📦 安装

### 1. 环境要求
- Python 3.12+
- Windows 10/11（系统控制功能仅支持 Windows）
- 麦克风设备

### 2. 克隆项目
```bash
git clone https://github.com/yourusername/voice-assistant.git
cd voice-assistant
```

### 3. 安装依赖
```bash
# 使用 uv（推荐）
uv pip install -e .

# 或使用 pip
pip install -e .
```

### 4. 下载模型
```bash
python scripts/download_models.py
```

模型文件约 250MB，包括：
- KWS 模型（3.3MB）- Zipformer WenetSpeech
- ASR 模型（120MB）- Paraformer 中文
- TTS 模型（50MB）- MeloTTS 中英文
- VAD 模型（1MB）- Silero VAD

---

## 🔧 配置

### API Keys
在 `src/voice_assistant/config.py` 中配置 API Key：

```python
# 方式1: 直接修改配置文件
DASHSCOPE_API_KEY = "your-api-key-here"
ALIYUN_APPKEY = "your-app-key-here"

# 方式2: 使用环境变量（推荐）
export DASHSCOPE_API_KEY="your-api-key-here"
export ALIYUN_APPKEY="your-app-key-here"
```

获取 API Key：
- [阿里云 DashScope](https://dashscope.console.aliyun.com/)

### 唤醒词配置
编辑 `config/keywords.txt`，使用以下格式：

```text
拼音音节(空格分隔) @中文
```

示例：
```text
x iǎo zh ì @小智
n ǐ h ǎo zh ù sh ǒu @你好助手
zh ì n éng zh ù sh ǒu @智能助手
x iǎo ài t óng x ué @小爱同学
```

**说明：**
- 使用带声调符号的拼音音节（ā á ǎ à ē é ě è 等）
- 音节之间用空格分隔
- 使用 @ 符号分隔拼音和中文
- 文件使用 UTF-8 编码（无需 BOM）

---

## 🚀 使用

### 启动助手
```bash
python main.py
```

### 交互流程
1. **唤醒**: 说出唤醒词（如"小智"）
2. **指令**: 听到提示音后，说出指令
3. **执行**: 系统自动理解并执行操作

### 支持的指令示例

#### 🌐 浏览器操作
```
"打开浏览器"
"查看浏览器内容"
"浏览器显示了什么"
```

#### 📱 应用控制
```
"打开记事本"
"打开计算器"
"打开文件管理器"
```

#### 📸 屏幕分析
```
"看看浏览器窗口"       # 智能定位浏览器
"查看当前窗口"         # 当前激活窗口
"截取整个屏幕"         # 全屏截图
```

---

## 📁 项目结构

```
voice-assistant/
├── src/voice_assistant/      # 核心源代码
│   ├── __init__.py           # 模块导出
│   ├── config.py             # 配置管理
│   ├── tts.py                # TTS 语音合成
│   ├── system_control.py     # 系统控制
│   ├── vision.py             # 视觉理解
│   ├── llm.py                # LLM 控制器
│   └── wake_word.py          # 唤醒词系统
│
├── scripts/                  # 工具脚本
│   └── download_models.py    # 模型下载
│
├── tests/                    # 测试文件
│   ├── quick_test.py
│   ├── quick_test_fixed.py
│   └── test_models.py
│
├── config/                   # 配置文件
│   ├── wake_words.txt
│   └── chinese_wake_words.txt
│
├── models/                   # 模型文件（需下载）
├── data/                     # 运行时数据
│   └── tts_audio/           # TTS 音频缓存
│
├── main.py                   # 主程序入口
├── pyproject.toml            # 项目配置
└── README.md                 # 项目文档
```

---

## 🧪 测试

### 测试所有模型
```bash
python tests/test_models.py
```

### 快速测试
```bash
python tests/quick_test_fixed.py
```

---

## 🔧 开发

### 代码格式化
```bash
# 安装开发依赖
pip install -e ".[dev]"

# 格式化代码
black src/

# 代码检查
ruff check src/
```

### 添加新功能
项目采用模块化设计，各模块职责清晰：
- `tts.py`: 语音合成相关
- `system_control.py`: 系统操作
- `vision.py`: 视觉理解
- `llm.py`: 大模型交互
- `wake_word.py`: 唤醒词和语音识别

---

## ⚠️ 注意事项

1. **API 费用**: 使用阿里云 API 会产生费用，请注意配额
2. **隐私安全**: API Key 不要提交到公开仓库
3. **系统兼容**: 系统控制功能仅支持 Windows
4. **网络需求**: LLM 和 TTS 需要网络连接

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 唤醒词检测 | Sherpa-ONNX (Zipformer) |
| 语音识别 | Sherpa-ONNX (Paraformer) |
| 语音合成 | 阿里云 DashScope TTS |
| 视觉理解 | Qwen-VL-Plus |
| 意图理解 | Qwen-Plus |
| 音频处理 | PyAudio, NumPy |
| 系统控制 | PyAutoGUI, PyGetWindow |

---

## 📝 常见问题

### Q: 为什么识别不到唤醒词？
A:
- 检查麦克风是否正常
- 确认唤醒词是否在配置文件中
- 尝试提高音量，靠近麦克风

### Q: TTS 播放失败？
A:
- 检查 API Key 是否正确
- 确认网络连接正常
- 查看控制台错误信息

### Q: 如何添加自定义唤醒词？
A: 编辑 `config/keywords.txt`，格式为：`拼音音节 @中文`
```text
x iǎo ài t óng x ué @小爱同学
t iān m āo j īng l íng @天猫精灵
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) - 语音识别框架
- [阿里云 DashScope](https://dashscope.aliyun.com/) - TTS 和多模态 API
- [Qwen](https://github.com/QwenLM/Qwen) - 大语言模型

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️

</div>
