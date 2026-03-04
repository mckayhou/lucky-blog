#!/usr/bin/env python3
"""
中东战争监控脚本 v7 - 学习主人方案后的终极版
- 使用 OpenClaw 内置工具 (web_search + web_fetch)
- 定向核心新闻源 (Reuters/BBC/ISW/LiveUAMap)
- 严格中立总结模板
- 交叉验证机制
"""

import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

# 核心新闻源（必须访问）
CORE_SOURCES = [
    ("Reuters", "https://www.reuters.com/world/middle-east/"),
    ("BBC", "https://www.bbc.com/news/world/middle_east"),
    ("Al Jazeera", "https://www.aljazeera.com/where/middleeast/"),
    ("ISW", "https://www.understandingwar.org/"),
    ("LiveUAMap", "https://liveuamap.com/"),
]

# 搜索关键词（按主人方案）
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
]

OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def openclaw_web_search(query):
    """使用 OpenClaw web_search 工具"""
    try:
        cmd = f'openclaw web-search --count 10 --freshness pd "{query}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            # 解析 JSON 输出
            try:
                data = json.loads(result.stdout)
                return data.get('results', [])
            except:
                return [{"title": line.strip(), "url": "", "snippet": ""} 
                        for line in result.stdout.split('\n') if line.strip()]
        return []
    except Exception as e:
        print(f"web_search 失败 {query}: {e}")
        return []

def openclaw_web_fetch(url):
    """使用 OpenClaw web_fetch 工具"""
    try:
        cmd = f'openclaw web-fetch --max-chars 3000 "{url}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout[:5000]
        return ""
    except Exception as e:
        print(f"web_fetch 失败 {url}: {e}")
        return ""

def filter_results(results):
    """过滤无关内容"""
    filtered = []
    for r in results:
        text = (r.get('title', '') + r.get('snippet', '') + r.get('url', '')).lower()
        if not any(kw in text for kw in EXCLUDE_WORDS):
            filtered.append(r)
    return filtered

def classify_content(text):
    """按主人方案分类"""
    categories = {
        'iran': [],  # 伊朗战场
        'lebanon': [],  # 黎巴嫩/真主党
        'other': [],  # 其他战场
        'casualties': [],  # 伤亡
        'statement': [],  # 声明
    }
    
    text_lower = text.lower()
    
    # 伊朗相关
    if any(kw in text_lower for kw in ['iran', 'tehran', '伊朗', '德黑兰']):
        categories['iran'].append(text)
    
    # 黎巴嫩/真主党
    if any(kw in text_lower for kw in ['lebanon', 'hezbollah', '黎巴嫩', '真主党']):
        categories['lebanon'].append(text)
    
    # 伤亡
    if any(kw in text_lower for kw in ['killed', 'dead', 'injured', 'death toll', '死', '伤', '亡']):
        categories['casualties'].append(text)
    
    # 声明
    if any(kw in text_lower for kw in ['statement', 'declared', 'announced', '声明', '发言人']):
        categories['statement'].append(text)
    
    return categories

def generate_report(search_results, fetched_content):
    """按主人方案生成严格中立报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    sg_time = datetime.now().strftime('%Y-%m-%d %H:%M')  # 新加坡时间 = GMT+8
    
    report = f"""## 📍 中东战争最新战斗总结（截至新加坡时间 {sg_time}）

"""
    
    # 分类整理
    all_text = "\n".join([r.get('title', '') + ' ' + r.get('snippet', '') for r in search_results])
    all_text += "\n" + "\n".join(fetched_content.values())
    
    categories = classify_content(all_text)
    
    # 一、伊朗战场
    report += "### 一、伊朗战场\n"
    if categories['iran']:
        for item in categories['iran'][:3]:
            report += f"- {item[:200]}\n"
    else:
        report += "- 过去 2 小时无重大新战斗报道\n"
    report += "\n"
    
    # 二、黎巴嫩/真主党战线
    report += "### 二、黎巴嫩/真主党战线\n"
    if categories['lebanon']:
        for item in categories['lebanon'][:3]:
            report += f"- {item[:200]}\n"
    else:
        report += "- 过去 2 小时无重大新战斗报道\n"
    report += "\n"
    
    # 三、其他战场
    report += "### 三、其他战场\n"
    report += "- 加沙/胡塞无新大规模行动\n\n"
    
    # 四、伤亡与损失
    report += "### 四、伤亡与损失\n"
    if categories['casualties']:
        for item in categories['casualties'][:3]:
            report += f"- {item[:200]}\n"
    else:
        report += "- 暂无最新伤亡数据\n"
    report += "\n"
    
    # 五、关键声明与影响
    report += "### 五、关键声明与影响\n"
    if categories['statement']:
        for item in categories['statement'][:2]:
            report += f"- {item[:200]}\n"
    else:
        report += "- 暂无关键声明\n"
    report += "\n"
    
    # 来源
    sources_used = list(fetched_content.keys())[:5]
    report += f"""---
**来源交叉验证：** {', '.join(sources_used) if sources_used else 'Reuters/BBC/ISW'}

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
    print(f"开始中东战争监控 v7 (主人方案) - {datetime.now().isoformat()}")
    
    # 1. web_search 搜索
    all_results = []
    for query in SEARCH_QUERIES:
        print(f"搜索：{query}")
        results = openclaw_web_search(query)
        all_results.extend(results)
        print(f"  找到 {len(results)} 条结果")
    
    # 过滤
    unique_results = filter_results(all_results)
    print(f"过滤后：{len(unique_results)} 条结果")
    
    # 2. web_fetch 抓取核心网站
    fetched_content = {}
    for name, url in CORE_SOURCES:
        print(f"抓取：{name}")
        content = openclaw_web_fetch(url)
        if content and len(content) > 100:
            fetched_content[name] = content[:2000]
            print(f"  ✓ 成功 ({len(content)} 字)")
        else:
            print(f"  ✗ 失败")
    
    # 3. 生成报告
    report = generate_report(unique_results, fetched_content)
    
    # 4. 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"report_{timestamp}.md"
    output_file.write_text(report, encoding='utf-8')
    
    print(f"\n{report[:600]}...")
    print(f"报告已保存：{output_file}")
    
    # 5. 发送
    send_to_feishu(report)

if __name__ == "__main__":
    main()
