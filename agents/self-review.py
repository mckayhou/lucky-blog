#!/usr/bin/env python3
"""
Self-Review 自动执行脚本
任务结束后自动分析、更新 AGENTS.md、输出 vNext 建议
"""

import json
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
AGENTS_DIR = WORKSPACE / "agents"
MEMORY_DIR = WORKSPACE / "memory"

def self_review(agent_name: str, task: str, result: str, metrics: dict = None):
    """执行 Self-Review"""
    
    timestamp = datetime.now().isoformat()
    
    # 1. 目标 vs 结果对比
    review = {
        "agent": agent_name,
        "task": task,
        "timestamp": timestamp,
        "metrics": metrics or {},
        "optimization_points": [],
        "vnext_suggestions": []
    }
    
    # 2. 识别优化点（简化版，实际可用 LLM 分析）
    if metrics:
        if metrics.get("duration_minutes", 0) > 10:
            review["optimization_points"].append("耗时较长，可优化执行路径")
        if metrics.get("success", True) == False:
            review["optimization_points"].append("任务失败，需分析原因")
    
    # 3. 生成 vNext 建议
    review["vnext_suggestions"].append("持续积累任务经验，优化响应策略")
    
    # 4. 保存到 review 日志
    review_file = AGENTS_DIR / f"{agent_name}-reviews.jsonl"
    with open(review_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(review, ensure_ascii=False) + '\n')
    
    # 5. 更新 AGENTS.md（简化版）
    agents_md = AGENTS_DIR / "AGENTS.md"
    if agents_md.exists():
        content = agents_md.read_text(encoding='utf-8')
        # 添加 review 记录
        review_entry = f"\n## {timestamp}\n- Agent: {agent_name}\n- Task: {task}\n- Status: {'✅' if metrics.get('success', True) else '❌'}\n"
        content += review_entry
        agents_md.write_text(content, encoding='utf-8')
    
    # 6. 输出 Self-Review 报告
    print(f"【Self-Review】{agent_name}")
    print(f"任务：{task}")
    print(f"时间：{timestamp}")
    if metrics:
        print(f"耗时：{metrics.get('duration_minutes', 'N/A')} 分钟")
        print(f"状态：{'✅ 成功' if metrics.get('success', True) else '❌ 失败'}")
    if review["optimization_points"]:
        print(f"优化点：{review['optimization_points']}")
    print(f"vNext: {review['vnext_suggestions'][0]}")
    
    return review

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：python3 self-review.py <agent_name> <task_description> [metrics_json]")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    task = sys.argv[2]
    metrics = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    
    self_review(agent_name, task, "", metrics)
