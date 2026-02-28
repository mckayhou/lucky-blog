#!/usr/bin/env python3
"""
周度模式提取器
分析过去 7 天的日志，提取主题、高频话题、行为模式
"""

import os
import re
from datetime import datetime, timedelta
from collections import Counter

WORKSPACE = "/root/.openclaw/workspace"
MEMORY_DIR = f"{WORKSPACE}/memory"
OUTPUT_DIR = f"{WORKSPACE}/life/projects/pattern-extraction"

def extract_patterns(days: int = 7):
    """提取最近 N 天的模式"""
    
    # 收集日志内容
    all_content = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    if os.path.exists(MEMORY_DIR):
        for filename in os.listdir(MEMORY_DIR):
            if filename.endswith('.md') and not filename.startswith('MEMORY-backup'):
                # 尝试从文件名解析日期
                try:
                    date_str = filename.replace('.md', '')
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if file_date >= cutoff_date:
                        with open(os.path.join(MEMORY_DIR, filename), 'r', encoding='utf-8') as f:
                            all_content.append(f.read())
                except:
                    pass
    
    if not all_content:
        print("没有找到最近的日志文件")
        return
    
    # 合并内容
    full_text = "\n".join(all_content)
    
    # 提取高频词（简化版）
    words = re.findall(r'[\u4e00-\u9fff]{2,}', full_text)  # 中文双字词
    word_counts = Counter(words).most_common(20)
    
    # 生成报告
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_file = f"{OUTPUT_DIR}/pattern-report-{datetime.now().strftime('%Y%m%d')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 周度模式提取报告\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"分析周期：过去 {days} 天\n\n")
        
        f.write("## 高频主题\n\n")
        for word, count in word_counts[:10]:
            f.write(f"- {word}: {count} 次\n")
        
        f.write("\n## 洞察\n\n")
        f.write("_需要 LLM 进一步分析语义和上下文_\n")
    
    print(f"✓ 模式报告已生成：{report_file}")
    return report_file

if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    extract_patterns(days)
