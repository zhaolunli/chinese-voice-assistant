"""测试各种截图方案的可靠性"""
import ctypes
from ctypes import wintypes
from PIL import ImageGrab
import tempfile
from pathlib import Path


def test_fullscreen_screenshot():
    """测试1: 全屏截图"""
    print("\n=== 测试1: 全屏截图 ===")
    try:
        screenshot = ImageGrab.grab()
        size = screenshot.size
        print(f"✅ 成功: {size[0]}x{size[1]} 像素")

        # 保存测试
        temp_path = Path(tempfile.gettempdir()) / "test_fullscreen.png"
        screenshot.save(temp_path)
        print(f"📁 已保存: {temp_path}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_window_screenshot_basic():
    """测试2: 基础窗口截图（可能有DPI问题）"""
    print("\n=== 测试2: 基础窗口截图 ===")
    try:
        # 获取前台窗口
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            print("❌ 无法获取前台窗口")
            return False

        # 获取窗口标题
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value
        print(f"📝 窗口标题: {title}")

        # 获取窗口矩形
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

        width = rect.right - rect.left
        height = rect.bottom - rect.top
        print(f"📐 窗口坐标: ({rect.left}, {rect.top}) -> ({rect.right}, {rect.bottom})")
        print(f"📏 窗口尺寸: {width}x{height}")

        # 截图
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        screenshot = ImageGrab.grab(bbox=bbox)
        size = screenshot.size
        print(f"📸 截图尺寸: {size[0]}x{size[1]}")

        # 保存测试
        temp_path = Path(tempfile.gettempdir()) / "test_window_basic.png"
        screenshot.save(temp_path)
        print(f"📁 已保存: {temp_path}")

        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_window_screenshot_dpi_aware():
    """测试3: DPI感知的窗口截图（更准确）"""
    print("\n=== 测试3: DPI感知窗口截图 ===")
    try:
        # 设置 DPI 感知
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            print("✅ DPI 感知已启用")
        except:
            print("⚠️ 无法启用 DPI 感知（可能已启用）")

        # 获取前台窗口
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            print("❌ 无法获取前台窗口")
            return False

        # 获取窗口矩形
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

        # 修正边框（可选）
        padding = 8
        bbox = (
            rect.left + padding,
            rect.top,
            rect.right - padding,
            rect.bottom - padding
        )

        print(f"📐 原始坐标: ({rect.left}, {rect.top}) -> ({rect.right}, {rect.bottom})")
        print(f"📐 修正坐标: {bbox}")

        # 截图
        screenshot = ImageGrab.grab(bbox=bbox)
        size = screenshot.size
        print(f"📸 截图尺寸: {size[0]}x{size[1]}")

        # 保存测试
        temp_path = Path(tempfile.gettempdir()) / "test_window_dpi.png"
        screenshot.save(temp_path)
        print(f"📁 已保存: {temp_path}")

        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_screenshots():
    """对比测试结果"""
    print("\n=== 对比分析 ===")
    temp_dir = Path(tempfile.gettempdir())

    files = {
        "全屏": temp_dir / "test_fullscreen.png",
        "基础窗口": temp_dir / "test_window_basic.png",
        "DPI感知": temp_dir / "test_window_dpi.png"
    }

    for name, path in files.items():
        if path.exists():
            from PIL import Image
            img = Image.open(path)
            size = img.size
            file_size = path.stat().st_size / 1024  # KB
            print(f"{name:8} - {size[0]:4}x{size[1]:4} 像素, {file_size:6.1f} KB, {path}")


if __name__ == "__main__":
    print("🧪 截图方案可靠性测试")
    print("=" * 60)
    print("请确保有一个窗口处于前台（如浏览器）")
    print("=" * 60)

    results = []
    results.append(("全屏截图", test_fullscreen_screenshot()))
    results.append(("基础窗口截图", test_window_screenshot_basic()))
    results.append(("DPI感知截图", test_window_screenshot_dpi_aware()))

    compare_screenshots()

    print("\n=== 测试结果汇总 ===")
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:12} - {status}")

    print("\n💡 建议:")
    print("1. 打开保存的图片，检查截图是否准确")
    print("2. 对比三张图片的内容范围")
    print("3. 检查是否有边框、阴影被包含")
    print("4. 如果 DPI 感知失败，可以使用基础窗口截图")
