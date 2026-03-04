#!/usr/bin/env python3
"""
中东战争监控脚本 v4 - 外部 LLM + 精准搜索
每 2 小时搜索全网战斗信息并总结
"""

import subprocess
import json
import re
import requests
from datetime import datetime
from pathlib import Path

# 精准搜索关键词（避免游戏/无关内容）
QUERIES = [
    "中东战争 2026 年 3 月 以色列 伊朗 袭击",
    "Israel Iran war March 2026 attack",
    "加沙 哈马斯 停火 最新",
]

# 排除词（过滤游戏等无关内容）
EXCLUDE_WORDS = ['魔兽世界', 'wow', '加基森', 'gadgetzan', '沙塔斯', 'shattrath', '游戏攻略', 'game']

OUTPUT_DIR = Path("/root/.openclaw/workspace/logs/mideast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 外部 LLM 配置（根据主人配置）
LLM_CONFIG = {
    "api_url": "https://api.siliconflow.cn/v1/chat/completions",  # 或其他配置
    "model": "qwen3.5-plus",
    "api_key": ""  # 从环境变量或配置读取
}

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

def summarize_with_external_llm(search_results):
    """用外部 LLM 总结"""
    try:
        # 准备搜索内容
        context = "\n\n".join([
            f"标题：{r.get('title', '无标题')}\n"
            f"来源：{r.get('href', '未知')}\n"
            f"摘要：{r.get('body', '无摘要')}"
            for r in search_results[:10]
        ])
        
        prompt = f"""你是战地新闻分析师。请根据以下搜索结果，总结中东战争最新战况。

搜索时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

搜索结果：
{context}

请按以下格式输出（简洁、客观）：

## 📍 中东战况速报（{datetime.now().strftime('%Y-%m-%d %H:%M')}）

### 关键事件（24 小时内）
- [列出 3-5 个最重要的战斗/政治事件，标注日期]

### 伤亡/损失
- [如有数据]

### 国际反应
- [各国/组织表态]

### 信息来源
- [列出主要来源 URL]

要求：
1. 只基于搜索结果，不编造
2. 标注时间（今天/昨天/具体日期）
3. 区分事实和推测
4. 中文输出，简洁专业"""

        # 调用外部 LLM API
        # 注意：需要配置 API key
        api_key = LLM_CONFIG.get('api_key') or subprocess.run(
            'openclaw config get llm.api_key 2>/dev/null || echo ""',
            shell=True, capture_output=True, text=True
        ).stdout.strip()
        
        if not api_key:
            # 无 API key，返回原始搜索结果
            return generate_simple_report(search_results)
        
        response = requests.post(
            LLM_CONFIG['api_url'],
            json={
                "model": LLM_CONFIG['model'],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.3
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"LLM API 失败：{response.status_code}")
            return generate_simple_report(search_results)
            
    except Exception as e:
        print(f"LLM 调用失败：{e}")
        return generate_simple_report(search_results)

def generate_simple_report(search_results):
    """无 LLM 时生成简单报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""## 📍 中东战况速报 ({timestamp})

### 最新头条
"""
    for r in search_results[:10]:
        title = r.get('title', '无标题')
        source = r.get('href', '未知')
        # 提取日期
        date_match = re.search(r'(\d{1,2} [A-Z][a-z]+ \d{4})', title + ' ' + r.get('body', ''))
        date_str = date_match.group(1) if date_match else "近期"
        report += f"- [{date_str}] {title}\n  来源：{source}\n\n"
    
    report += f"""
### 信息来源
- 共搜索到 {len(search_results)} 条相关新闻

---
*下次更新：2 小时后*
"""
    return report

def send_to_feishu(report):
    """发送飞书"""
    try:
        report_file = OUTPUT_DIR / "latest_report.txt"
        report_file.write_text(report, encoding='utf-8')
        
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
    import re
    print(f"开始中东战争监控 v4 - {datetime.now().isoformat()}")
    
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
    
    # 总结
    report = summarize_with_external_llm(unique)
    
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
