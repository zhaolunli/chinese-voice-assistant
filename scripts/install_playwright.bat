@echo off
echo ========================================
echo 安装 Playwright 浏览器
echo ========================================
echo.
echo 这将下载 Chromium 浏览器（约 300MB）
echo 只需执行一次
echo.
pause

echo.
echo 正在安装 Playwright...
npx playwright install chromium

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 现在可以运行 main.py 启动语音助手了
pause
