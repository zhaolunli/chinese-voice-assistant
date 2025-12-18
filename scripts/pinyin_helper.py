#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼音转换工具 - 用于生成唤醒词文件
将中文转换为sherpa-onnx所需的拼音格式
"""

# 简单的拼音映射表（示例）
PINYIN_MAP = {
    '小': 'x iǎo',
    '智': 'zh ì',
    '你': 'n ǐ',
    '好': 'h ǎo',
    '助': 'zh ù',
    '手': 'sh ǒu',
    '智': 'zh ì',
    '能': 'n éng',
    '爱': 'ài',
    '同': 't óng',
    '学': 'x ué',
    '天': 't iān',
    '猫': 'm āo',
    '精': 'j īng',
    '灵': 'l íng',
}

def chinese_to_pinyin(text):
    """
    将中文转换为拼音格式（简单实现）
    实际使用建议用 pypinyin 库
    """
    result = []
    for char in text:
        if char in PINYIN_MAP:
            result.append(PINYIN_MAP[char])
        else:
            result.append(f"[{char}]")
    return ' '.join(result)

def generate_keyword_line(chinese_text):
    """生成关键词文件的一行"""
    pinyin = chinese_to_pinyin(chinese_text)
    return f"{pinyin} @{chinese_text}"

if __name__ == "__main__":
    print("=" * 60)
    print("唤醒词拼音转换工具")
    print("=" * 60)
    print("\n提示：建议安装 pypinyin 库以获得完整拼音支持")
    print("  pip install pypinyin\n")

    print("请输入唤醒词（输入q退出）：")

    while True:
        text = input("> ").strip()
        if text.lower() == 'q':
            break
        if not text:
            continue

        line = generate_keyword_line(text)
        print(f"格式化结果: {line}\n")

        # 检查是否有未知字符
        if '[' in line:
            print("⚠️  包含未映射的字符，建议使用 pypinyin 库或参考模型自带示例")

print("\n使用示例（使用pypinyin）：")
print("""
from pypinyin import lazy_pinyin, Style

def text_to_keyword(text):
    pinyin_list = lazy_pinyin(text, style=Style.TONE3)
    # 转换声调数字为符号
    pinyin = ' '.join(pinyin_list)
    return f"{pinyin} @{text}"

# 使用
print(text_to_keyword("小爱同学"))
""")
