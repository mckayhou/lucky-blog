#!/usr/bin/env python3
"""
中东战争监控脚本
每 2 小时搜索全网战斗信息并总结
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

# 搜索关键词 - 优先实时新闻
QUERIES = [
    "中东 以色列 伊朗 袭击 2026 年 3 月 4 日",
    "Israel Iran attack March 4 2026",
    "加沙 战斗 最新 今天",
    "Middle East breaking news 24 hours",
    "site:twitter.com 中东 战争 2026",
    "site:reddit.com/r/worldnews Middle East 2026"
]

# 新闻源 RSS（实时）
NEWS_RSS = [
    "https://feeds.reuters.com/Reuters/worldNews",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://m.news.cctv.com/rss/world/",
]

# 输出文件
OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def search_with_duckduckgo(query, num_results=10):
    """用 duckduckgo-search 库搜索（免费，无需 API key）"""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            return results
    except ImportError:
        print(f"安装 duckduckgo-search: pip install duckduckgo-search")
        subprocess.run(["pip", "install", "duckduckgo-search", "-q"])
        return search_with_duckduckgo(query, num_results)
    except Exception as e:
        print(f"搜索失败 {query}: {e}")
        return []

def fetch_url_content(url, max_chars=2000):
    """抓取网页内容"""
    try:
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        
        # 简单提取正文（去除 HTML 标签）
        import re
        text = re.sub(r'<[^>]+>', ' ', resp.text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars]
    except Exception as e:
        return f"抓取失败：{e}"

def summarize_with_llm(text, query):
    """用本地 LLM 总结"""
    try:
        import requests
        
        prompt = f"""你是战地新闻分析师。请根据以下搜索结果，总结中东战争最新战况。

搜索词：{query}

搜索结果：
{text}

请按以下格式输出：

## 📍 最新战况（{datetime.now().strftime('%Y-%m-%d %H:%M')}）

### 关键事件
- [列出 3-5 个最重要的战斗/政治事件]

### 伤亡/损失
- [如有数据]

### 国际反应
- [各国/组织表态]

### 信息来源
- [列出主要来源]

要求：简洁、客观、标注时间。"""

        # 调用本地 LLM（根据实际配置调整）
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "stream": False,
                "max_tokens": 1000
            },
            timeout=60
        )
        return response.json().get('response', '总结失败')
    except Exception as e:
        return f"LLM 调用失败：{e}\n\n原始内容：\n{text[:500]}"

def main():
    print(f"开始中东战争监控 - {datetime.now().isoformat()}")
    
    all_results = []
    
    # 搜索多个关键词
    for query in QUERIES:
        print(f"搜索：{query}")
        results = search_with_duckduckgo(query, num_results=5)
        all_results.extend(results)
        print(f"  找到 {len(results)} 条结果")
    
    if not all_results:
        print("未找到任何结果")
        return
    
    # 去重（按 URL）
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get('href', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)
    
    print(f"去重后：{len(unique_results)} 条结果")
    
    # 生成总结
    summary_text = "\n\n".join([
        f"标题：{r.get('title', '无标题')}\n来源：{r.get('href', '未知')}\n摘要：{r.get('body', '无摘要')}"
        for r in unique_results[:15]  # 取前 15 条
    ])
    
    # 尝试用 LLM 总结
    summary = summarize_with_llm(summary_text, QUERIES[0])
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"report_{timestamp}.md"
    output_file.write_text(summary, encoding='utf-8')
    
    # 输出到 stdout（供 cron 日志）
    print(f"\n{'='*60}")
    print(summary)
    print(f"{'='*60}")
    print(f"报告已保存：{output_file}")
    
    # 发送到飞书（如果配置了）
    send_to_feishu(summary)

def send_to_feishu(summary):
    """发送总结到飞书"""
    try:
        # 写入临时文件，用 openclaw message 发送
        report_file = OUTPUT_DIR / "latest_report.txt"
        report_file.write_text(f"🦞 中东战争监控报告\n\n{summary[:2000]}\n\n完整报告：/root/.openclaw/workspace/logs/mideast/", encoding='utf-8')
        
        # 通过 openclaw message 发送
        cmd = f'openclaw message send --channel feishu --target "ou_387ea30b17d6ea838f90c47bdb655330" --message "$(cat {report_file})"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ 已发送飞书")
        else:
            print(f"发送失败：{result.stderr}")
    except Exception as e:
        print(f"发送飞书失败：{e}")

if __name__ == "__main__":
    main()
