#!/usr/bin/env python3
"""
决策日志记录工具
用法：python3 log-decision.py "决策标题" "决策内容" "选择的原因"
"""

import json
import sys
import os
from datetime import datetime

WORKSPACE = "/root/.openclaw/workspace"
INDEX_FILE = f"{WORKSPACE}/life/decisions/index.json"
DECISIONS_DIR = f"{WORKSPACE}/life/decisions"

def create_decision(title: str, context: str, reason: str, options: list = None):
    """创建决策记录"""
    
    # 确保目录存在
    os.makedirs(DECISIONS_DIR, exist_ok=True)
    
    # 读取索引
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {"decisions": [], "stats": {}}
    
    # 生成决策 ID
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    decision_id = f"dec-{timestamp}"
    
    # 创建决策记录
    decision = {
        "id": decision_id,
        "title": title,
        "context": context,
        "options": options or [],
        "selected": 0,
        "reason": reason,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    
    # 保存决策文件
    decision_file = f"{DECISIONS_DIR}/{decision_id}.json"
    with open(decision_file, 'w', encoding='utf-8') as f:
        json.dump(decision, f, ensure_ascii=False, indent=2)
    
    # 更新索引
    index["decisions"].append({
        "id": decision_id,
        "title": title,
        "created_at": decision["created_at"]
    })
    index["stats"]["total"] = len(index["decisions"])
    index["stats"]["last_updated"] = datetime.now().isoformat()
    
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 决策已记录：{decision_id}")
    print(f"  标题：{title}")
    print(f"  原因：{reason}")
    return decision_id

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法：python3 log-decision.py \"标题\" \"上下文\" \"原因\"")
        print("示例：python3 log-decision.py \"选择记忆系统\" \"需要持久化记忆\" \"elite-longterm-memory 功能最全\"")
        sys.exit(1)
    
    title = sys.argv[1]
    context = sys.argv[2]
    reason = sys.argv[3]
    
    create_decision(title, context, reason)
