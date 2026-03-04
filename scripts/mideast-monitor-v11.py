#!/usr/bin/env python3
"""
中东战争监控脚本 v11 - Delta 每小时版
- 频率：每 1 小时
- 范围：严格过去 60 分钟新事件
- 状态管理：war_last_run.json
"""

import subprocess
import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Tavily API Key
TAVILY_API_KEY = "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"

# 搜索关键词（强调最新）
SEARCH_QUERIES = [
    "Iran Israel war past hour last 60 minutes",
    "Lebanon Hezbollah attack today latest",
    "Middle East conflict updates last hour",
]

# X OSINT 账号
OSINT_ACCOUNTS = ["@sentdefender", "@Osint613", "@OSINTWarfare"]

# 状态文件
STATE_FILE = Path("/root/.openclaw/workspace/state/war_last_run.json")
OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_state():
    """读取上次运行时间"""
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['last_run'].replace('Z', '')).replace(tzinfo=None)
    except:
        return datetime.utcnow() - timedelta(hours=1)

def save_state():
    """保存当前运行时间"""
    with open(STATE_FILE, 'w') as f:
        json.dump({"last_run": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}, f)

def tavily_search(query):
    """Tavily 搜索"""
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "topic": "news",
            "search_depth": "advanced",
            "max_results": 10,
        }
        resp = requests.post(url, json=payload, timeout=30)
        return resp.json().get('results', [])
    except Exception as e:
        print(f"Tavily 失败 {query}: {e}")
        return []

def parse_event_time(text):
    """从文本提取事件时间"""
    now = datetime.utcnow()
    
    # 检查是否包含"分钟"
    min_match = re.search(r'(\d+)\s*(分钟|minutes|min)\s*(前|ago)', text, re.IGNORECASE)
    if min_match:
        mins = int(min_match.group(1))
        return now - timedelta(minutes=mins)
    
    # 检查"小时"
    hour_match = re.search(r'(\d+)\s*(小时|hours|hr)\s*(前|ago)', text, re.IGNORECASE)
    if hour_match:
        hrs = int(hour_match.group(1))
        return now - timedelta(hours=hrs)
    
    # 检查"今天"
    if '今天' in text or 'today' in text.lower():
        return now
    
    # 默认返回 now（假设是最新）
    return now

def is_new_event(r, last_run):
    """判断是否为 60 分钟内的新事件"""
    title = r.get('title', '') + ' ' + r.get('content', '')
    event_time = parse_event_time(title)
    
    # 简单判断：如果包含"past hour", "last 60 minutes", "今天", "today"等
    time_keywords = ['past hour', 'last 60 minutes', '今天', 'today', '刚刚', 'just now', 'breaking']
    has_recent_keyword = any(kw in title.lower() for kw in time_keywords)
    
    return has_recent_keyword or event_time > last_run

def generate_delta_report(results, last_run):
    """生成 Delta 报告（只含新事件）"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    sg_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC+8')
    
    # 过滤新事件
    new_events = [r for r in results if is_new_event(r, last_run)]
    
    report = f"""## 📍 中东战争本小时新事件（截至 {sg_time}）

"""
    
    if not new_events:
        report += "**过去 60 分钟无重大新战斗报道**\n\n"
    else:
        # 分类展示
        military = [r for r in new_events if any(kw in (r.get('title','')+r.get('content','')).lower() for kw in ['attack', 'strike', 'missile', 'bomb', '袭击', '轰炸', '导弹'])]
        casualties = [r for r in new_events if any(kw in (r.get('title','')+r.get('content','')).lower() for kw in ['killed', 'dead', 'injured', '死', '伤', '亡'])]
        diplomacy = [r for r in new_events if any(kw in (r.get('title','')+r.get('content','')).lower() for kw in ['statement', 'declared', '声明', '发言人'])]
        
        if military:
            report += "### ⚔️ 军事行动\n"
            for r in military[:5]:
                title = r.get('title', '无标题')
                url = r.get('url', '')
                source = url.split('//')[-1].split('/')[0] if '//' in url else "未知"
                report += f"- {title}（{source}）\n"
            report += "\n"
        
        if casualties:
            report += "### 🩸 伤亡情况\n"
            for r in casualties[:3]:
                title = r.get('title', '无标题')
                url = r.get('url', '')
                source = url.split('//')[-1].split('/')[0] if '//' in url else "未知"
                report += f"- {title}（{source}）\n"
            report += "\n"
        
        if diplomacy:
            report += "### 🏛️ 外交动态\n"
            for r in diplomacy[:2]:
                title = r.get('title', '无标题')
                url = r.get('url', '')
                source = url.split('//')[-1].split('/')[0] if '//' in url else "未知"
                report += f"- {title}（{source}）\n"
            report += "\n"
    
    # 来源统计
    sources = set()
    for r in new_events:
        url = r.get('url', '')
        if url:
            sources.add(url.split('//')[-1].split('/')[0])
    
    report += f"""---
**来源：** {', '.join(list(sources)[:5]) if sources else 'Tavily'} | **新事件数：** {len(new_events)}

*下次更新：1 小时后 | 状态：{timestamp}*
"""
    return report

def send_to_feishu(report):
    """发送飞书"""
    try:
        truncated = report[:2000]
        cmd = f'openclaw message send --channel feishu --target "ou_387ea30b17d6ea838f90c47bdb655330" --message "{truncated}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ 已发送飞书")
        else:
            print(f"发送失败：{result.stderr}")
    except Exception as e:
        print(f"发送失败：{e}")

def main():
    print(f"开始中东战争 Delta 监控 v11 - {datetime.utcnow().isoformat()}Z")
    
    # 读取状态
    last_run = load_state()
    print(f"上次运行：{last_run.isoformat()}Z")
    
    all_results = []
    
    # Tavily 搜索
    for query in SEARCH_QUERIES:
        print(f"搜索：{query}")
        results = tavily_search(query)
        all_results.extend(results)
        print(f"  {len(results)} 条")
    
    # 去重
    seen = set()
    unique = []
    for r in all_results:
        url = r.get('url', '')
        if url not in seen:
            seen.add(url)
            unique.append(r)
    
    print(f"去重后：{len(unique)} 条")
    
    # 生成 Delta 报告
    report = generate_delta_report(unique, last_run)
    
    # 保存
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"delta_{timestamp}.md"
    output_file.write_text(report, encoding='utf-8')
    
    print(f"\n{report[:500]}...")
    
    # 发送
    send_to_feishu(report)
    
    # 更新状态
    save_state()
    print(f"状态已更新：{datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
