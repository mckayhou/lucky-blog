#!/usr/bin/env python3
"""
中东战争监控脚本 v2 - 直接抓取新闻网站
每 2 小时搜索全网战斗信息并总结
"""

import requests
import re
from datetime import datetime
from pathlib import Path

# 新闻源（直接抓取）
NEWS_URLS = [
    # 中文
    ("央视国际", "https://m.news.cctv.com/world/index.shtml"),
    ("澎湃新闻", "https://www.thepaper.cn/list_25512"),
    ("联合早报", "https://www.zaobao.com.sg/realtime/china"),
    # 英文
    ("Reuters World", "https://www.reuters.com/world/"),
    ("Al Jazeera", "https://www.aljazeera.com/where/middleeast/"),
    ("BBC Middle East", "https://www.bbc.com/news/world/middle_east"),
]

OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_news(url):
    """抓取新闻列表"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text[:50000]  # 限制大小
    except Exception as e:
        return f"抓取失败：{e}"

def extract_headlines(html, source):
    """简单提取标题"""
    headlines = []
    
    # 匹配常见标题标签
    patterns = [
        r'<h[34][^>]*>([^<]+?</h[34]>)',
        r'title="([^"]+)"',
        r'<a[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for m in matches[:10]:
            # 清理 HTML
            text = re.sub(r'<[^>]+>', '', m).strip()
            if len(text) > 10 and len(text) < 200:
                # 过滤关键词
                if any(kw in text.lower() for kw in ['中东', '以色列', '伊朗', '加沙', 'palestine', 'israel', 'iran', 'gaza', 'hamas', 'war', 'attack']):
                    headlines.append(f"- [{source}] {text}")
    
    return list(set(headlines))[:5]  # 去重，最多 5 条

def generate_report(all_headlines):
    """生成报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""## 📍 中东战况速报 ({timestamp})

### 最新头条
{chr(10).join(all_headlines[:15]) if all_headlines else "暂无最新战况"}

### 信息源
- 央视国际、澎湃新闻、联合早报
- Reuters、Al Jazeera、BBC

---
*下次更新：2 小时后*
"""
    return report

def send_to_feishu(report):
    """发送飞书"""
    try:
        report_file = OUTPUT_DIR / "latest_report.txt"
        report_file.write_text(report, encoding='utf-8')
        
        cmd = f'openclaw message send --channel feishu --target "ou_387ea30b17d6ea838f90c47bdb655330" --message "$(cat {report_file})"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ 已发送飞书")
        else:
            print(f"发送失败：{result.stderr}")
    except Exception as e:
        print(f"发送飞书失败：{e}")

def main():
    print(f"开始中东战争监控 v2 - {datetime.now().isoformat()}")
    
    all_headlines = []
    
    for source, url in NEWS_URLS:
        print(f"抓取：{source}")
        html = fetch_news(url)
        headlines = extract_headlines(html, source)
        all_headlines.extend(headlines)
        print(f"  找到 {len(headlines)} 条相关新闻")
    
    if not all_headlines:
        print("未找到相关新闻")
        all_headlines = ["- 暂无最新战况（可能网络问题或局势平静）"]
    
    # 生成报告
    report = generate_report(all_headlines)
    
    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"report_{timestamp}.md"
    output_file.write_text(report, encoding='utf-8')
    
    print(f"\n{report}")
    print(f"报告已保存：{output_file}")
    
    # 发送
    send_to_feishu(report)

if __name__ == "__main__":
    import subprocess
    main()
