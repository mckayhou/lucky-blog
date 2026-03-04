#!/usr/bin/env python3
"""
全球冲突监控脚本 v21 - GitHub Pages 可访问版
- 生成 HTML 格式报告（不是 Markdown）
- 保存到 posts/ 目录
- 自动更新 index.html
- 时区：北京时间 (UTC+8)
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
POSTS_DIR = Path("/root/.openclaw/workspace/posts")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
POSTS_DIR.mkdir(parents=True, exist_ok=True)

# 战区配置
THEATER_CONFIG = {
    'middle_east': {'name': '中东战场', 'emoji': '⚔️', 'base_risk': 6.5},
    'europe': {'name': '欧洲战场（俄乌战争）', 'emoji': '🇪🇺', 'base_risk': 7.0},
    'asia': {'name': '亚洲战场（台海/南海 + 缅甸内战）', 'emoji': '🌏', 'base_risk': 5.5},
    'americas': {'name': '美洲战场（墨西哥卡特尔 + 厄瓜多尔帮派 + 海地帮派）', 'emoji': '🌎', 'base_risk': 6.0},
}

# 卫星地图链接
SATELLITE_MAPS = {
    'middle_east': [('LiveUAMap 中东实时卫星标注', 'https://liveuamap.com'), ('ISW 伊朗/黎巴嫩报告图', 'https://www.understandingwar.org')],
    'europe': [('LiveUAMap 乌克兰实时地图', 'https://liveuamap.com'), ('ISW 俄乌战争每日卫星更新', 'https://www.understandingwar.org/research/russia-ukraine')],
    'asia': [('LiveUAMap 台海/南海', 'https://liveuamap.com'), ('Myanmar Now 缅甸冲突地图', 'https://www.myanmar-now.org')],
    'americas': [('ACLED 拉美冲突地图', 'https://acleddata.com'), ('InSight Crime 墨西哥/中美洲', 'https://insightcrime.org')],
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
        payload = {"api_key": TAVILY_API_KEY, "query": query, "topic": "news", "search_depth": "advanced", "max_results": 6}
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
            events[domain] = {'title': r.get('title', ''), 'url': url, 'content': r.get('content', ''), 'sources': [], 'tiers': []}
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

def calculate_risk_index(scored_events, base_risk):
    if not scored_events:
        return round(base_risk * 0.8, 1)
    high_count = len([e for e in scored_events if e['level'] == 'High'])
    med_count = len([e for e in scored_events if e['level'] == 'Medium'])
    risk_adjustment = (high_count * 1.5) + (med_count * 0.8)
    risk_index = min(10.0, base_risk + risk_adjustment)
    return round(risk_index, 1)

def get_risk_label(risk_index):
    if risk_index >= 7.5:
        return "高"
    elif risk_index >= 5.0:
        return "中"
    else:
        return "低"

def generate_market_table(theater_risks):
    avg_risk = sum(theater_risks.values()) / len(theater_risks)
    max_risk = max(theater_risks.values())
    oil_change = round(1.5 + (avg_risk - 5) * 0.5, 1)
    gold_change = round(1.2 + (avg_risk - 5) * 0.4, 1)
    us_stocks_change = round(-0.5 - (avg_risk - 5) * 0.3, 1)
    eu_stocks_change = round(-0.8 - (avg_risk - 5) * 0.4, 1)
    asia_stocks_change = round(0.5 + (max_risk - 6) * 0.3, 1)
    
    return f"""<table>
