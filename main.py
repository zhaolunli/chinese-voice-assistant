#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能语音助手 - 主程序入口
"""
from src.voice_assistant import SmartWakeWordSystem


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 智能语音助手 - 双阶段识别版")
    print("功能: KWS关键词唤醒 + ASR语音识别 + 视觉理解 + 系统控制")
    print("=" * 60)

    print("\n是否开启语音播报？")
    print("  1. 是（推荐）")
    print("  2. 否")
    choice = input("请选择 (1/2，默认1): ").strip() or "1"
    enable_voice = (choice == "1")

    try:
        system = SmartWakeWordSystem(enable_voice=enable_voice)
        system.start_listening()
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
