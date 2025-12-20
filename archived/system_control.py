"""Windows系统控制器 - 基于 pywinauto"""
import re
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple, List
from PIL import Image, ImageGrab
from pywinauto import Application, Desktop
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError as PywinautoTimeoutError


# ==================== 异常类 ====================

class SystemControlError(Exception):
    """系统控制基础异常"""
    pass


class WindowNotFoundError(SystemControlError):
    """窗口未找到"""
    pass


class LaunchTimeoutError(SystemControlError):
    """启动超时"""
    pass


class CaptureError(SystemControlError):
    """截图失败"""
    pass


# ==================== 配置常量 ====================

# 后端偏好配置
BACKEND_PREFERENCES = {
    "chrome": "uia",
    "edge": "uia",
    "firefox": "uia",
    "notepad": "win32",
    "calculator": "uia",
    "explorer": "uia"
}

# 应用配置
APP_CONFIGS = {
    "notepad": {
        "path": "notepad.exe",
        "title_pattern": r".*记事本.*|.*Notepad.*",
        "verify_timeout": 3,
        "backend": "win32"
    },
    "calculator": {
        "path": "calc.exe",
        "title_pattern": r".*计算器.*|.*Calculator.*",
        "verify_timeout": 3,
        "backend": "uia"
    },
    "chrome": {
        "path": "chrome.exe",
        "title_pattern": r".*Chrome.*",
        "verify_timeout": 5,
        "backend": "uia"
    },
    "edge": {
        "path": "msedge.exe",
        "title_pattern": r".*Edge.*",
        "verify_timeout": 5,
        "backend": "uia"
    },
    "firefox": {
        "path": "firefox.exe",
        "title_pattern": r".*Firefox.*",
        "verify_timeout": 5,
        "backend": "uia"
    },
    "explorer": {
        "path": "explorer.exe",
        "title_pattern": r".*文件资源管理器.*|.*File Explorer.*|.*资源管理器.*",
        "verify_timeout": 3,
        "backend": "uia"
    }
}


# ==================== WindowManager 类 ====================