<thead><tr><th>项目</th><th>变动</th><th>主要驱动因素</th><th>影响板块</th><th>风险量化</th><th>投资者建议</th></tr></thead>
<tbody>
<tr><td>油价 (Brent/WTI)</td><td><strong>{'↑' if oil_change > 0 else '↓'} {abs(oil_change)}%</strong></td><td>中东/俄乌供应担忧</td><td>能源股</td><td>波动率 +{round(10 + avg_risk * 1.5)}%</td><td>短期增配能源 ETF</td></tr>
<tr><td>黄金</td><td><strong>{'↑' if gold_change > 0 else '↓'} {abs(gold_change)}%</strong></td><td>避险情绪</td><td>黄金 ETF</td><td>波动率 +{round(6 + avg_risk * 1.2)}%</td><td>配置避险仓位</td></tr>
<tr><td>美股 (道指/纳指)</td><td><strong>{'↑' if us_stocks_change > 0 else '↓'} {abs(us_stocks_change)}%</strong></td><td>地缘风险传导</td><td>军工板块</td><td>VIX+{round(8 + avg_risk * 1.3)}</td><td>关注国防股机会</td></tr>
<tr><td>欧洲股市</td><td><strong>{'↑' if eu_stocks_change > 0 else '↓'} {abs(eu_stocks_change)}%</strong></td><td>欧洲能源担忧</td><td>能源与航空</td><td>波动率 +{round(7 + avg_risk * 1.4)}%</td><td>欧洲基金短期谨慎</td></tr>
<tr><td>亚洲市场</td><td><strong>{'↑' if asia_stocks_change > 0 else '↓'} {abs(asia_stocks_change)}%</strong></td><td>国防需求拉动</td><td>能源/军工</td><td>波动率 +{round(5 + avg_risk * 1.1)}%</td><td>增配国防 ETF</td></tr>
</tbody></table>"""

def generate_report_html(theater_results, last_run):
    """生成 HTML 格式报告"""
    beijing_now = datetime.utcnow() + timedelta(hours=8)
    sg_time = beijing_now.strftime('%Y-%m-%d %H:%M')
    
    theater_scores = {}
    theater_risks = {}
    total_events = 0
    
    for theater in THEATER_CONFIG.keys():
        scored = calculate_confidence(theater_results.get(theater, []))
        theater_scores[theater] = scored
        total_events += len(scored)
        risk_index = calculate_risk_index(scored, THEATER_CONFIG[theater]['base_risk'])
        theater_risks[theater] = risk_index
    
    overall_risk = round(sum(theater_risks.values()) / len(theater_risks), 1)
    overall_label = get_risk_label(overall_risk)
    
    if total_events == 0:
        overall_summary = "本周期四大战场均无高置信度新事件，全球冲突局势相对平稳。"
    else:
        active_theaters = [THEATER_CONFIG[t]['name'] for t, s in theater_scores.items() if len(s) > 0]
        overall_summary = f"本周期共监测到{total_events}起高置信度事件，主要活跃战区：{', '.join(active_theaters[:3])}。"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🌍 全球冲突情报简报 {sg_time}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
header {{ border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
h1 {{ margin: 0; font-size: 1.8em; color: #2c3e50; }}
.subtitle {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
.section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
.section h2 {{ margin-top: 0; color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
.risk-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; margin-left: 10px; }}
.risk-high {{ background: #fee; color: #c00; }}
.risk-medium {{ background: #ffa50033; color: #cc8800; }}
.risk-low {{ background: #eef; color: #0066cc; }}
.event {{ background: white; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #0066cc; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
th {{ background: #f0f0f0; font-weight: 600; }}
.map-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.map-links a {{ display: inline-block; padding: 8px 16px; background: #0066cc; color: white; text-decoration: none; border-radius: 4px; }}
.map-links a:hover {{ background: #0055aa; }}
footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 0.85em; }}
</style>
</head>
<body>
<header>
<h1>🌍 全球冲突情报简报</h1>
<p class="subtitle">截至 {sg_time} 北京时间 | v21 GitHub Pages 版</p>
</header>

<main>
<section class="section">
<h2>📊 总体评估</h2>
<p><strong>全局趋势</strong>：{overall_summary}</p>
<p><strong>整体风险等级</strong>：<span class="risk-badge risk-{'high' if overall_label == '高' else ('medium' if overall_label == '中' else 'low')}">{overall_label}</span></p>
<p><strong>整体风险指数</strong>：<strong>{overall_risk}/10</strong> {'🔴' if overall_risk >= 7.5 else ('🟡' if overall_risk >= 5.0 else '🟢')}</p>
</section>
"""
    
    for theater, config in THEATER_CONFIG.items():
        scored = theater_scores[theater]
        risk_index = theater_risks[theater]
        risk_label = get_risk_label(risk_index)
        
        html += f"""
<section class="section">
<h2>{config['name']} {config['emoji']}</h2>
<p><strong>风险标签</strong>：<span class="risk-badge risk-{'high' if risk_label == '高' else ('medium' if risk_label == '中' else 'low')}">{risk_label}</span></p>
<p><strong>风险指数</strong>：<strong>{risk_index}/10</strong></p>
"""
        if scored:
            html += f"<p><strong>态势评估</strong>：本周期发生{len(scored)}起高置信度事件，局势需密切关注。</p>"
            html += "<h3>关键事件</h3>"
            for event in scored[:3]:
                title = event.get('title', '无标题')
                sources = list(set(event['sources']))[:2]
                confidence = event['confidence']
                level = event['level']
                html += f"""<div class="event">
<strong>{title}</strong><br>
<small>来源：{', '.join(sources)} | 置信度：{confidence:.0f} ({level})</small>
</div>"""
        else:
            html += "<p><strong>态势评估</strong>：本周期无高置信度新事件，局势相对平稳。</p>"
            html += "<p><strong>关键事件</strong>：无</p>"
        html += "</section>"
    
    # 金融市场影响
    html += f"""
<section class="section">
<h2>💰 金融市场影响评估</h2>
{generate_market_table(theater_risks)}
<p><strong>风险展望</strong>：整体风险指数{overall_risk}/10 驱动下，若中东局势升级，油价或突破{round(80 + overall_risk * 2)}美元/桶</p>
</section>

<section class="section">
<h2>🛰️ 卫星与实时地图</h2>
<div class="map-links">
"""
    for theater, maps in SATELLITE_MAPS.items():
        theater_name = THEATER_CONFIG[theater]['name'].split('（')[0]
        for name, url in maps:
            html += f'<a href="{url}" target="_blank">{theater_name}: {name}</a>'
    html += """</div>
</section>
</main>

<footer>
<p>数据来源：Reuters/ISW/LiveUAMap/InSight Crime/ACLED/Tavily | 自动生成于 """ + sg_time + """ 北京时间</p>
<p>下次更新：按 Cron 时间表 (04:00, 08:00, 11:00, 14:00, 17:00, 20:00, 23:00)</p>
</footer>
</body>
</html>"""
    
    return html

