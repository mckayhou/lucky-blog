#!/usr/bin/env python3
"""
全球冲突监控脚本 v13 - 四战区版 (中东 + 欧洲 + 亚洲 + 美洲)
- 时区：北京时间 (UTC+8)
- 置信度：v3 公式 (≥70 推送)
- 频率：每 3 小时 + 凌晨 4 点
"""

import subprocess
import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Tavily API Key
TAVILY_API_KEY = "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"

# 搜索关键词（四战区）
SEARCH_QUERIES = {
    'middle_east': [
        "Iran Israel war past hour",
        "Lebanon Hezbollah attack today",
        "Middle East conflict updates",
    ],
    'europe': [
        "Russia Ukraine war Russian offensive",
        "Ukraine strike advance casualty",
        "Ukraine war latest updates",
    ],
    'asia': [
        "Taiwan Strait South China Sea China",
        "Myanmar civil war fighting junta resistance",
        "Asia Pacific conflict updates",
    ],
    'americas': [
        "Mexico cartel CJNG Sinaloa narco",
        "Ecuador gang Los Lobos violence",
        "Haiti gang Viv Ansanm clash",
    ]
}

# 来源分级
TIER_S = ['reuters', 'bbc', 'understandingwar', 'isw', 'liveuamap']
TIER_A = ['timesofisrael', 'aljazeera', 'sentdefender', 'osintwarfare', 'haaretz', 'insightcrime', 'acleddata', 'irrawaddy']

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
        return datetime.utcnow() - timedelta(hours=3)

def save_state():
    """保存当前运行时间（北京时间）"""
    beijing_now = datetime.utcnow() + timedelta(hours=8)
    with open(STATE_FILE, 'w') as f:
        json.dump({"last_run": beijing_now.strftime('%Y-%m-%dT%H:%M:%SZ')}, f)

def tavily_search(query):
    """Tavily 搜索"""
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "topic": "news",
            "search_depth": "advanced",
            "max_results": 8,
        }
        resp = requests.post(url, json=payload, timeout=30)
        return resp.json().get('results', [])
    except Exception as e:
        print(f"Tavily 失败 {query}: {e}")
        return []

def get_source_tier(url):
    """判断来源等级"""
    url_lower = url.lower() if url else ''
    for tier in TIER_S:
        if tier in url_lower:
            return 'S'
    for tier in TIER_A:
        if tier in url_lower:
            return 'A'
    return 'B'

def calculate_confidence(results):
    """计算置信度评分（简化版）"""
    events = {}
    
    # 按域名分组
    for r in results:
        url = r.get('url', '')
        if not url:
            continue
        domain = url.split('//')[-1].split('/')[0]
        
        if domain not in events:
            events[domain] = {
                'title': r.get('title', ''),
                'url': url,
                'content': r.get('content', ''),
                'sources': [],
                'tiers': [],
            }
        
        tier = get_source_tier(url)
        events[domain]['sources'].append(domain)
        events[domain]['tiers'].append(tier)
    
    # 计算置信度
    scored = []
    for domain, event in events.items():
        tiers = event['tiers']
        
        # 必须有 Tier S
        if 'S' not in tiers:
            continue
        
        source_base = max(60 if t == 'S' else (35 if t == 'A' else 15) for t in tiers)
        unique_tiers = len(set(tiers))
        corroboration = 1.5 if unique_tiers >= 3 else (1.3 if unique_tiers == 2 else 1.0)
        freshness = 1.08  # 默认 30-45 分钟
        media_bonus = 8 if 'photo' in event['content'].lower() or 'image' in event['content'].lower() else 0
        
        confidence = (source_base * corroboration * freshness) + media_bonus
        
        if confidence >= 70:
            level = "High" if confidence >= 90 else ("Medium" if confidence >= 80 else "Low")
            event['confidence'] = confidence
            event['level'] = level
            event['breakdown'] = f"SourceBase={source_base} ×{corroboration}×{freshness} +{media_bonus} = {confidence:.0f}"
            scored.append(event)
    
    scored.sort(key=lambda x: x['confidence'], reverse=True)
    return scored

def generate_report(theater_results, last_run):
    """生成四战区报告"""
    beijing_now = datetime.utcnow() + timedelta(hours=8)
    sg_time = beijing_now.strftime('%Y-%m-%d %H:%M')
    
    theater_names = {
        'middle_east': '中东战场',
        'europe': '欧洲战场（俄乌战争）',
        'asia': '亚洲战场（台海/南海 + 缅甸内战）',
        'americas': '美洲战场（墨西哥卡特尔 + 厄瓜多尔帮派 + 海地帮派）'
    }
    
    report = f"""## 📍 全球冲突本周期新事件（截至 {sg_time} 北京时间）【置信度 v3】

"""
    
    for theater, name in theater_names.items():
        scored = calculate_confidence(theater_results.get(theater, []))
        
        report += f"### {name}\n"
        
        if not scored:
            report += "**本周期无≥70 置信度新事件**\n\n"
        else:
            for event in scored[:3]:  # 每战区最多 3 条
                title = event.get('title', '无标题')
                sources = list(set(event['sources']))[:2]
                confidence = event['confidence']
                level = event['level']
                breakdown = event['breakdown']
                
                report += f"- **{title}**\n"
                report += f"  来源：{', '.join(sources)} | 置信度：{confidence:.0f} ({level})\n"
                report += f"  Breakdown: {breakdown}\n\n"
    
    report += f"""---
*数据截止：{sg_time} | 下次更新：按 Cron 时间表*
*状态文件：war_last_run.json | 日志：/root/.openclaw/workspace/logs/mideast/*
*所有时间均为北京时间（中国标准时间）*
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
    print(f"开始全球冲突监控 v13 (四战区) - {datetime.utcnow().isoformat()}Z")
    
    # 读取状态
    last_run = load_state()
    print(f"上次运行：{last_run.isoformat()}Z")
    
    # 并行搜索四战区
    all_results = {}
    for theater, queries in SEARCH_QUERIES.items():
        print(f"\n搜索：{theater}")
        theater_results = []
        for query in queries:
            results = tavily_search(query)
            theater_results.extend(results)
            print(f"  {query[:40]}... → {len(results)} 条")
        all_results[theater] = theater_results
    
    # 生成报告
    report = generate_report(all_results, last_run)
    
    # 保存
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"global_{timestamp}.md"
    output_file.write_text(report, encoding='utf-8')
    
    print(f"\n{report[:600]}...")
    
    # 发送
    send_to_feishu(report)
    
    # 更新状态
    save_state()
    print(f"\n状态已更新：{datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
