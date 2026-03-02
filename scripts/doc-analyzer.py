#!/usr/bin/env python3
"""Simple document analyzer using local LLM."""

import sys
import os

def analyze_file(filepath):
    """Read and summarize a file."""
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n{'='*60}")
    print(f"📄 文件：{filepath}")
    print(f"{'='*60}")
    print(f"字数：{len(content)} 字符")
    print(f"行数：{len(content.splitlines())} 行")
    print(f"\n📝 内容预览（前 500 字）：\n")
    print(content[:500])
    print("\n...")
    print(f"\n{'='*60}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python3 doc-analyzer.py <文件路径>")
        sys.exit(1)
    
    analyze_file(sys.argv[1])
