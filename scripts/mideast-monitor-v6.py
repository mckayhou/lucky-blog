#!/usr/bin/env python3
"""
中东战争监控脚本 v6 - 优化版
- 更精准的日期解析
- 去重分类（每条新闻只出现一次）
- 提取关键数字（伤亡、地点）
"""

import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path

# 精准搜索关键词
QUERIES = [
    "中东战争 2026 年 3 月 以色列 伊朗 袭击",
    "Israel Iran war March 2026 attack",
    "加沙 哈马斯 停火 最新",
]

# 排除词（过滤游戏、色情、无关内容）
EXCLUDE_WORDS = [
    '魔兽世界', 'wow', '加基森', 'gadgetzan', '沙塔斯', 'shattrath', '游戏攻略', 'game',
    '黑料', '吃瓜', '不雅视频', '网红', '色情', 'porn', 'xxx',
    'tag/黑料', 'campus.xlvfxbak',
]

OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def search_duckduckgo(query):
    """搜索 DuckDuckGo"""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
            filtered = []
            for r in results:
                text = (r.get('title', '') + r.get('body', '')).lower()
                if not any(kw in text for kw in EXCLUDE_WORDS):
                    filtered.append(r)
            return filtered[:5]
    except Exception as e:
        print(f"搜索失败 {query}: {e}")
        return []

def parse_date(text):
    """精准日期解析"""
    today = datetime.now()
    
    # 中文日期
    cn_patterns = [
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: f"{m.group(2)}-{m.group(3)}"),
        (r'(\d{1,2})月(\d{1,2})日', lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r'今天|今日', lambda m: today.strftime('%m-%d')),
        (r'昨天|昨日', lambda m: (today - timedelta(days=1)).strftime('%m-%d')),
        (r'前天', lambda m: (today - timedelta(days=2)).strftime('%m-%d')),
    ]
    
    for pattern, formatter in cn_patterns:
        match = re.search(pattern, text)
        if match:
            return formatter(match)
    
    # 英文日期
    en_patterns = [
        (r'(\d{1,2}) ([A-Z][a-z]+) (\d{4})', lambda m: f"{datetime.strptime(m.group(2), '%b').month}-{m.group(1)}"),
        (r'today|hours ago', lambda m: today.strftime('%m-%d')),
        (r'yesterday|1 day ago', lambda m: (today - timedelta(days=1)).strftime('%m-%d')),
    ]
    
    for pattern, formatter in en_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return formatter(None)
    
    return "近期"

def extract_numbers(text):
    """提取关键数字（伤亡、袭击次数等）"""
    numbers = {}
    
    # 伤亡数字
    dead_match = re.search(r'(\d+)\s*(死|亡|killed|dead|deaths)', text, re.IGNORECASE)
    injured_match = re.search(r'(\d+)\s*(伤|injured|wounded)', text, re.IGNORECASE)
    
    if dead_match:
        numbers['死亡'] = dead_match.group(1)
    if injured_match:
        numbers['受伤'] = injured_match.group(1)
    
    return numbers

def classify_news(r):
    """智能分类（优先级：军事 > 伤亡 > 外交 > 经济）"""
    title = r.get('title', '')
    body = r.get('body', '')
    text = (title + ' ' + body).lower()
    
    # 评分系统
    scores = {
        'military': 0,
        'casualties': 0,
        'diplomacy': 0,
        'economy': 0,
    }
    
    # 军事关键词
    military_kw = ['attack', 'strike', 'bomb', 'missile', 'airstrike', '袭击', '轰炸', '导弹', '空袭', '军事']
    scores['military'] = sum(1 for kw in military_kw if kw in text)
    
    # 伤亡关键词
    casualties_kw = ['dead', 'killed', 'die', 'injured', 'casualty', '死', '伤', '亡']
    scores['casualties'] = sum(1 for kw in casualties_kw if kw in text)
    
    # 外交关键词
    diplomacy_kw = ['embassy', 'diplomat', 'statement', 'ministry', '外交', '使馆', '发言人', '声明']
    scores['diplomacy'] = sum(1 for kw in diplomacy_kw if kw in text)
    
    # 经济关键词
    economy_kw = ['oil', 'economy', 'trade', 'economic', 'market', '石油', '经济', '贸易', '市场']
    scores['economy'] = sum(1 for kw in economy_kw if kw in text)
    
    # 返回最高分分类
    max_category = max(scores, key=scores.get)
    if scores[max_category] == 0:
        return 'other'
    return max_category

def generate_report(results):
    """生成优化报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 分类（每条新闻只属于一个分类）
    categories = {
        'military': [],
        'casualties': [],
        'diplomacy': [],
        'economy': [],
        'other': [],
    }
    
    for r in results:
        category = classify_news(r)
        categories[category].append(r)
    
    # 生成报告
    report = f"""## 📍 中东战况速报 ({timestamp})

"""
    
    category_names = {
        'military': ('⚔️', '军事行动'),
        'casualties': ('🩸', '伤亡情况'),
        'diplomacy': ('🏛️', '外交动态'),
        'economy': ('🛢️', '经济影响'),
        'other': ('📰', '其他新闻'),
    }
    
    for cat_key, (emoji, cat_name) in category_names.items():
        items = categories[cat_key]
        if items:
            report += f"### {emoji} {cat_name}\n"
            for r in items[:5]:
                title = r.get('title', '无标题')
                url = r.get('href', '未知')
                date = parse_date(title + ' ' + r.get('body', ''))
                numbers = extract_numbers(title + ' ' + r.get('body', ''))
                
                report += f"- [{date}] {title}\n"
                if numbers:
                    nums = ', '.join(f"{k}{v}" for k, v in numbers.items())
                    report += f"  🔢 {nums}\n"
                report += f"  📎 {url}\n\n"
    
    # 统计
    report += f"""
---
### 📊 数据摘要
- 共搜索：{len(results)} 条新闻
- 军事行动：{len(categories['military'])} 条
- 伤亡报告：{len(categories['casualties'])} 条
- 外交动态：{len(categories['diplomacy'])} 条
- 经济影响：{len(categories['economy'])} 条

*数据来源：DuckDuckGo · 下次更新：2 小时后*
*完整日志：/root/.openclaw/workspace/logs/mideast/*
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
        print(f"发送飞书失败：{e}")

def main():
    print(f"开始中东战争监控 v6 - {datetime.now().isoformat()}")
    
    all_results = []
    
    for query in QUERIES:
        print(f"搜索：{query}")
        results = search_duckduckgo(query)
        all_results.extend(results)
        print(f"  找到 {len(results)} 条相关新闻")
    
    if not all_results:
        print("未找到任何结果")
        all_results = [{"title": "暂无最新战况", "href": "", "body": "可能网络问题或局势平静"}]
    
    # 去重
    seen = set()
    unique = []
    for r in all_results:
        key = r.get('title', '') + r.get('body', '')
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    print(f"去重后：{len(unique)} 条结果")
    
    # 生成报告
    report = generate_report(unique)
    
    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"report_{timestamp}.md"
    output_file.write_text(report, encoding='utf-8')
    
    print(f"\n{report[:600]}...")
    print(f"报告已保存：{output_file}")
    
    # 发送
    send_to_feishu(report)

if __name__ == "__main__":
    main()
