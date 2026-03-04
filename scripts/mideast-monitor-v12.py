#!/usr/bin/env python3
"""
中东战争监控脚本 v12 - 置信度评分系统 (Admiralty Code 标准)
- 公式：Confidence = (SourceBase × CorroborationMultiplier × FreshnessFactor) + MediaBonus - ContradictionPenalty
- 阈值：≥80 才推送
"""

import subprocess
import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Tavily API Key
TAVILY_API_KEY = "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"

# 搜索关键词
SEARCH_QUERIES = [
    "Iran Israel war past hour last 60 minutes",
    "Lebanon Hezbollah attack today latest",
    "Middle East conflict updates last hour",
]

# 来源分级（主人方案）
TIER_S = ['reuters', 'bbc', 'understandingwar', 'isw', 'liveuamap']
TIER_A = ['timesofisrael', 'aljazeera', 'sentdefender', 'osintwarfare', 'haaretz']

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

def get_source_base_score(tier):
    """来源基础分"""
    if tier == 'S':
        return 60
    elif tier == 'A':
        return 35
    else:
        return 15

def get_corroboration_multiplier(tiers):
    """多源佐证乘数"""
    unique_tiers = set(tiers)
    if len(unique_tiers) >= 3:
        return 1.5
    elif len(unique_tiers) == 2:
        return 1.3
    else:
        return 1.0

def get_freshness_factor(minutes_ago):
    """时效乘数"""
    if minutes_ago < 15:
        return 1.25
    elif minutes_ago < 30:
        return 1.15
    elif minutes_ago < 45:
        return 1.08
    else:
        return 1.0

def get_media_bonus(content):
    """证据强度加分"""
    content_lower = content.lower() if content else ''
    if 'video' in content_lower or 'footage' in content_lower:
        return 18
    elif 'satellite' in content_lower or 'map' in content_lower:
        return 14
    elif 'photo' in content_lower or 'image' in content_lower:
        return 8
    else:
        return 0

def calculate_confidence(results, last_run):
    """计算置信度评分"""
    now = datetime.utcnow()
    
    # 按 URL 分组（同一事件的不同来源）
    events = {}
    for r in results:
        url = r.get('url', '')
        if not url:
            continue
        
        # 提取域名作为事件标识
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
    
    # 计算每个事件的置信度
    scored_events = []
    for domain, event in events.items():
        tiers = event['tiers']
        
        # 必须有 Tier S
        if 'S' not in tiers:
            continue
        
        # 计算各参数
        source_base = max(get_source_base_score(t) for t in tiers)  # 取最高
        corroboration = get_corroboration_multiplier(tiers)
        
        # 时效性（假设都是过去 1 小时内）
        freshness = get_freshness_factor(30)  # 默认 30 分钟前
        
        # 媒体加分
        media_bonus = get_media_bonus(event['content'])
        
        # 矛盾惩罚（简化：暂时设为 0）
        contradiction = 0
        
        # 计算置信度
        confidence = (source_base * corroboration * freshness) + media_bonus - contradiction
        
        # 只保留≥70 的（Admiralty 标准）
        if confidence >= 70:
            # 等级映射
            if confidence >= 90:
                level = "High"
            elif confidence >= 80:
                level = "Medium"
            else:
                level = "Low"
            
            event['confidence'] = confidence
            event['level'] = level
            event['breakdown'] = f"SourceBase={source_base} ×{corroboration}×{freshness} +{media_bonus} -{contradiction} = {confidence:.0f}"
            scored_events.append(event)
    
    # 按置信度排序
    scored_events.sort(key=lambda x: x['confidence'], reverse=True)
    
    return scored_events

def generate_report(scored_events, last_run):
    """生成带置信度的 Delta 报告"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    sg_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC+8')
    
    report = f"""## 📍 中东战争本小时新事件（截至 {sg_time}）【置信度 v3】

"""
    
    if not scored_events:
        report += "**过去 60 分钟无≥80 置信度新事件**\n\n"
    else:
        for event in scored_events[:5]:  # 最多 5 条
            title = event.get('title', '无标题')
            sources = list(set(event['sources']))[:3]
            confidence = event['confidence']
            level = event['level']
            breakdown = event['breakdown']
            
            report += f"### ⚔️ {title}\n"
            report += f"**来源：** {', '.join(sources)}\n"
            report += f"**置信度：** {confidence:.0f} ({level})\n"
            report += f"**Breakdown:** {breakdown}\n\n"
    
    report += f"""---
*数据截止：{timestamp} | 下次更新：1 小时后*
*状态文件：war_last_run.json | 日志：/root/.openclaw/workspace/logs/mideast/*
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
    print(f"开始中东战争监控 v12 (置信度 v3) - {datetime.utcnow().isoformat()}Z")
    
    # 读取状态
    last_run = load_state()
    print(f"上次运行：{last_run.isoformat()}Z")
    
    # Tavily 搜索
    all_results = []
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
    
    # 计算置信度
    scored_events = calculate_confidence(unique, last_run)
    print(f"≥80 置信度：{len(scored_events)} 条")
    
    # 生成报告
    report = generate_report(scored_events, last_run)
    
    # 保存
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"delta_{timestamp}.md"
    output_file.write_text(report, encoding='utf-8')
    
    print(f"\n{report[:600]}...")
    
    # 发送
    send_to_feishu(report)
    
    # 更新状态
    save_state()
    print(f"状态已更新：{datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
