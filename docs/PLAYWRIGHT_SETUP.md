# Playwright MCP 集成说明

## 问题：Playwright 启动超时

如果看到 "playwright MCP Server 启动超时"，原因可能是：
1. Playwright 浏览器未安装
2. npx 下载 @playwright/mcp 包较慢

## 解决方案

### 方案1：手动安装 Playwright 浏览器（推荐）

运行安装脚本：
```bash
scripts\install_playwright.bat
```

或手动执行：
```bash
npx playwright install chromium
```

这会下载 Chromium 浏览器（约 300MB），只需执行一次。

### 方案2：仅使用 Windows-MCP（临时方案）

如果不需要浏览器自动化，可以暂时跳过 Playwright。系统会自动降级使用 Windows-MCP 的工具。

输出示例：
```
✅ 成功启动 1/2 个 MCP Server

  ✓ Windows-MCP: 11 个工具
  ⚠️ Playwright-MCP 未启动（浏览器操作将使用 Windows 工具）
  📊 总计: 11 个工具
```

### 方案3：增加启动时间（已自动增加到 120 秒）

当前配置：
- Windows-MCP: 60 秒超时
- Playwright-MCP: 120 秒超时

如果网络较慢，首次启动可能需要等待 2 分钟。

## 验证安装

安装完成后，测试 Playwright 是否可用：

```bash
npx @playwright/mcp@latest
```

如果成功启动（不报错），按 Ctrl+C 退出，然后重新运行 main.py。

## Playwright vs Windows-MCP 对比

| 特性 | Playwright-MCP | Windows-MCP |
|------|----------------|-------------|
| 浏览器操作 | ✅ 快速、精确 | ⚠️ 需要 Vision + 坐标 |
| DOM 访问 | ✅ | ❌ |
| 表单填写 | ✅ | ⚠️ |
| 桌面操作 | ❌ | ✅ |
| 安装复杂度 | 高（需要下载浏览器） | 低 |

**结论**：如果只做简单的桌面操作，可以暂时不安装 Playwright。如果需要频繁操作浏览器，强烈推荐安装。
