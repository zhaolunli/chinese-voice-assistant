# 智能语音助手

<div align="center">

**双阶段语音识别 + React智能代理 + Playwright浏览器控制 + 多引擎TTS**

基于 Sherpa-ONNX + Qwen + Playwright MCP + Piper 的中文语音助手

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](https://github.com/yourusername/chinese-voice-assistant)

</div>

## ✨ 特性

### 🎯 双阶段识别架构
- **阶段1 - 唤醒词检测（KWS）**: 轻量级关键词检测（3.3MB），持续监听，CPU占用低
- **阶段2 - 语音识别（ASR）**: 唤醒后启动完整语音识别（120MB），准确率高

### 🚀 核心功能
- **🎤 语音唤醒**: 支持自定义唤醒词（默认：小智、你好助手、智能助手）
- **🗣️ 语音识别**: 基于 Paraformer 的中文 ASR，识别准确，自动静音检测
- **🔊 语音合成**: 三种TTS引擎
  - **Piper TTS** - 本地超低延迟（推荐）⚡
  - **RealtimeTTS** - 流式实时播放 🎵
  - **MeloTTS** - 中英文混合支持 🌐
- **🧠 React Agent**: 多轮推理决策框架，自动规划执行步骤
- **🎭 Playwright MCP**: 浏览器自动化操作（主要使用）
  - 网页导航、元素交互、截图、PDF生成等
  - 支持 Chrome/Firefox/Safari 浏览器控制
- **👁️ 视觉理解**: Qwen-VL-Max 多模态理解，可分析屏幕内容
- **💾 长期记忆**: 5分钟时间窗口的跨会话记忆持久化

### 🎨 技术亮点
- 📦 模块化架构，代码结构清晰
- ⚡ **高性能**：Playwright 浏览器自动化，精确可靠
- 🎯 **高准确率**：浏览器操作准确率可达 **95%+**
- 🌐 云端大模型集成（Qwen-Plus）
- 🔇 智能静音检测，说完即停
- 🎵 TTS播放期间自动暂停监听
- 🛡️ 支持执行中断（可被新唤醒词打断）
- 🧠 本地+云端混合推理

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
# 下载 KWS + ASR + VAD 模型
python scripts/download_models.py

# 下载 Piper TTS 中文模型（推荐）
python download_piper_model.py
```

模型文件约 250MB，包括：
- **KWS 模型**（3.3MB）- Zipformer WenetSpeech（唤醒词检测）
- **ASR 模型**（120MB）- Paraformer 中文（语音识别）
- **Piper TTS 模型**（~50MB）- 中文语音合成（本地、超低延迟）
- **VAD 模型**（1MB）- Silero VAD（静音检测）
- **MeloTTS 模型**（可选）- 中英文混合（备选方案）

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

#### 🌐 浏览器导航（基于 Playwright MCP）
```
"打开浏览器访问百度"
"访问 https://www.github.com"
"浏览器后退"
"浏览器前进"
"刷新页面"
"关闭当前标签页"
```

#### 🖱️ 网页交互（基于 Playwright MCP）
```
"点击搜索框"
"点击登录按钮"
"在输入框输入测试文本"
"填写表单"
"提交表单"
"滚动到页面底部"
```

#### 📸 屏幕截图（基于 Playwright MCP）
```
"截取当前页面"
"保存页面为PDF"
"截图保存"
```

#### 🔍 信息提取（基于 Playwright MCP）
```
"获取页面标题"
"获取页面内容"
"查看浏览器控制台"
```

#### 👁️ 视觉理解（基于 Vision）
```
"看看浏览器窗口显示了什么"
"分析当前屏幕内容"
"这个页面是关于什么的"
```

---

## 📁 项目结构

```
chinese-voice-assistant/
├── src/voice_assistant/      # 核心源代码
│   ├── __init__.py           # 模块导出
│   ├── config.py             # 配置管理
│   ├── wake_word.py          # 唤醒词系统 (双阶段识别)
│   ├── react_agent.py        # React 智能代理 (推理框架)
│   ├── mcp_client.py         # MCP 客户端 (Playwright 浏览器控制)
│   ├── tts.py                # TTS 语音合成 (多引擎管理)
│   └── vision.py             # 视觉理解 (Qwen-VL-Max)
│
├── scripts/                  # 工具脚本
│   ├── download_models.py    # 模型下载
│   ├── pinyin_helper.py      # 拼音转换助手
│   └── install_playwright.bat # Playwright 安装
│
├── tests/                    # 测试文件
│   ├── quick_test_fixed.py   # TTS/ASR/KWS 快速测试
│   ├── test_models.py        # 完整模型测试
│   └── test_screenshot.py    # 截图功能测试
│
├── config/                   # 配置文件
│   ├── keywords.txt          # 唤醒词配置 (主)
│   ├── wake_words.txt        # 唤醒词配置 (备)
│   └── chinese_wake_words.txt # 中文唤醒词
│
├── models/                   # 模型文件（需下载）
│   ├── piper/                # Piper TTS 模型
│   ├── sherpa-onnx-kws-*/    # KWS 关键词检测
│   └── sherpa-onnx-paraformer-zh/ # ASR 语音识别
│
├── docs/                     # 文档
│   ├── MCP_INTEGRATION.md    # MCP 集成指南
│   └── PLAYWRIGHT_SETUP.md   # Playwright 设置
│
├── data/                     # 运行时数据
│   ├── tts_audio/           # TTS 音频缓存
│   └── memory/              # 长期记忆存储
│
├── main.py                   # 主程序入口
├── download_piper_model.py   # Piper 模型下载
├── pyproject.toml            # 项目配置 (v2.0.0)
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

### 核心模块说明
项目采用模块化设计，各模块职责清晰：

| 模块 | 职责 | 代码行数 |
|-----|------|---------|
| `wake_word.py` | 双阶段识别（KWS + ASR）、音频录制、静音检测 | ~13K |
| `react_agent.py` | React 推理框架、多轮决策、长期记忆管理 | ~32K |
| `mcp_client.py` | MCP 客户端、Playwright 浏览器自动化 | ~19K |
| `tts.py` | TTS 引擎管理（Piper/RealtimeTTS/MeloTTS） | ~24K |
| `vision.py` | Qwen-VL-Max 视觉理解、屏幕截图分析 | ~73 |
| `config.py` | 全局配置、API Keys、路径管理 | - |

### 添加新功能
1. **添加新的 Playwright 操作**: 在 `mcp_client.py` 中调用 Playwright 工具
2. **添加新的 TTS 引擎**: 在 `tts.py` 的 `TTSManager` 类中添加引擎
3. **添加新的唤醒词**: 编辑 `config/keywords.txt`
4. **扩展 React Agent**: 在 `react_agent.py` 中添加新的推理逻辑

---

## ⚠️ 注意事项

1. **API 费用**: 使用阿里云 API（LLM、Vision）会产生费用，请注意配额
   - 推荐使用 Piper TTS（免费本地）代替阿里云 TTS
   - Playwright 操作本地执行，无 API 费用

2. **隐私安全**:
   - API Key 不要提交到公开仓库
   - 建议使用环境变量管理敏感信息
   - 本地模型（Piper、Sherpa-ONNX）无隐私风险

3. **系统兼容**:
   - Playwright 支持 Windows/Linux/macOS
   - 需要安装 Node.js 和 npx（用于启动 Playwright MCP）
   - 首次使用需要下载浏览器驱动

4. **网络需求**:
   - **无需网络**: KWS、ASR、Piper TTS（完全离线）
   - **需要网络**: LLM 决策、Vision 理解、阿里云 TTS
   - **首次需要**: Playwright MCP 安装（`npx @playwright/mcp@latest`）

5. **性能建议**:
   - Playwright 适合浏览器操作，准确率高
   - 简单网页操作优先使用 Playwright
   - 复杂场景结合 Vision 理解
   - 推荐 Piper TTS（100ms 延迟 vs 500ms）

---

## 🛠️ 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **语音识别** | | |
| 唤醒词检测 | Sherpa-ONNX (Zipformer) | 3.3MB 轻量级 KWS |
| 语音识别 | Sherpa-ONNX (Paraformer) | 120MB 中文 ASR |
| 静音检测 | Silero VAD | 1MB 语音活动检测 |
| **语音合成** | | |
| 本地 TTS | Piper TTS | 超低延迟（推荐） |
| 流式 TTS | RealtimeTTS | 实时流式播放 |
| 混合 TTS | MeloTTS | 中英文支持 |
| 云端 TTS | 阿里云 DashScope | 备选方案 |
| **智能决策** | | |
| 推理框架 | React Agent | 多轮思考+行动 |
| LLM 模型 | Qwen-Plus | 意图理解+规划 |
| 长期记忆 | JSON 持久化 | 5分钟时间窗口 |
| **浏览器控制** | | |
| MCP 框架 | Playwright MCP | 浏览器自动化 |
| 网页交互 | Playwright | 跨浏览器支持 |
| **视觉理解** | | |
| 多模态模型 | Qwen-VL-Max | 屏幕内容分析 |
| 截图工具 | PIL ImageGrab | 屏幕截图 |
| **其他** | | |
| 音频处理 | PyAudio + NumPy | 录音播放 |
| HTTP 请求 | requests | API 调用 |
| Python 版本 | 3.12+ | 必需 |
| Node.js | 18+ | Playwright MCP 必需 |

---

## 📝 常见问题

### Q: 为什么识别不到唤醒词？
A:
- 检查麦克风是否正常工作
- 确认唤醒词是否在配置文件中（`config/keywords.txt`）
- 尝试提高音量，靠近麦克风说话
- 检查是否下载了 KWS 模型（3.3MB）

### Q: TTS 播放失败？
A:
- **使用 Piper TTS（推荐）**: 完全本地，无需网络和 API
- **使用阿里云 TTS**: 检查 API Key 是否正确，确认网络连接正常
- 查看控制台错误信息
- 确认已下载 Piper 模型：`python download_piper_model.py`

### Q: 如何选择 TTS 引擎？
A: 在启动时会提示选择，建议：
- **Piper TTS**: 最快，本地运行，推荐日常使用 ⚡
- **RealtimeTTS**: 流式播放，适合长文本
- **阿里云 TTS**: 音质最佳，但需要网络

### Q: Playwright MCP 无法使用？
A:
- 确认已安装 Node.js（版本 18+）
- 检查 npx 命令是否可用：`npx --version`
- 手动安装 Playwright MCP：`npx @playwright/mcp@latest`
- 查看 `docs/PLAYWRIGHT_SETUP.md` 获取详细配置说明
- 检查控制台是否有 Playwright 启动错误信息

### Q: 如何添加自定义唤醒词？
A: 编辑 `config/keywords.txt`，格式为：`拼音音节 @中文`
```text
x iǎo ài t óng x ué @小爱同学
t iān m āo j īng l íng @天猫精灵
```
**提示**: 使用 `scripts/pinyin_helper.py` 辅助生成带声调的拼音

### Q: Vision 理解不准确？
A:
- Vision 现在主要用于复杂场景分析，浏览器操作推荐使用 Playwright
- Playwright 工具直接操作浏览器，准确率更高
- 如需使用 Vision，确保 DashScope API Key 正确配置
- Vision 适合"看看这个页面是什么内容"这类理解任务

### Q: 如何查看 React Agent 的推理过程？
A:
- 在控制台会输出完整的 Thought → Action → Observation 循环
- 可以看到 Agent 的思考和决策步骤
- 查看 `data/memory/` 目录了解长期记忆内容

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🔥 最近更新

### v2.0.0 - 架构升级版本（2025-01）

#### ✨ 新增特性
1. **Piper TTS 集成** - 本地超低延迟语音合成
   - 延迟降低至 100-200ms
   - 完全离线运行
   - 中文音色自然

2. **RealtimeTTS 支持** - 流式实时播放
   - 边生成边播放
   - 更好的实时体验

3. **Playwright MCP 集成** - 浏览器自动化控制
   - 网页导航、元素交互、截图
   - 支持 Chrome/Firefox/Safari
   - 跨平台支持（Windows/Linux/macOS）

4. **React Agent 框架** - 智能推理决策
   - 多轮思考+行动循环
   - 自动错误纠正
   - 长期记忆支持

#### 🐛 Bug 修复
- 修复 Piper TTS 长文本截断问题
- 修复 Vision API 错误处理
- 添加 Vision 模式中断检查
- 改进 JSON 格式化和解析

#### 📊 性能提升
- TTS 延迟从 500ms → 100ms（Piper）
- Playwright 浏览器操作响应迅速
- React Agent 智能规划优化执行流程

---

## 🙏 致谢

- [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) - 高性能语音识别框架
- [Playwright](https://playwright.dev/) - 强大的浏览器自动化工具
- [Playwright MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/playwright) - Playwright MCP 服务器
- [Piper TTS](https://github.com/rhasspy/piper) - 快速本地文本转语音引擎
- [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS) - 流式语音合成库
- [阿里云 DashScope](https://dashscope.aliyun.com/) - 多模态 API 和 LLM 服务
- [Qwen](https://github.com/QwenLM/Qwen) - 强大的大语言模型和视觉模型

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️

</div>
