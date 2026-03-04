#!/usr/bin/env python3
"""
中东战争监控脚本 v5 - AI 自主总结（不调用外部 LLM）
每 2 小时搜索全网战斗信息并总结
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

# 排除词（过滤游戏等无关内容）
EXCLUDE_WORDS = ['魔兽世界', 'wow', '加基森', 'gadgetzan', '沙塔斯', 'shattrath', '游戏攻略', 'game']

OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def search_duckduckgo(query):
    """搜索 DuckDuckGo"""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
            # 过滤无关内容
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
    """从文本提取日期"""
    today = datetime.now()
    text_lower = text.lower()
    
    # 今天/昨天
    if '今天' in text_lower or 'today' in text_lower or 'hours ago' in text_lower:
        return today.strftime('%m-%d')
    if '昨天' in text_lower or 'yesterday' in text_lower or '1 day ago' in text_lower:
        return (today - timedelta(days=1)).strftime('%m-%d')
    
    # 具体日期格式
    patterns = [
        r'(\d{1,2} [A-Z][a-z]+ \d{4})',  # 4 Mar 2026
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2026-03-04
        r'(\d{1,2}月\d{1,2}日)',  # 3 月 4 日
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return "近期"

def generate_report(results):
    """AI 自主总结报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 分类整理
    military = []  # 军事行动
    casualties = []  # 伤亡
    diplomacy = []  # 外交
    economy = []  # 经济影响
    
    for r in results:
        title = r.get('title', '')
        body = r.get('body', '')
        url = r.get('href', '')
        text = title + ' ' + body
        
        # 简单分类
        if any(kw in text.lower() for kw in ['attack', 'strike', 'bomb', 'missile', '袭击', '轰炸', '导弹']):
            military.append((title, url))
        if any(kw in text.lower() for kw in ['dead', 'killed', 'die', 'injured', '死', '伤', '亡']):
            casualties.append((title, url))
        if any(kw in text.lower() for kw in ['diplomat', 'embassy', 'statement', '外交', '使馆', '发言人']):
            diplomacy.append((title, url))
        if any(kw in text.lower() for kw in ['oil', 'economy', 'trade', 'economic', '石油', '经济', '贸易']):
            economy.append((title, url))
    
    # 生成报告
    report = f"""## 📍 中东战况速报 ({timestamp})

"""
    
    if military:
        report += "### ⚔️ 军事行动\n"
        for title, url in military[:5]:
            date = parse_date(title)
            report += f"- [{date}] {title}\n  来源：{url}\n\n"
    
    if casualties:
        report += "### 🩸 伤亡情况\n"
        for title, url in casualties[:3]:
            report += f"- {title}\n  来源：{url}\n\n"
    
    if diplomacy:
        report += "### 🏛️ 外交动态\n"
        for title, url in diplomacy[:3]:
            report += f"- {title}\n  来源：{url}\n\n"
    
    if economy:
        report += "### 🛢️ 经济影响\n"
        for title, url in economy[:3]:
            report += f"- {title}\n  来源：{url}\n\n"
    
    if not (military or casualties or diplomacy or economy):
        report += "### 最新头条\n"
        for r in results[:10]:
            date = parse_date(r.get('title', '') + r.get('body', ''))
            report += f"- [{date}] {r.get('title', '无标题')}\n  来源：{r.get('href', '未知')}\n\n"
    
    report += f"""
---
*数据来源：DuckDuckGo 搜索 · 下次更新：2 小时后*
*完整日志：/root/.openclaw/workspace/logs/mideast/*
"""
    return report

def send_to_feishu(report):
    """发送飞书"""
    try:
        # 截断到 2000 字
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
    print(f"开始中东战争监控 v5 - {datetime.now().isoformat()}")
    
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
    
    print(f"\n{report[:500]}...")
    print(f"报告已保存：{output_file}")
    
    # 发送
    send_to_feishu(report)

if __name__ == "__main__":
    main()
