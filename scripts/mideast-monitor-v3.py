#!/usr/bin/env python3
"""
中东战争监控脚本 v3 - 用 web_fetch API
每 2 小时搜索全网战斗信息并总结
"""

import subprocess
from datetime import datetime
from pathlib import Path

# 新闻源 URL
NEWS_URLS = [
    ("Al Jazeera 中东", "https://www.aljazeera.com/where/middleeast/"),
    ("Reuters 世界", "https://www.reuters.com/world/"),
    ("BBC 中东", "https://www.bbc.com/news/world/middle_east"),
]

OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_url(url):
    """用 openclaw web_fetch 抓取"""
    try:
        cmd = f'openclaw web-fetch --max-chars 5000 "{url}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout[:8000]
    except Exception as e:
        return f"抓取失败：{e}"

def extract_headlines(text, source):
    """从抓取内容提取标题"""
    headlines = []
    
    # 找包含日期的行（今天或昨天）
    today = datetime.now().strftime('%-d %b')  # 4 Mar
    yesterday = datetime.now().strftime('%-d %b')  # 3 Mar
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        # 检查是否包含日期和关键词
        if any(kw in line.lower() for kw in ['iran', 'israel', 'gaza', 'attack', 'strike', 'war', '中东', '以色列', '伊朗']):
            if len(line) > 20 and len(line) < 300:
                # 清理
                line = line.replace('Published On', '').strip()
                headlines.append(f"- [{source}] {line}")
    
    return list(set(headlines))[:5]

def generate_report(all_headlines):
    """生成报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""## 📍 中东战况速报 ({timestamp})

### 最新头条
{chr(10).join(all_headlines[:15]) if all_headlines else "暂无最新战况"}

### 信息源
- Al Jazeera、Reuters、BBC

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
    print(f"开始中东战争监控 v3 - {datetime.now().isoformat()}")
    
    all_headlines = []
    
    for source, url in NEWS_URLS:
        print(f"抓取：{source}")
        text = fetch_url(url)
        headlines = extract_headlines(text, source)
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
    main()
