#!/usr/bin/env python3
"""
Notion → GitHub → Vercel 自动同步脚本
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# 配置
WORKSPACE = Path("/root/.openclaw/workspace/notion-sync")
SYNC_DIR = Path("/tmp/lucky-blog/posts")
STATUS_FILE = WORKSPACE / ".sync-status.json"

# 环境变量
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")

def log(message: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def check_env():
    """检查环境变量"""
    missing = []
    if not NOTION_API_KEY:
        missing.append("NOTION_API_KEY")
    if not NOTION_DATABASE_ID:
        missing.append("NOTION_DATABASE_ID")
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if not VERCEL_TOKEN:
        missing.append("VERCEL_TOKEN")
    
    if missing:
        log(f"❌ 缺少环境变量：{', '.join(missing)}")
        return False
    
    log("✅ 环境变量检查通过")
    return True

def query_notion_pages():
    """查询 Notion 页面"""
    log("📖 查询 Notion 数据库...")
    
    # 使用 MCP 服务器
    mcp_script = WORKSPACE / "sre_mcp_server.py"
    
    # 简单实现：直接调用 Notion API
    import urllib.request
    
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    data = {"page_size": 100}
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            pages = result.get("results", [])
            log(f"✅ 找到 {len(pages)} 个页面")
            return pages
    except Exception as e:
        log(f"❌ 查询失败：{e}")
        return []

def export_page_to_markdown(page: dict) -> tuple:
    """导出页面为 Markdown"""
    page_id = page.get("id")
    properties = page.get("properties", {})
    
    # 获取标题
    title = ""
    if "Name" in properties:
        title = properties["Name"].get("title", [{}])[0].get("plain_text", "")
    elif "title" in properties:
        title = properties["title"].get("title", [{}])[0].get("plain_text", "")
    
    if not title:
        title = f"Untitled-{page_id[:8]}"
    
    # 获取状态（如果有）
    status = "published"
    if "Status" in properties:
        status_prop = properties["Status"].get("select", {})
        if status_prop:
            status = status_prop.get("name", "published")
    
    # 只同步已发布的
    if status != "published":
        return None, None
    
    # 生成 Markdown
    md_content = f"""---
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
source: Notion
notion_id: "{page_id}"
---

# {title}

*从 Notion 自动同步 · {datetime.now().strftime('%Y-%m-%d %H:%M')}*

---

> 📄 原文链接：Notion Page {page_id[:8]}

"""
    
    return title, md_content

def commit_to_github(path: str, content: str, message: str) -> bool:
    """提交到 GitHub"""
    log(f"📦 提交到 GitHub: {path}")
    
    import urllib.request
    import base64
    
    # 获取当前 SHA
    sha = None
    try:
        url = f"https://api.github.com/repos/mckayhou/lucky-blog/contents/{path}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            sha = data.get("sha")
    except:
        pass
    
    # 提交
    url = f"https://api.github.com/repos/mckayhou/lucky-blog/contents/{path}"
    data = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode()
    }
    if sha:
        data["sha"] = sha
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            log(f"✅ 提交成功：{result['commit']['sha'][:8]}")
            return True
    except Exception as e:
        log(f"❌ 提交失败：{e}")
        return False

def trigger_vercel_deploy():
    """触发 Vercel 部署"""
    log("🚀 触发 Vercel 部署...")
    # Vercel 会自动从 GitHub 部署
    log("✅ Vercel 将自动部署（GitHub webhook）")

def save_status(synced_pages: list):
    """保存同步状态"""
    status = {
        "last_sync": datetime.now().isoformat(),
        "synced_pages": synced_pages
    }
    
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def main():
    """主函数"""
    log("=" * 50)
    log("🔄 Notion → GitHub → Vercel 同步开始")
    log("=" * 50)
    
    # 检查环境
    if not check_env():
        sys.exit(1)
    
    # 查询页面
    pages = query_notion_pages()
    if not pages:
        log("⚠️ 没有找到页面")
        sys.exit(0)
    
    synced = []
    
    # 同步每个页面
    for page in pages:
        title, md_content = export_page_to_markdown(page)
        
        if not md_content:
            continue
        
        # 生成文件名
        filename = title.lower().replace(" ", "-").replace("/", "-")
        filename = "".join(c for c in filename if c.isalnum() or c in "-_")
        filename = f"{filename}.md"
        path = f"posts/{filename}"
        
        # 提交到 GitHub
        if commit_to_github(path, md_content, f"📝 Sync from Notion: {title}"):
            synced.append({
                "title": title,
                "path": path,
                "notion_id": page.get("id")
            })
    
    # 触发 Vercel 部署
    if synced:
        trigger_vercel_deploy()
        save_status(synced)
    
    log("=" * 50)
    log(f"✅ 同步完成：{len(synced)} 个页面")
    log("=" * 50)

if __name__ == "__main__":
    main()
