#!/usr/bin/env python3
"""
全球冲突监控脚本 v14 - 报告式总结版
- 格式：整体总结 + 战区总结 + 关键事件
- 时区：北京时间 (UTC+8)
- 置信度：v3 公式 (≥70 推送)
"""

import subprocess
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Tavily API Key
TAVILY_API_KEY = "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"

# 搜索关键词（四战区）
SEARCH_QUERIES = {
    'middle_east': ["Iran Israel war", "Hezbollah attack", "Middle East conflict"],
    'europe': ["Russia Ukraine war", "Ukraine strike", "Ukraine war latest"],
    'asia': ["Taiwan Strait South China Sea", "Myanmar civil war", "Asia Pacific conflict"],
    'americas': ["Mexico cartel CJNG", "Ecuador gang violence", "Haiti gang clash"],
}

# 来源分级
TIER_S = ['reuters', 'bbc', 'understandingwar', 'isw', 'liveuamap']
TIER_A = ['timesofisrael', 'aljazeera', 'sentdefender', 'osintwarfare', 'haaretz', 'insightcrime', 'acleddata', 'irrawaddy', 'euromaidanpress']

# 状态文件
STATE_FILE = Path("/root/.openclaw/workspace/state/war_last_run.json")
OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 战区配置
THEATER_CONFIG = {
    'middle_east': {'name': '中东战场', 'summary_hint': '伊朗 - 以色列紧张局势'},
    'europe': {'name': '欧洲战场（俄乌战争）', 'summary_hint': '俄乌冲突态势'},
    'asia': {'name': '亚洲战场（台海/南海 + 缅甸内战）', 'summary_hint': '亚太热点动态'},
    'americas': {'name': '美洲战场（墨西哥卡特尔 + 厄瓜多尔帮派 + 海地帮派）', 'summary_hint': '拉美暴力局势'},
}

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['last_run'].replace('Z', '')).replace(tzinfo=None)
    except:
        return datetime.utcnow() - timedelta(hours=3)

def save_state():
    beijing_now = datetime.utcnow() + timedelta(hours=8)
    with open(STATE_FILE, 'w') as f:
        json.dump({"last_run": beijing_now.strftime('%Y-%m-%dT%H:%M:%SZ')}, f)

def tavily_search(query):
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "topic": "news",
            "search_depth": "advanced",
            "max_results": 6,
        }
        resp = requests.post(url, json=payload, timeout=30)
        return resp.json().get('results', [])
    except Exception as e:
        print(f"Tavily 失败 {query}: {e}")
        return []

def get_source_tier(url):
    url_lower = url.lower() if url else ''
    for tier in TIER_S:
        if tier in url_lower:
            return 'S'
    for tier in TIER_A:
        if tier in url_lower:
            return 'A'
    return 'B'

def calculate_confidence(results):
    events = {}
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
    
    scored = []
    for domain, event in events.items():
        tiers = event['tiers']
        if 'S' not in tiers:
            continue
        source_base = max(60 if t == 'S' else (35 if t == 'A' else 15) for t in tiers)
        unique_tiers = len(set(tiers))
        corroboration = 1.5 if unique_tiers >= 3 else (1.3 if unique_tiers == 2 else 1.0)
        freshness = 1.08
        media_bonus = 8 if any(kw in event['content'].lower() for kw in ['photo', 'image', 'video']) else 0
        confidence = (source_base * corroboration * freshness) + media_bonus
        if confidence >= 70:
            level = "High" if confidence >= 90 else ("Medium" if confidence >= 80 else "Low")
            event['confidence'] = confidence
            event['level'] = level
            event['breakdown'] = f"SourceBase={source_base} ×{corroboration}×{freshness} +{media_bonus} = {confidence:.0f}"
            scored.append(event)
    scored.sort(key=lambda x: x['confidence'], reverse=True)
    return scored

def generate_theater_summary(theater, scored_events):
    """生成战区总结（1-2 句趋势）"""
    if not scored_events:
        return "本周期无高置信度新事件，局势相对平稳。"
    
    # 简单总结：基于事件数量和高置信度事件
    high_count = len([e for e in scored_events if e['level'] == 'High'])
    med_count = len([e for e in scored_events if e['level'] == 'Medium'])
    
    if high_count > 0:
        return f"本周期发生{len(scored_events)}起高置信度事件（{high_count}起高置信），局势需密切关注。"
    elif med_count > 0:
        return f"本周期发生{len(scored_events)}起中置信度事件，局势保持关注。"
    else:
        return f"本周期发生{len(scored_events)}起低置信度事件，局势相对平稳。"

def generate_report(theater_results, last_run):
    """生成报告式总结"""
    beijing_now = datetime.utcnow() + timedelta(hours=8)
    sg_time = beijing_now.strftime('%Y-%m-%d %H:%M')
    
    # 计算各战区结果
    theater_scores = {}
    total_events = 0
    for theater in THEATER_CONFIG.keys():
        scored = calculate_confidence(theater_results.get(theater, []))
        theater_scores[theater] = scored
        total_events += len(scored)
    
    # 整体总结
    if total_events == 0:
        overall_summary = "本周期四大战场均无高置信度新事件，全球冲突局势相对平稳。"
    else:
        active_theaters = [THEATER_CONFIG[t]['name'] for t, s in theater_scores.items() if len(s) > 0]
        overall_summary = f"本周期共监测到{total_events}起高置信度事件，主要活跃战区：{', '.join(active_theaters[:3])}。"
    
    report = f"""## 📊 全球冲突本周期新事件报告（截至 {sg_time} 北京时间）【置信度 v3】

---

### 整体总结
{overall_summary}

---

"""
    
    for theater, config in THEATER_CONFIG.items():
        scored = theater_scores[theater]
        summary = generate_theater_summary(theater, scored)
        
        report += f"### {config['name']}\n"
        report += f"**战场总结**：{summary}\n"
        
        if scored:
            report += "**关键事件**：\n"
            for event in scored[:3]:
                title = event.get('title', '无标题')
                sources = list(set(event['sources']))[:2]
                confidence = event['confidence']
                level = event['level']
                breakdown = event['breakdown']
                
                report += f"- {title}（{', '.join(sources)}）【置信度：{confidence:.0f} ({level})】\n"
                report += f"  *Breakdown: {breakdown}*\n"
        else:
            report += "**关键事件**：无\n"
        
        report += "\n"
    
    report += f"""---
*数据截止：{sg_time} | 下次更新：按 Cron 时间表*
*状态文件：war_last_run.json | 日志：/root/.openclaw/workspace/logs/mideast/*
*所有时间均为北京时间（中国标准时间）*
"""
    return report

def send_to_feishu(report):
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
    print(f"开始全球冲突监控 v14 (报告式总结) - {datetime.utcnow().isoformat()}Z")
    
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
    
    print(f"\n{report[:800]}...")
    
    # 发送
    send_to_feishu(report)
    
    # 更新状态
    save_state()
    print(f"\n状态已更新：{datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
