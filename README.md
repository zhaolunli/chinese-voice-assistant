# 智能语音助手

<div align="center">

**双阶段语音识别 + React智能代理 + Playwright浏览器控制 + Pipecat实时音频处理**

基于 Sherpa-ONNX + Qwen + Playwright MCP + Piper + Pipecat 的中文语音助手

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](https://github.com/yourusername/chinese-voice-assistant)

</div>

## ✨ 特性

### 🎯 双模式架构
- **传统模式 (Traditional)**: 经典架构，稳定可靠
- **Pipecat 模式 (Experimental)**: 基于 Pipecat 框架的实时音频流处理

### 🚀 核心功能
- **🎤 语音唤醒**:
  - **阶段1 - KWS**: 轻量级关键词检测（3.3MB），持续监听，CPU占用低
  - **阶段2 - ASR**: 唤醒后启动完整语音识别（120MB），准确率高
  - 支持自定义唤醒词（默认：小智、你好助手、智能助手）

- **🧠 React Agent**: 多轮推理决策框架
  - 自动规划执行步骤
  - 支持同步（传统模式）和异步（Pipecat 模式）执行
  - 基于 MCP Python SDK 官方推荐模式

- **🎭 Playwright MCP**: 浏览器自动化操作
  - 网页导航、元素交互、截图、PDF生成等
  - 支持 Chrome/Firefox/Safari 浏览器控制
  - **完全异步**的工具调用（符合 MCP 官方最佳实践）

- **🔊 语音合成**: 多引擎支持
  - **Piper TTS** - 本地超低延迟（推荐）⚡
  - **RealtimeTTS** - 流式实时播放 🎵
  - **MeloTTS** - 中英文混合支持 🌐

- **👁️ 视觉理解**: Qwen-VL-Max 多模态理解
  - 屏幕内容分析
  - 支持窗口/全屏截图

- **💾 长期记忆**: 5分钟时间窗口的跨会话记忆持久化

### 🎨 技术亮点

#### 传统模式
- 📦 模块化架构，代码结构清晰
- 🎯 浏览器操作准确率可达 **95%+**
- 🔇 智能静音检测，说完即停
- 🛡️ 支持执行中断（可被新唤醒词打断）

#### Pipecat 模式（实验性）
- ⚡ **完全异步架构** - 基于 Pipecat 实时音频框架
- 🎯 **官方推荐模式** - 符合 MCP Python SDK 最佳实践
- 🔄 **Pipeline 流式处理** - KWS → ASR → Agent → TTS 流水线
- 🚀 **零线程开销** - 纯异步，无 `run_coroutine_threadsafe`
- 🛡️ **非阻塞执行** - Agent 后台运行，不阻塞音频处理
- ⏸️ **标准中断机制** - 使用 Pipecat 官方 `InterruptionFrame`
  - ✅ 生态兼容：可与官方 TTS/LLM Processor 配合
  - ✅ 统一协调：`allow_interruptions` 全局管理
  - ✅ 事件明确：`TTSStoppedFrame` 通知停止状态

---

## 📦 安装

### 1. 环境要求
- Python 3.12+
- Windows 10/11
- 麦克风设备
- Node.js 18+（用于 Playwright MCP）

### 2. 克隆项目
```bash
git clone https://github.com/yourusername/voice-assistant.git
cd .\src\voice_assistant\
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
```

---

## 🚀 使用

### 启动助手
```bash
python main.py
```

启动时会提示选择运行模式：
```
请选择运行模式：
  1. 传统模式 (原有架构)
  2. Pipecat 模式 (新架构，实验性)
请选择 (1/2，默认1):
```

### 模式说明

#### **传统模式** (推荐)
- ✅ 稳定可靠，经过充分测试
- ✅ 完整功能支持（Vision + MCP）
- ✅ 适合日常使用

#### **Pipecat 模式** (实验性)
- 🧪 基于 Pipecat 实时音频框架
- ⚡ 完全异步架构，性能更优
- 🔄 Pipeline 流式处理
- 📝 目前支持：KWS + ASR + Agent + TTS
- ⚠️ Vision 模式暂未集成

### 交互流程
1. **唤醒**: 说出唤醒词（如"小智"）
2. **指令**: 听到提示音后，说出指令
3. **执行**: 系统自动理解并执行操作

### 支持的指令示例

#### 🌐 浏览器导航
```
"打开 B 站"
"访问百度"
"浏览器后退"
"刷新页面"
```

#### 🖱️ 网页交互
```
"点击搜索框"
"点击登录按钮"
"在输入框输入测试文本"
```

#### 📸 屏幕截图
```
"截取当前页面"
"保存页面为PDF"
```

#### 👁️ 视觉理解（仅传统模式）
```
"看看浏览器窗口显示了什么"
"分析当前屏幕内容"
```

---

## 📁 项目结构

```
chinese-voice-assistant/
├── src/voice_assistant/      # 核心源代码
│   ├── __init__.py           # 模块导出 (30行)
│   ├── config.py             # 配置管理 (40行)
│   ├── wake_word.py          # 唤醒词系统 (352行)
│   ├── react_agent.py        # React 智能代理 (1040行)
│   │                         # - execute_command (同步，传统模式)
│   │                         # - execute_command_async (异步，Pipecat模式)
│   ├── mcp_client.py         # MCP 客户端 (578行)
│   │                         # - MCPManager (异步，多Server管理)
│   │                         # - MCPManagerSync (同步，传统模式封装)
│   ├── pipecat_main.py       # Pipecat 主程序 (323行)
│   ├── pipecat_adapters.py   # Pipecat Processors (356行)
│   │                         # - SherpaKWSProcessor (KWS)
│   │                         # - SherpaASRProcessor (ASR)
│   │                         # - ReactAgentProcessor (Agent)
│   │                         # - PiperTTSProcessor (TTS)
│   ├── tts.py                # TTS 语音合成 (666行)
│   └── vision.py             # 视觉理解 (72行)
│
├── scripts/                  # 工具脚本
│   ├── download_models.py    # 模型下载
│   └── pinyin_helper.py      # 拼音转换助手
│
├── tests/                    # 测试文件
│   └── test_phase1.py        # Pipecat 模式测试
│
├── config/                   # 配置文件
│   └── keywords.txt          # 唤醒词配置
│
├── models/                   # 模型文件（需下载）
│   ├── piper/                # Piper TTS 模型
│   ├── sherpa-onnx-kws-*/    # KWS 模型 (3.3MB)
│   └── sherpa-onnx-paraformer-zh/ # ASR 模型 (120MB)
│
├── main.py                   # 主程序入口
├── pyproject.toml            # 项目配置 (v2.0.0)
└── README.md                 # 项目文档
```

### 代码统计
| 模块 | 代码行数 | 主要功能 |
|-----|---------|---------|
| `react_agent.py` | 1040 | React 推理框架、同步+异步执行 |
| `tts.py` | 666 | TTS 引擎管理（Piper/RealtimeTTS/MeloTTS） |
| `mcp_client.py` | 578 | MCP 客户端、多 Server 管理 |
| `pipecat_adapters.py` | 356 | Pipecat Processors |
| `wake_word.py` | 352 | 双阶段识别（KWS + ASR） |
| `pipecat_main.py` | 323 | Pipecat Pipeline 配置 |
| `vision.py` | 72 | Qwen-VL-Max 视觉理解 |
| `config.py` | 40 | 全局配置 |
| **总计** | **3,457** | **完整功能实现** |

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

### 架构说明

#### **传统模式架构**
```
音频输入 → KWS → ASR → React Agent → MCP Tools → TTS → 音频输出
```

#### **Pipecat 模式架构**
```
Pipeline:
  SimplePyAudioTransport (音频I/O)
    ↓
  SherpaKWSProcessor (唤醒词检测)
    ↓
  SherpaASRProcessor (语音识别)
    ↓
  ReactAgentProcessor (智能代理，后台执行)
    ↓
  PiperTTSProcessor (语音合成，支持中断)
    ↓
  SimplePyAudioTransport (音频输出)
```

### 核心改进（Pipecat 模式）

#### **1. 完全异步架构**
```python
# React Agent 异步支持
async def execute_command_async(self, command: str) -> Dict:
    return await self._react_mode_async(command)

async def _execute_action_async(self, action: str, action_input: Dict):
    # 直接使用官方 SDK 方法
    result = await self.mcp.call_tool_async(action, action_input)
```

#### **2. ReactAgentProcessor 简化**
- **之前**: 185 行（线程 + 包装器 + `run_coroutine_threadsafe`）
- **现在**: 82 行（纯异步，-55% 代码）

```python
class ReactAgentProcessor(FrameProcessor):
    async def _execute_and_push_result(self, command: str, direction):
        # 直接异步调用，无需线程！
        result = await self.agent.execute_command_async(command)
```

#### **3. 符合 MCP 官方推荐**
```python
# mcp_client.py:122 - 底层使用官方 SDK
result = await self.session.call_tool(tool_name, args)  # ✅ 官方方法
```

### 添加新功能
1. **添加新的 Pipecat Processor**: 在 `pipecat_adapters.py` 中继承 `FrameProcessor`
2. **添加新的 MCP 工具**: 工具会自动路由到正确的 Server
3. **添加新的唤醒词**: 编辑 `config/keywords.txt`
4. **扩展 React Agent**: 在 `react_agent.py` 中添加新的推理逻辑

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
| **智能决策** | | |
| 推理框架 | React Agent | 多轮思考+行动 |
| LLM 模型 | Qwen-Plus | 意图理解+规划 |
| 长期记忆 | JSON 持久化 | 5分钟时间窗口 |
| **浏览器控制** | | |
| MCP 框架 | Model Context Protocol | 官方 Python SDK v1.25.0 |
| 浏览器自动化 | Playwright MCP | 跨浏览器支持 |
| **音频处理** | | |
| 实时框架 | Pipecat AI v0.0.98 | Frame/Pipeline/Processor |
| 音频I/O | PyAudio | 录音播放 |
| **视觉理解** | | |
| 多模态模型 | Qwen-VL-Max | 屏幕内容分析 |
| 截图工具 | PIL ImageGrab | 屏幕截图 |
| **其他** | | |
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

### Q: 传统模式和 Pipecat 模式有什么区别？
A:
- **传统模式**: 稳定可靠，完整功能（推荐日常使用）
- **Pipecat 模式**: 实验性，完全异步架构，性能更优，但 Vision 暂未集成

### Q: MCP 工具调用失败？
A:
- 确认已安装 Node.js（版本 18+）
- 检查 npx 命令是否可用：`npx --version`
- 手动测试 Playwright MCP：`npx @playwright/mcp@latest`
- 查看控制台错误信息

### Q: Pipecat 模式有什么优势？
A:
- ✅ 完全异步，无线程开销
- ✅ 符合 MCP Python SDK 官方最佳实践
- ✅ Pipeline 流式处理，更高效
- ✅ 代码简洁（减少 55% 复杂度）
- ✅ 非阻塞执行，响应更快

---

## ⚠️ 注意事项

1. **API 费用**: 使用阿里云 API（LLM、Vision）会产生费用
   - 推荐使用 Piper TTS（免费本地）
   - Playwright 操作本地执行，无 API 费用

2. **隐私安全**:
   - API Key 不要提交到公开仓库
   - 建议使用环境变量管理敏感信息
   - 本地模型（Piper、Sherpa-ONNX）无隐私风险

3. **系统兼容**:
   - Playwright 支持跨平台
   - Pipecat 模式目前在 Windows 上测试

4. **网络需求**:
   - **无需网络**: KWS、ASR、Piper TTS（完全离线）
   - **需要网络**: LLM 决策、Vision 理解
   - **首次需要**: Playwright MCP 安装

---

## 🔥 最近更新

### v2.0.0 - 架构升级版本（2025-12）

#### ✨ 新增特性
1. **Pipecat 框架集成** - 实时音频流处理
   - 完全异步 Pipeline 架构
   - KWS → ASR → Agent → TTS 流水线
   - 非阻塞执行，TTS 可中断

2. **Pipecat 官方中断机制** - 符合 Pipecat 最佳实践
   - 使用标准 `InterruptionFrame` 替代自定义帧
   - 配置 `allow_interruptions=True` 全局管理
   - 发出 `TTSStoppedFrame` 明确停止事件
   - 生态兼容：可与官方 TTS/LLM Processor 配合

3. **MCP 官方推荐模式重构**
   - 基于 MCP Python SDK v1.25.0 官方最佳实践
   - 移除所有线程和 `run_coroutine_threadsafe`
   - 纯异步调用 `await session.call_tool()`
   - ReactAgentProcessor 代码减少 55%

4. **双模式架构**
   - 传统模式：稳定可靠，完整功能
   - Pipecat 模式：实验性，完全异步

5. **Piper TTS 集成** - 本地超低延迟语音合成
   - 延迟降低至 100-200ms
   - 完全离线运行
   - 中文音色自然

6. **Playwright MCP 集成** - 浏览器自动化控制
   - 网页导航、元素交互、截图
   - 支持 Chrome/Firefox/Safari
   - 跨平台支持

7. **React Agent 框架** - 智能推理决策
   - 多轮思考+行动循环
   - 支持同步和异步执行
   - 自动错误纠正
   - 长期记忆支持

#### 🐛 Bug 修复
- 修复 Pipecat 模式 Agent 阻塞 Pipeline 问题
- 修复 MCP 事件循环冲突导致超时
- 添加 TTS 中断机制
- 支持后台任务取消

#### 📊 性能提升
- TTS 延迟从 500ms → 100ms（Piper）
- MCP 调用完全异步，无线程开销
- Pipeline 流式处理，不阻塞

#### 🔧 技术改进
- 符合 MCP Python SDK 官方推荐模式
- 符合 Pipecat 官方中断机制（InterruptionFrame + TTSStoppedFrame）
- 代码简化 55%（185行 → 82行）
- 完全异步架构，无自定义帧类型
- 生态兼容，可与官方 Processor 配合
- 易于维护和扩展

---

## 🙏 致谢

- [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) - 高性能语音识别框架
- [Playwright](https://playwright.dev/) - 强大的浏览器自动化工具
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 官方 Python SDK
- [Pipecat AI](https://github.com/pipecat-ai/pipecat) - 实时音频处理框架
- [Piper TTS](https://github.com/rhasspy/piper) - 快速本地文本转语音引擎
- [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS) - 流式语音合成库
- [阿里云 DashScope](https://dashscope.aliyun.com/) - 多模态 API 和 LLM 服务
- [Qwen](https://github.com/QwenLM/Qwen) - 强大的大语言模型和视觉模型

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️

</div>
