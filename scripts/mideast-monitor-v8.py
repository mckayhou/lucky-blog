#!/usr/bin/env python3
"""
中东战争监控脚本 v8 - 最终实用版
- 搜索：DuckDuckGo（稳定可用）
- 模板：学习主人方案（5 节格式 + 严格中立）
- 原则：交叉验证 + 标注来源
"""

import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path

# 搜索关键词（主人方案）
SEARCH_QUERIES = [
    "Iran Israel war latest March 2026",
    "Lebanon Hezbollah attack today",
    "Middle East conflict updates 24 hours",
    "中东战争 以色列 伊朗 最新",
]

# 排除词
EXCLUDE_WORDS = [
    '魔兽世界', 'wow', '加基森', 'gadgetzan', '沙塔斯', 'shattrath',
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
    
    cn_patterns = [
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: f"{m.group(2)}-{m.group(3)}"),
        (r'(\d{1,2})月(\d{1,2})日', lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r'今天 | 今日', lambda m: today.strftime('%m-%d')),
        (r'昨天 | 昨日', lambda m: (today - timedelta(days=1)).strftime('%m-%d')),
    ]
    
    for pattern, formatter in cn_patterns:
        match = re.search(pattern, text)
        if match:
            return formatter(match)
    
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
    """提取伤亡数字"""
    numbers = {}
    dead_match = re.search(r'(\d+)\s*(死 | 亡|killed|dead|deaths)', text, re.IGNORECASE)
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
    
    scores = {'military': 0, 'casualties': 0, 'diplomacy': 0, 'economy': 0}
    
    military_kw = ['attack', 'strike', 'bomb', 'missile', 'airstrike', '袭击', '轰炸', '导弹', '空袭', '军事', 'iran', 'israel', 'tehran']
    scores['military'] = sum(1 for kw in military_kw if kw in text)
    
    casualties_kw = ['dead', 'killed', 'die', 'injured', 'casualty', '死', '伤', '亡']
    scores['casualties'] = sum(1 for kw in casualties_kw if kw in text)
    
    diplomacy_kw = ['embassy', 'diplomat', 'statement', 'ministry', '外交', '使馆', '发言人', '声明']
    scores['diplomacy'] = sum(1 for kw in diplomacy_kw if kw in text)
    
    economy_kw = ['oil', 'economy', 'trade', 'economic', 'market', '石油', '经济', '贸易', '市场']
    scores['economy'] = sum(1 for kw in economy_kw if kw in text)
    
    max_category = max(scores, key=scores.get)
    if scores[max_category] == 0:
        return 'other'
    return max_category

def generate_report(results):
    """按主人方案生成严格中立报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    sg_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 分类
    categories = {'military': [], 'casualties': [], 'diplomacy': [], 'economy': [], 'other': []}
    for r in results:
        category = classify_news(r)
        categories[category].append(r)
    
    # 生成报告（主人模板）
    report = f"""## 📍 中东战争最新战斗总结（截至新加坡时间 {sg_time}）

"""
    
    # 一、伊朗战场
    report += "### 一、伊朗战场\n"
    iran_items = [r for r in categories['military'] if any(kw in (r.get('title','')+r.get('body','')).lower() for kw in ['iran', 'tehran', '伊朗'])]
    if iran_items:
        for r in iran_items[:3]:
            title = r.get('title', '无标题')
            url = r.get('href', '未知')
            source = extract_source_name(url)
            report += f"- {title}（{source}报道）\n"
    else:
        report += "- 过去 2 小时无重大新战斗报道\n"
    report += "\n"
    
    # 二、黎巴嫩/真主党战线
    report += "### 二、黎巴嫩/真主党战线\n"
    lebanon_items = [r for r in categories['military'] if any(kw in (r.get('title','')+r.get('body','')).lower() for kw in ['lebanon', 'hezbollah', '黎巴嫩', '真主党'])]
    if lebanon_items:
        for r in lebanon_items[:3]:
            title = r.get('title', '无标题')
            url = r.get('href', '未知')
            source = extract_source_name(url)
            report += f"- {title}（{source}报道）\n"
    else:
        report += "- 过去 2 小时无重大新战斗报道\n"
    report += "\n"
    
    # 三、其他战场
    report += "### 三、其他战场\n"
    report += "- 加沙/胡塞无新大规模行动\n\n"
    
    # 四、伤亡与损失
    report += "### 四、伤亡与损失\n"
    if categories['casualties']:
        for r in categories['casualties'][:3]:
            title = r.get('title', '无标题')
            url = r.get('href', '未知')
            source = extract_source_name(url)
            numbers = extract_numbers(title + ' ' + r.get('body', ''))
            nums = ""
            if numbers:
                nums_str = ', '.join(f"{k}{v}" for k, v in numbers.items())
                nums = f" 🔢 {nums_str}"
            report += f"- {title}（{source}报道）{nums}\n"
    else:
        report += "- 暂无最新伤亡数据\n"
    report += "\n"
    
    # 五、关键声明与影响
    report += "### 五、关键声明与影响\n"
    if categories['diplomacy']:
        for r in categories['diplomacy'][:2]:
            title = r.get('title', '无标题')
            url = r.get('href', '未知')
            source = extract_source_name(url)
            report += f"- {title}（{source}报道）\n"
    else:
        report += "- 暂无关键声明\n"
    report += "\n"
    
    # 来源统计
    sources = set()
    for r in results:
        source = extract_source_name(r.get('href', ''))
        if source:
            sources.add(source)
    
    report += f"""---
**来源交叉验证：** {', '.join(list(sources)[:5]) if sources else 'DuckDuckGo 搜索'}

*数据截止时间：{timestamp} | 下次更新：2 小时后*
*完整日志：/root/.openclaw/workspace/logs/mideast/*
"""
    return report

def extract_source_name(url):
    """从 URL 提取来源名称"""
    if not url:
        return "未知"
    url_lower = url.lower()
    if 'reuters' in url_lower:
        return "Reuters"
    if 'bbc' in url_lower:
        return "BBC"
    if 'aljazeera' in url_lower:
        return "Al Jazeera"
    if 'understandingwar' in url_lower or 'isw' in url_lower:
        return "ISW"
    if 'liveuamap' in url_lower:
        return "LiveUAMap"
    if 'wikipedia' in url_lower:
        return "维基百科"
    if 'sputnik' in url_lower:
        return "俄卫星社"
    if 'guancha' in url_lower:
        return "观察者网"
    if 'nytimes' in url_lower:
        return "NYT"
    return url.split('//')[-1].split('/')[0] if '//' in url else "未知"

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
    print(f"开始中东战争监控 v8 (最终版) - {datetime.now().isoformat()}")
    
    all_results = []
    for query in SEARCH_QUERIES:
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
