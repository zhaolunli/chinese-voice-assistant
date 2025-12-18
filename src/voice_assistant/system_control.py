"""Windows系统控制器"""
import subprocess
import time
import pyautogui
import pygetwindow as gw
from PIL import ImageGrab


class SystemController:
    """Windows系统控制器"""

    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()

    def smart_capture(self, target="full", save_path="screen.png"):
        """智能截图"""
        screenshot = None

        if target == "full":
            print("📸 截取整个屏幕...")
            screenshot = ImageGrab.grab()
        elif target == "browser":
            print("📸 查找并截取浏览器窗口...")
            browsers = ['Chrome', 'Firefox', 'Edge', 'Microsoft Edge']
            for browser in browsers:
                try:
                    windows = gw.getWindowsWithTitle(browser)
                    if windows:
                        w = windows[0]
                        if w.isMinimized:
                            w.restore()
                        w.activate()
                        time.sleep(0.2)
                        screenshot = ImageGrab.grab(bbox=(w.left, w.top, w.right, w.bottom))
                        break
                except:
                    continue
            if not screenshot:
                screenshot = ImageGrab.grab()
        elif target == "active":
            print("📸 截取当前激活窗口...")
            try:
                windows = gw.getAllWindows()
                for window in windows:
                    if window.isActive:
                        screenshot = ImageGrab.grab(bbox=(window.left, window.top, window.right, window.bottom))
                        break
            except:
                pass
            if not screenshot:
                screenshot = ImageGrab.grab()
        else:
            screenshot = ImageGrab.grab()

        if screenshot:
            screenshot.save(save_path)
            return save_path
        return None

    def open_browser(self, url=""):
        """打开浏览器"""
        if url:
            subprocess.Popen(f'start chrome {url}', shell=True)
        else:
            subprocess.Popen('start chrome', shell=True)
        print("✓ 已打开浏览器")

    def open_app(self, app_name):
        """打开应用"""
        app_map = {
            "记事本": "notepad.exe",
            "计算器": "calc.exe",
            "文件管理器": "explorer.exe",
        }
        cmd = app_map.get(app_name, f"{app_name}.exe")
        subprocess.Popen(cmd, shell=True)
        print(f"✓ 已打开 {app_name}")