class WindowManager:
    """窗口管理器 - 负责查找、激活、管理窗口"""

    def __init__(self, backend: str = "uia"):
        """
        Args:
            backend: "win32" 或 "uia"
                - "win32": 适用于 MFC, VB6, VCL, WinForms 老应用
                - "uia": 适用于 WPF, Chrome, Firefox, Edge 等现代应用
        """
        self.backend = backend
        self.desktop = Desktop(backend=backend)
        self._app_cache: Dict[int, Application] = {}
        self.logger = logging.getLogger(__name__)

    def find_window_by_title(self, title_pattern: str, exact: bool = False) -> Optional[object]:
        """
        按标题查找窗口

        Args:
            title_pattern: 窗口标题模式（支持正则）
            exact: 是否精确匹配

        Returns:
            窗口对象或None
        """
        try:
            windows = self.desktop.windows()
            for window in windows:
                try:
                    title = window.window_text()
                    if exact:
                        if title == title_pattern:
                            return window
                    else:
                        if re.search(title_pattern, title, re.IGNORECASE):
                            return window
                except Exception:
                    continue
            return None
        except Exception as e:
            self.logger.error(f"查找窗口失败: {e}")
            return None

    def find_window_by_class(self, class_name: str) -> Optional[object]:
        """按窗口类名查找"""
        try:
            windows = self.desktop.windows()
            for window in windows:
                try:
                    if window.class_name() == class_name:
                        return window
                except Exception:
                    continue
            return None
        except Exception as e:
            self.logger.error(f"按类名查找窗口失败: {e}")
            return None

    def activate_window(self, window) -> bool:
        """
        激活窗口（最小化恢复、置顶）

        Args:
            window: pywinauto 窗口对象

        Returns:
            是否成功
        """
        try:
            # 检查窗口是否可见
            if not window.is_visible():
                window.restore()
                time.sleep(0.2)

            # 激活窗口
            window.set_focus()
            time.sleep(0.1)
            return True
        except Exception as e:
            self.logger.error(f"激活窗口失败: {e}")
            return False

    def get_active_window(self) -> Optional[object]:
        """获取当前激活窗口"""
        try:
            # 使用 Desktop.get_active() 获取激活窗口
            from pywinauto import Desktop as DesktopClass
            active = DesktopClass(backend=self.backend).get_active()
            return active
        except Exception as e:
            self.logger.error(f"获取激活窗口失败: {e}")
            return None

    def wait_for_window(self, title_pattern: str, timeout: int = 5) -> Optional[object]:
        """
        等待窗口出现

        Args:
            title_pattern: 窗口标题模式
            timeout: 超时时间（秒）

        Returns:
            窗口对象或None
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            window = self.find_window_by_title(title_pattern)
            if window:
                return window
            time.sleep(0.5)

        self.logger.warning(f"等待窗口超时: {title_pattern}")
        return None


# ==================== ApplicationLauncher 类 ====================

class ApplicationLauncher:
    """应用启动器 - 负责启动并验证应用"""

    def __init__(self, window_manager: WindowManager):
        self.wm = window_manager
        self.logger = logging.getLogger(__name__)
        self.app_configs = APP_CONFIGS

    def launch_app(self, app_key: str, **kwargs) -> Tuple[Optional[Application], Optional[object]]:
        """
        启动应用并返回 Application 和窗口对象

        Args:
            app_key: 应用键名（如 "notepad", "calculator"）
            **kwargs: 额外参数

        Returns:
            (Application, Window) tuple 或 (None, None)
        """
        config = self.app_configs.get(app_key)
        if not config:
            self.logger.error(f"未知应用: {app_key}")
            return None, None

        try:
            # 1. 选择后端
            backend = config.get("backend", "uia")

            # 2. 启动应用
            self.logger.info(f"启动应用: {config['path']}")
            app = Application(backend=backend).start(
                config["path"],
                timeout=10
            )

            # 3. 等待窗口出现
            window = self.wm.wait_for_window(
                title_pattern=config["title_pattern"],
                timeout=config["verify_timeout"]
            )

            if window:
                # 4. 激活窗口
                self.wm.activate_window(window)
                self.logger.info(f"✓ 成功启动应用: {app_key}")
                return app, window
            else:
                raise LaunchTimeoutError(f"应用窗口未出现: {app_key}")

        except Exception as e:
            self.logger.error(f"✗ 启动应用失败 {app_key}: {e}")
            return None, None

    def launch_browser(self, browser: str = "chrome", url: str = "") -> Tuple[Optional[Application], Optional[object]]:
        """
        启动浏览器（特殊处理）

        Args:
            browser: 浏览器名称
            url: 可选URL

        Returns:
            (Application, Window) tuple 或 (None, None)
        """
        # 浏览器完整路径配置
        browser_paths = {
            "chrome": [
                "chrome.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
            "edge": [
                "msedge.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
            "firefox": [
                "firefox.exe",
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ]
        }

        # 浏览器优先级
        browser_priority = ["chrome", "edge", "firefox"]
        if browser in browser_priority:
            browser_priority.remove(browser)
            browser_priority.insert(0, browser)

        for browser_name in browser_priority:
            config = self.app_configs.get(browser_name)
            if not config:
                continue

            # 获取可能的路径列表
            possible_paths = browser_paths.get(browser_name, [config["path"]])

            for exe_path in possible_paths:
                try:
                    backend = config.get("backend", "uia")

                    # 1. 先尝试连接已运行的浏览器
                    try:
                        self.logger.info(f"尝试连接已运行的 {browser_name}...")
                        app = Application(backend=backend).connect(path=exe_path, timeout=2)
                        window = self.wm.find_window_by_title(config["title_pattern"])
                        if window:
                            self.wm.activate_window(window)
                            self.logger.info(f"✓ 已连接到运行中的浏览器: {browser_name}")
                            return app, window
                    except Exception:
                        pass  # 连接失败，继续尝试启动

                    # 2. 启动新浏览器
                    cmd = f'"{exe_path}" {url}' if url else f'"{exe_path}"'
                    self.logger.info(f"尝试启动浏览器: {browser_name} ({exe_path})")

                    app = Application(backend=backend).start(cmd, timeout=10)

                    # 3. 等待窗口
                    window = self.wm.wait_for_window(
                        title_pattern=config["title_pattern"],
                        timeout=config["verify_timeout"]
                    )

                    if window:
                        self.wm.activate_window(window)
                        self.logger.info(f"✓ 成功启动浏览器: {browser_name}")
                        return app, window
                    else:
                        self.logger.warning(f"浏览器 {browser_name} 已启动但窗口未出现")

                except Exception as e:
                    self.logger.debug(f"路径 {exe_path} 失败: {e}")
                    continue

            self.logger.warning(f"浏览器 {browser_name} 所有路径均失败")

        self.logger.error("✗ 未找到可用浏览器")
        return None, None


# ==================== ScreenCapturer 类 ====================

class ScreenCapturer:
    """屏幕截图器 - 负责智能截图"""

    def __init__(self, window_manager: WindowManager):
        self.wm = window_manager
        self.logger = logging.getLogger(__name__)

    def capture_full_screen(self, save_path: Path) -> Optional[Path]:
        """
        全屏截图

        Args:
            save_path: 保存路径

        Returns:
            保存路径或None
        """
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(save_path)
            self.logger.info(f"✓ 全屏截图保存: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"全屏截图失败: {e}")
            return None

    def capture_window(self, window, save_path: Path) -> Optional[Path]:
        """
        捕获指定窗口

        Args:
            window: pywinauto 窗口对象
            save_path: 保存路径

        Returns:
            保存路径或None
        """
        try:
            # 方法1：尝试使用 pywinauto 的 capture_as_image()
            try:
                img = window.capture_as_image()
                img.save(save_path)
                self.logger.info(f"✓ 窗口截图保存: {save_path}")
                return save_path
            except Exception:
                # 方法2：使用 bbox + PIL.ImageGrab
                rect = window.rectangle()
                screenshot = ImageGrab.grab(bbox=(
                    rect.left, rect.top, rect.right, rect.bottom
                ))
                screenshot.save(save_path)
                self.logger.info(f"✓ 窗口截图保存（bbox方式）: {save_path}")
                return save_path

        except Exception as e:
            self.logger.error(f"窗口截图失败: {e}")
            return None

    def capture_active_window(self, save_path: Path) -> Optional[Path]:
        """
        捕获当前激活窗口

        Args:
            save_path: 保存路径

        Returns:
            保存路径或None
        """
        try:
            # 获取激活窗口
            active_window = self.wm.get_active_window()

            if not active_window or not active_window.is_visible():
                raise CaptureError("无法获取激活窗口")

            # 截图
            result = self.capture_window(active_window, save_path)
            if result:
                self.logger.info(f"✓ 截取激活窗口: {active_window.window_text()}")
                return result
            else:
                # 降级到全屏
                self.logger.warning("激活窗口截图失败，使用全屏")
                return self.capture_full_screen(save_path)

        except Exception as e:
            self.logger.error(f"截取激活窗口失败: {e}")
            return self.capture_full_screen(save_path)

    def capture_browser(self, save_path: Path) -> Optional[Path]:
        """
        智能捕获浏览器窗口

        策略：按优先级搜索 Chrome -> Edge -> Firefox

        Args:
            save_path: 保存路径

        Returns:
            保存路径或None
        """
        browser_patterns = [
            ("Chrome", r".*Chrome.*"),
            ("Edge", r".*Edge.*"),
            ("Firefox", r".*Firefox.*")
        ]

        for browser_name, title_pattern in browser_patterns:
            try:
                self.logger.info(f"查找浏览器: {browser_name}")
                window = self.wm.find_window_by_title(title_pattern)

                if window:
                    # 激活窗口
                    self.wm.activate_window(window)
                    time.sleep(0.3)  # 等待窗口渲染

                    # 截图
                    result = self.capture_window(window, save_path)
                    if result:
                        self.logger.info(f"✓ 截取浏览器窗口: {browser_name}")
                        return result

            except Exception as e:
                self.logger.debug(f"浏览器 {browser_name} 截图失败: {e}")
                continue

        # 降级：全屏截图
        self.logger.warning("未找到浏览器窗口，使用全屏截图")
        return self.capture_full_screen(save_path)


# ==================== UIAutomator 类 ====================

class UIAutomator:
    """UI 自动化器 - 负责交互操作"""

    def __init__(self, window_manager: WindowManager):
        self.wm = window_manager
        self.logger = logging.getLogger(__name__)

    def type_text(self, window, text: str, set_focus: bool = True) -> bool:
        """
        输入文本到窗口

        Args:
            window: 目标窗口
            text: 要输入的文本
            set_focus: 是否先设置焦点

        Returns:
            是否成功
        """
        try:
            if set_focus:
                self.wm.activate_window(window)
                time.sleep(0.2)

            # 使用 pywinauto 的 type_keys
            window.type_keys(text, with_spaces=True)
            self.logger.info(f"✓ 成功输入文本: {text[:20]}...")
            return True
        except Exception as e:
            self.logger.error(f"输入文本失败: {e}")
            return False

    def click_button(self, window, button_name: str) -> bool:
        """
        点击窗口中的按钮

        Args:
            window: 目标窗口
            button_name: 按钮名称

        Returns:
            是否成功
        """
        try:
            # 查找按钮控件
            button = window.child_window(title=button_name, control_type="Button")
            button.click()
            self.logger.info(f"✓ 成功点击按钮: {button_name}")
            return True
        except Exception as e:
            self.logger.error(f"点击按钮失败 {button_name}: {e}")
            return False

    def send_keys(self, window, keys: str) -> bool:
        """
        发送快捷键

        Args:
            window: 目标窗口
            keys: 快捷键字符串（如 "^c" 表示 Ctrl+C）

        Returns:
            是否成功
        """
        try:
            self.wm.activate_window(window)
            time.sleep(0.1)
            window.type_keys(keys)
            self.logger.info(f"✓ 成功发送快捷键: {keys}")
            return True
        except Exception as e:
            self.logger.error(f"发送快捷键失败: {e}")
            return False

    def click_coordinates(self, window, x: int, y: int) -> bool:
        """
        点击窗口中的指定坐标

        Args:
            window: 目标窗口
            x: X 坐标（相对窗口）
            y: Y 坐标（相对窗口）

        Returns:
            是否成功
        """
        try:
            window.click_input(coords=(x, y))
            self.logger.info(f"✓ 成功点击坐标: ({x}, {y})")
            return True
        except Exception as e:
            self.logger.error(f"点击坐标失败: {e}")
            return False

    def browser_navigate(self, url: str) -> bool:
        """
        在浏览器中导航到URL（使用快捷键）

        策略：
        1. 查找浏览器窗口
        2. Ctrl+L 聚焦地址栏
        3. 输入URL
        4. 按 Enter

        Args:
            url: 目标URL

        Returns:
            是否成功
        """
        try:
            # 查找浏览器窗口
            browser_patterns = [r".*Chrome.*", r".*Edge.*", r".*Firefox.*"]
            window = None
            for pattern in browser_patterns:
                window = self.wm.find_window_by_title(pattern)
                if window:
                    break

            if not window:
                self.logger.error("未找到浏览器窗口")
                return False

            # 激活窗口
            self.wm.activate_window(window)
            time.sleep(0.3)

            # Ctrl+L 聚焦地址栏
            window.type_keys("^l")
            time.sleep(0.2)

            # 输入URL
            window.type_keys(url, with_spaces=True)
            time.sleep(0.1)

            # 按 Enter
            window.type_keys("{ENTER}")

            self.logger.info(f"✓ 成功导航到: {url}")
            return True

        except Exception as e:
            self.logger.error(f"浏览器导航失败: {e}")
            return False

    def browser_search(self, query: str) -> bool:
        """
        在浏览器中搜索（使用快捷键）

        策略：
        1. 查找浏览器窗口
        2. Ctrl+L 聚焦地址栏
        3. 输入搜索词
        4. 按 Enter

        Args:
            query: 搜索词

        Returns:
            是否成功
        """
        return self.browser_navigate(query)


# ==================== SystemController 类 ====================

class SystemController:
    """Windows 系统控制器 - 统一接口"""

    def __init__(self, backend: str = "uia"):
        """
        Args:
            backend: 默认后端（"uia" 或 "win32"）
        """
        self.window_manager = WindowManager(backend=backend)
        self.launcher = ApplicationLauncher(self.window_manager)
        self.capturer = ScreenCapturer(self.window_manager)
        self.automator = UIAutomator(self.window_manager)
        self.logger = logging.getLogger(__name__)

        # 日志配置
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)  # 启用详细日志

    # ==================== 核心方法（保持 API 兼容）====================

    def open_browser(self, url: str = "") -> bool:
        """
        打开浏览器

        Args:
            url: 可选URL

        Returns:
            是否成功
        """
        app, window = self.launcher.launch_browser(url=url)
        return window is not None

    def open_app(self, app_name: str) -> bool:
        """
        打开应用

        Args:
            app_name: 应用名称（中文或英文键名）

        Returns:
            是否成功
        """
        # 中文名称映射
        app_map = {
            "记事本": "notepad",
            "计算器": "calculator",
            "文件管理器": "explorer",
            "浏览器": "chrome",
        }

        app_key = app_map.get(app_name, app_name.lower())

        # 特殊处理：浏览器
        if app_key in ["chrome", "edge", "firefox"]:
            return self.open_browser()

        app, window = self.launcher.launch_app(app_key)
        return window is not None

    def smart_capture(self, target: str = "full", save_path: str = "screen.png") -> Optional[str]:
        """
        智能截图

        Args:
            target: 截图目标（"full", "browser", "active"）
            save_path: 保存路径

        Returns:
            保存路径或None
        """
        save_path_obj = Path(save_path)

        try:
            if target == "full":
                result = self.capturer.capture_full_screen(save_path_obj)
            elif target == "browser":
                result = self.capturer.capture_browser(save_path_obj)
            elif target == "active":
                result = self.capturer.capture_active_window(save_path_obj)
            else:
                self.logger.warning(f"未知截图目标: {target}，使用全屏")
                result = self.capturer.capture_full_screen(save_path_obj)

            return str(result) if result else None

        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return None

    # ==================== 新增功能 ====================

    def maximize_window(self, title_pattern: str) -> bool:
        """最大化窗口"""
        window = self.window_manager.find_window_by_title(title_pattern)
        if window:
            try:
                window.maximize()
                self.logger.info(f"✓ 窗口已最大化: {title_pattern}")
                return True
            except Exception as e:
                self.logger.error(f"最大化窗口失败: {e}")
        return False

    def minimize_window(self, title_pattern: str) -> bool:
        """最小化窗口"""
        window = self.window_manager.find_window_by_title(title_pattern)
        if window:
            try:
                window.minimize()
                self.logger.info(f"✓ 窗口已最小化: {title_pattern}")
                return True
            except Exception as e:
                self.logger.error(f"最小化窗口失败: {e}")
        return False

    def close_window(self, title_pattern: str) -> bool:
        """关闭窗口"""
        window = self.window_manager.find_window_by_title(title_pattern)
        if window:
            try:
                window.close()
                self.logger.info(f"✓ 窗口已关闭: {title_pattern}")
                return True
            except Exception as e:
                self.logger.error(f"关闭窗口失败: {e}")
        return False

    def browser_navigate(self, url: str) -> bool:
        """
        在浏览器中导航到URL

        Args:
            url: 目标URL或搜索词

        Returns:
            是否成功
        """
        return self.automator.browser_navigate(url)

    def browser_search(self, query: str) -> bool:
        """
        在浏览器中搜索

        Args:
            query: 搜索词

        Returns:
            是否成功
        """
        return self.automator.browser_search(query)

    def input_text(self, target_window: str, text: str) -> bool:
        """
        向指定窗口输入文本

        Args:
            target_window: 窗口标题模式
            text: 要输入的文本

        Returns:
            是否成功
        """
        window = self.window_manager.find_window_by_title(target_window)
        if not window:
            self.logger.error(f"未找到窗口: {target_window}")
            return False

        return self.automator.type_text(window, text)

    def click_ui_element(self, target_window: str, element_name: str) -> bool:
        """
        点击窗口中的 UI 元素

        Args:
            target_window: 窗口标题模式
            element_name: 元素名称

        Returns:
            是否成功
        """
        window = self.window_manager.find_window_by_title(target_window)
        if not window:
            self.logger.error(f"未找到窗口: {target_window}")
            return False

        return self.automator.click_button(window, element_name)

    def is_app_running(self, app_name: str) -> bool:
        """
        检查应用是否在运行

        Args:
            app_name: 应用名称

        Returns:
            是否在运行
        """
        app_map = {
            "记事本": "notepad",
            "计算器": "calculator",
            "文件管理器": "explorer",
        }

        app_key = app_map.get(app_name, app_name.lower())
        config = self.launcher.app_configs.get(app_key)

        if not config:
            return False

        window = self.window_manager.find_window_by_title(config["title_pattern"])
        return window is not None

    def get_window_info(self, title_pattern: str) -> Optional[Dict]:
        """
        获取窗口信息

        Args:
            title_pattern: 窗口标题模式

        Returns:
            窗口信息字典或None
        """
        window = self.window_manager.find_window_by_title(title_pattern)
        if not window:
            return None

        try:
            rect = window.rectangle()
            return {
                "title": window.window_text(),
                "visible": window.is_visible(),
                "enabled": window.is_enabled(),
                "position": (rect.left, rect.top),
                "size": (rect.width(), rect.height())
            }
        except Exception as e:
            self.logger.error(f"获取窗口信息失败: {e}")
            return None
