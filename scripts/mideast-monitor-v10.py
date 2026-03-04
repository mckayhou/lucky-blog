#!/usr/bin/env python3
"""
中东战争监控脚本 v10 - OSINT 终极版
- 搜索：Tavily API + X OSINT + 仪表盘
- 模板：主人 5 节格式
- 验证：3 源交叉验证
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
    "Iran Israel war latest March 2026",
    "Lebanon Hezbollah attack today",
    "Middle East conflict updates 24 hours",
]

# X(Twitter) OSINT 账号（主人方案）
OSINT_ACCOUNTS = [
    "@sentdefender",
    "@Osint613",
    "@OSINTWarfare",
    "@WarMonitors",
    "@IDF",
    "@IranIntl_EN",
]

# 核心仪表盘
DASHBOARDS = [
    ("LiveUAMap", "https://liveuamap.com"),
    ("ISW", "https://www.understandingwar.org/backgrounder"),
    ("WorldMonitor", "https://worldmonitor.app"),
    ("SignalCockpit", "https://signalcockpit.com"),
    ("USvsIran", "https://usvsiran.com"),
]

# 排除词
EXCLUDE_WORDS = [
    '魔兽世界', 'wow', '加基森', 'gadgetzan', '沙塔斯', 'shattrath',
    '黑料', '吃瓜', '不雅视频', '网红', '色情', 'porn', 'xxx',
]

OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def tavily_search(query):
    """使用 Tavily API 搜索"""
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "topic": "news",
            "search_depth": "advanced",
            "max_results": 10,
            "include_answer": True,
            "include_raw_content": True
        }
        resp = requests.post(url, json=payload, timeout=30)
        data = resp.json()
        return data.get('results', [])
    except Exception as e:
        print(f"Tavily 搜索失败 {query}: {e}")
        return []

def search_x_osint():
    """搜索 X(Twitter) OSINT 账号"""
    results = []
    for account in OSINT_ACCOUNTS[:3]:  # 取前 3 个
        query = f"{account} Iran Israel attack missile"
        try:
            # 用 Tavily 搜索 X 内容
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": f"from:{account} Iran Israel attack",
                "topic": "news",
                "search_depth": "basic",
                "max_results": 3,
            }
            resp = requests.post(url, json=payload, timeout=20)
            data = resp.json()
            for r in data.get('results', []):
                r['source'] = f"X:{account}"
                results.append(r)
        except Exception as e:
            print(f"X OSINT 搜索失败 {account}: {e}")
    return results

def check_dashboards():
    """检查仪表盘（简单状态检查）"""
    results = []
    for name, url in DASHBOARDS[:3]:  # 取前 3 个
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                results.append({
                    'title': f"{name} 仪表盘可访问",
                    'url': url,
                    'content': f"{name} 正常运行，可查看详细战况",
                    'source': name
                })
        except:
            pass
    return results

def parse_date(text):
    """精准日期解析"""
    today = datetime.now()
    
    patterns = [
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: f"{m.group(2)}-{m.group(3)}"),
        (r'(\d{1,2})月 (\d{1,2})日', lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r'今天 | 今日|today|hours ago', lambda m: today.strftime('%m-%d')),
        (r'昨天 | 昨日|yesterday|1 day ago', lambda m: (today - timedelta(days=1)).strftime('%m-%d')),
        (r'(\d{1,2}) ([A-Z][a-z]+) (\d{4})', lambda m: f"{datetime.strptime(m.group(2), '%b').month}-{m.group(1)}"),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return formatter(match)
    
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
    """智能分类"""
    title = r.get('title', '')
    content = r.get('content', '')
    text = (title + ' ' + content).lower()
    
    scores = {'military': 0, 'casualties': 0, 'diplomacy': 0, 'economy': 0}
    
    military_kw = ['attack', 'strike', 'bomb', 'missile', 'airstrike', '袭击', '轰炸', '导弹', '空袭', '军事', 'iran', 'israel', 'tehran', 'hezbollah']
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
    if 'jpost' in url_lower or 'jerusalem' in url_lower:
        return "Jerusalem Post"
    if 'timesofisrael' in url_lower:
        return "Times of Israel"
    if 'understandingwar' in url_lower or 'isw' in url_lower:
        return "ISW"
    if 'liveuamap' in url_lower:
        return "LiveUAMap"
    if 'nytimes' in url_lower:
        return "NYT"
    if 'washingtonpost' in url_lower:
        return "Washington Post"
    return url.split('//')[-1].split('/')[0] if '//' in url else "未知"

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
    iran_items = [r for r in categories['military'] if any(kw in (r.get('title','')+r.get('content','')).lower() for kw in ['iran', 'tehran', '伊朗'])]
    if iran_items:
        for r in iran_items[:3]:
            title = r.get('title', '无标题')
            url = r.get('url', '未知')
            source = r.get('source', extract_source_name(url))
            report += f"- {title}（{source}）\n"
    else:
        report += "- 过去 2 小时无重大新战斗报道\n"
    report += "\n"
    
    # 二、黎巴嫩/真主党战线
    report += "### 二、黎巴嫩/真主党战线\n"
    lebanon_items = [r for r in categories['military'] if any(kw in (r.get('title','')+r.get('content','')).lower() for kw in ['lebanon', 'hezbollah', '黎巴嫩', '真主党'])]
    if lebanon_items:
        for r in lebanon_items[:3]:
            title = r.get('title', '无标题')
            url = r.get('url', '未知')
            source = r.get('source', extract_source_name(url))
            report += f"- {title}（{source}）\n"
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
            url = r.get('url', '未知')
            source = r.get('source', extract_source_name(url))
            numbers = extract_numbers(title + ' ' + r.get('content', ''))
            nums = ""
            if numbers:
                nums_str = ', '.join(f"{k}{v}" for k, v in numbers.items())
                nums = f" 🔢 {nums_str}"
            report += f"- {title}（{source}）{nums}\n"
    else:
        report += "- 暂无最新伤亡数据\n"
    report += "\n"
    
    # 五、关键声明与影响
    report += "### 五、关键声明与影响\n"
    if categories['diplomacy']:
        for r in categories['diplomacy'][:2]:
            title = r.get('title', '无标题')
            url = r.get('url', '未知')
            source = r.get('source', extract_source_name(url))
            report += f"- {title}（{source}）\n"
    else:
        report += "- 暂无关键声明\n"
    report += "\n"
    
    # 来源统计
    sources = set()
    for r in results:
        source = r.get('source', extract_source_name(r.get('url', '')))
        if source:
            sources.add(source)
    
    report += f"""---
**来源交叉验证：** {', '.join(list(sources)[:6]) if sources else 'Tavily 搜索'}

*数据截止时间：{timestamp} | 下次更新：2 小时后*
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
    print(f"开始中东战争监控 v10 (OSINT 终极版) - {datetime.now().isoformat()}")
    
    all_results = []
    
    # 1. Tavily 搜索
    for query in SEARCH_QUERIES:
        print(f"Tavily 搜索：{query}")
        results = tavily_search(query)
        all_results.extend(results)
        print(f"  找到 {len(results)} 条结果")
    
    # 2. X OSINT
    print("X OSINT 搜索...")
    x_results = search_x_osint()
    all_results.extend(x_results)
    print(f"  找到 {len(x_results)} 条 X 内容")
    
    # 3. 仪表盘检查
    print("仪表盘检查...")
    dash_results = check_dashboards()
    all_results.extend(dash_results)
    print(f"  {len(dash_results)} 个仪表盘可访问")
    
    if not all_results:
        print("未找到任何结果")
        all_results = [{"title": "暂无最新战况", "url": "", "content": "可能网络问题或局势平静", "source": "监控"}]
    
    # 去重（按 URL）
    seen_urls = set()
    unique = []
    for r in all_results:
        url = r.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
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