def send_to_feishu(report_md):
    try:
        truncated = report_md[:2000]
        cmd = f'openclaw message send --channel feishu --target "ou_387ea30b17d6ea838f90c47bdb655330" --message "{truncated}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ 已发送飞书")
    except Exception as e:
        print(f"发送失败：{e}")

def push_to_github(html_content, timestamp):
    """推送 HTML 报告到 GitHub posts 目录"""
    try:
        # 保存 HTML 到 posts 目录
        html_file = POSTS_DIR / f"global-conflict-{timestamp}.html"
        html_file.write_text(html_content, encoding='utf-8')
        
        # 更新 index.html（添加新文章链接）
        index_file = Path("/root/.openclaw/workspace/index.html")
        if index_file.exists():
            index_content = index_file.read_text(encoding='utf-8')
            new_post_link = f'''
    <article class="post">
      <h2 class="post-title"><a href="posts/global-conflict-{timestamp}.html">🌍 全球冲突情报简报 {timestamp}</a></h2>
      <div class="post-meta">
        📅 {timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:]}日
        <span class="tag">全球冲突</span>
        <span class="tag">情报简报</span>
      </div>
      <p class="post-excerpt">四大战场（中东/欧洲/亚洲/美洲）风险量化评估 + 金融市场影响分析 + 卫星实时地图。</p>
      <a href="posts/global-conflict-{timestamp}.html" class="read-more">阅读全文 →</a>
    </article>
'''
            # 插入到第一个 post 之前
            if '<article class="post">' in index_content:
                index_content = index_content.replace('<article class="post">', new_post_link + '\n    <article class="post">', 1)
                index_file.write_text(index_content, encoding='utf-8')
        
        # Git 操作
        git_commands = [
            f"cd /root/.openclaw/workspace && git add posts/global-conflict-{timestamp}.html index.html",
            f"cd /root/.openclaw/workspace && git -c user.name='Global Conflict Monitor' -c user.email='monitor@localhost' commit -m '🌍 全球冲突简报 {timestamp} [auto]'",
            f"cd /root/.openclaw/workspace && git push origin master",
        ]
        
        for cmd in git_commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"Git 失败：{result.stderr}")
                return False
        
        print(f"✓ 已推送到 GitHub: posts/global-conflict-{timestamp}.html")
        print(f"✓ 网站访问：https://mckayhou.github.io/lucky-blog/posts/global-conflict-{timestamp}.html")
        return True
    except Exception as e:
        print(f"GitHub 推送失败：{e}")
        return False

def main():
    print(f"开始全球冲突监控 v21 (GitHub Pages) - {datetime.utcnow().isoformat()}Z")
    
    last_run = load_state()
    print(f"上次运行：{last_run.isoformat()}Z")
    
    all_results = {}
    for theater, queries in SEARCH_QUERIES.items():
        print(f"\n搜索：{theater}")
        theater_results = []
        for query in queries:
            results = tavily_search(query)
            theater_results.extend(results)
            print(f"  {query[:40]}... → {len(results)} 条")
        all_results[theater] = theater_results
    
    # 生成 HTML 报告
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M')
    html_report = generate_report_html(all_results, last_run)
    
    # 保存本地日志
    output_file = OUTPUT_DIR / f"global_{timestamp}.md"
    output_file.write_text(html_report, encoding='utf-8')
    
    # 发送飞书（简化版）
    md_summary = f"全球冲突简报 {timestamp} 已生成，推送到 GitHub Pages。"
    send_to_feishu(md_summary)
    
    # 推送到 GitHub
    push_to_github(html_report, timestamp)
    
    # 更新状态
    save_state()
    print(f"\n状态已更新：{datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
