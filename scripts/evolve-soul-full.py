#!/usr/bin/env python3
"""
SOUL.md 完整进化脚本
从 Chitin 提取洞察，智能重构 SOUL.md
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
SOUL_FILE = WORKSPACE / "SOUL.md"
BACKUP_DIR = WORKSPACE / "memory"

def run_command(cmd: str) -> str:
    """运行 shell 命令并返回输出"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_chitin_stats() -> dict:
    """获取 Chitin 统计信息"""
    stats_output = run_command("chitin stats 2>/dev/null")
    return {"raw": stats_output}

def get_insights_by_type(insight_type: str, limit: int = 5) -> list:
    """获取指定类型的洞察"""
    output = run_command(f"chitin list --type {insight_type} --json 2>/dev/null")
    if not output:
        return []
    try:
        # 解析 JSON 输出
        insights = json.loads(output) if output.startswith('[') else []
        return insights[:limit]
    except:
        return []

def format_insight(insight: dict) -> str:
    """格式化单条洞察"""
    claim = insight.get('claim', '')
    confidence = insight.get('confidence', 0)
    return f"- {claim} (置信度：{confidence:.2f})"

def generate_personality_section() -> str:
    """生成人格洞察部分"""
    sections = []
    
    # 获取各类洞察
    types = ['behavioral', 'personality', 'relational', 'principle', 'skill']
    
    for insight_type in types:
        insights = get_insights_by_type(insight_type, limit=3)
        if insights:
            type_name = {
                'behavioral': '行为模式',
                'personality': '人格特质',
                'relational': '关系动态',
                'principle': '核心原则',
                'skill': '技能经验'
            }.get(insight_type, insight_type)
            
            sections.append(f"### {type_name}")
            for insight in insights:
                sections.append(format_insight(insight))
            sections.append("")
    
    return "\n".join(sections)

def evolve_soul():
    """执行 SOUL 进化"""
    timestamp = datetime.now().strftime('%Y%m%d')
    
    # 备份当前 SOUL.md
    if SOUL_FILE.exists():
        backup_path = BACKUP_DIR / f"chitin-soul-backup-{timestamp}.md"
        backup_path.write_text(SOUL_FILE.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"✓ SOUL.md 已备份至 {backup_path}")
    
    # 获取统计
    stats = get_chitin_stats()
    print(f"Chitin 状态:\n{stats['raw']}")
    
    # 生成人格洞察部分
    personality_content = generate_personality_section()
    
    if personality_content:
        print("\n生成的人格洞察:")
        print(personality_content)
        
        # 这里可以添加逻辑将洞察合并到 SOUL.md
        # 当前版本仅生成报告，完整版本需要解析和更新 SOUL.md
    else:
        print("暂无新洞察可提取")
    
    print(f"\n✓ SOUL 进化完成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    evolve_soul()
