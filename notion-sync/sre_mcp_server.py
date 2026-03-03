#!/usr/bin/env python3
"""
Notion → GitHub → Vercel 同步 MCP 服务器
基于 Claude SRE Agent 和 ClawRouter 架构设计
"""

import asyncio
import json
import sys
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

# 配置
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
GITHUB_REPO = "mckayhou/lucky-blog"
VERCEL_PROJECT_ID = "hcsgrenren-7976s-projects/lucky-blog"
SYNC_DIR = Path("/tmp/lucky-blog/posts")

# ==================== 工具定义 ====================

TOOLS = [
    {
        "name": "notion_query_database",
        "description": "Query a Notion database and return pages",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database_id": {"type": "string", "description": "Notion Database ID"},
                "query": {"type": "string", "description": "Search query (optional)"},
                "page_size": {"type": "number", "description": "Results per page (max 100)", "default": 20}
            },
            "required": ["database_id"]
        }
    },
    {
        "name": "notion_get_page",
        "description": "Get a Notion page's content and properties",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "Notion Page ID"}
            },
            "required": ["page_id"]
        }
    },
    {
        "name": "notion_export_markdown",
        "description": "Export a Notion page to Markdown format",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "Notion Page ID"},
                "include_frontmatter": {"type": "boolean", "description": "Include YAML frontmatter", "default": True}
            },
            "required": ["page_id"]
        }
    },
    {
        "name": "github_commit_file",
        "description": "Commit a file to GitHub repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path in repo (e.g., posts/my-page.md)"},
                "content": {"type": "string", "description": "File content"},
                "message": {"type": "string", "description": "Commit message"}
            },
            "required": ["path", "content", "message"]
        }
    },
    {
        "name": "vercel_deploy",
        "description": "Trigger Vercel deployment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Vercel project ID"},
                "branch": {"type": "string", "description": "Branch to deploy", "default": "master"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "validate_content",
        "description": "Validate HTML/Markdown content before deployment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to validate"},
                "content_type": {"type": "string", "enum": ["html", "markdown"], "description": "Content type"}
            },
            "required": ["content", "content_type"]
        }
    },
    {
        "name": "sync_status",
        "description": "Get current sync status and last sync time",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# ==================== 工具处理器 ====================

async def notion_query_database(params: Dict[str, Any]) -> Dict[str, Any]:
    """查询 Notion 数据库"""
    database_id = params.get("database_id")
    query = params.get("query", "")
    page_size = params.get("page_size", 20)
    
    if not NOTION_API_KEY:
        return {"error": "NOTION_API_KEY not configured"}
    
    url = "https://api.notion.com/v1/databases/" + database_id + "/query"
    data = {"page_size": page_size}
    if query:
        data["filter"] = {
            "property": "Name",
            "rich_text": {"contains": query}
        }
    
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
            return {
                "pages": result.get("results", []),
                "has_more": result.get("has_more", False),
                "next_cursor": result.get("next_cursor")
            }
    except Exception as e:
        return {"error": str(e)}


async def notion_get_page(params: Dict[str, Any]) -> Dict[str, Any]:
    """获取 Notion 页面内容"""
    page_id = params.get("page_id")
    
    if not NOTION_API_KEY:
        return {"error": "NOTION_API_KEY not configured"}
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2025-09-03"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}


async def notion_export_markdown(params: Dict[str, Any]) -> Dict[str, Any]:
    """导出 Notion 页面为 Markdown"""
    page_id = params.get("page_id")
    include_frontmatter = params.get("include_frontmatter", True)
    
    # 简化实现：获取页面属性并生成 Markdown
    page_data = await notion_get_page({"page_id": page_id})
    
    if "error" in page_data:
        return page_data
    
    properties = page_data.get("properties", {})
    title = ""
    
    # 获取标题
    if "Name" in properties:
        title = properties["Name"].get("title", [{}])[0].get("plain_text", "")
    
    # 生成 Markdown
    md_content = ""
    if include_frontmatter:
        md_content += f"""---
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
source: Notion
---

"""
    
    md_content += f"# {title}\n\n"
    md_content += f"*从 Notion 同步 · {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    md_content += "---\n\n"
    md_content += f"> 📄 Notion Page ID: {page_id}\n"
    
    return {
        "markdown": md_content,
        "title": title,
        "page_id": page_id
    }


async def github_commit_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """提交文件到 GitHub"""
    path = params.get("path")
    content = params.get("content")
    message = params.get("message")
    
    # 安全限制：只能提交到 posts/ 目录
    if not path.startswith("posts/"):
        return {"error": "Path must start with 'posts/'"}
    
    if not GITHUB_TOKEN:
        return {"error": "GITHUB_TOKEN not configured"}
    
    # 获取当前 SHA（如果是更新）
    sha = None
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            sha = data.get("sha")
    except:
        pass  # 文件不存在，创建新文件
    
    # 提交
    import base64
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
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
            return {
                "success": True,
                "sha": result["commit"]["sha"],
                "url": result["content"]["html_url"]
            }
    except Exception as e:
        return {"error": str(e)}


async def vercel_deploy(params: Dict[str, Any]) -> Dict[str, Any]:
    """触发 Vercel 部署"""
    project_id = params.get("project_id")
    branch = params.get("branch", "master")
    
    if not VERCEL_TOKEN:
        return {"error": "VERCEL_TOKEN not configured"}
    
    # Vercel 会自动部署 GitHub push，这里只返回状态
    return {
        "success": True,
        "message": "Vercel will auto-deploy from GitHub",
        "project_id": project_id,
        "branch": branch,
        "preview_url": f"https://{project_id}.vercel.app"
    }


async def validate_content(params: Dict[str, Any]) -> Dict[str, Any]:
    """验证内容"""
    content = params.get("content")
    content_type = params.get("content_type")
    
    errors = []
    
    if content_type == "html":
        if not content.strip().startswith("<!DOCTYPE html>") and not content.strip().startswith("<html"):
            errors.append("Invalid HTML: missing DOCTYPE or html tag")
        if content.count("<") != content.count(">"):
            errors.append("Invalid HTML: mismatched tags")
    elif content_type == "markdown":
        if len(content) < 10:
            errors.append("Markdown too short")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


async def sync_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """获取同步状态"""
    status_file = SYNC_DIR.parent / ".notion-sync-status.json"
    
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
    else:
        status = {"last_sync": None, "synced_pages": []}
    
    return {
        "last_sync": status.get("last_sync"),
        "synced_pages_count": len(status.get("synced_pages", [])),
        "sync_dir": str(SYNC_DIR)
    }


# ==================== 工具分发 ====================

async def dispatch(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """分发工具调用"""
    handlers = {
        "notion_query_database": notion_query_database,
        "notion_get_page": notion_get_page,
        "notion_export_markdown": notion_export_markdown,
        "github_commit_file": github_commit_file,
        "vercel_deploy": vercel_deploy,
        "validate_content": validate_content,
        "sync_status": sync_status
    }
    
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    
    return await handler(params)


# ==================== JSON-RPC 服务器 ====================

async def main():
    """MCP 服务器主循环"""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    def send_result(request_id: Any, result: Any):
        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    
    def send_error(request_id: Any, error: str):
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": error}
        }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    
    # 初始化
    line = await reader.readline()
    init_request = json.loads(line)
    
    if init_request.get("method") == "initialize":
        send_result(init_request["id"], {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "notion-sync-mcp", "version": "0.1.0"}
        })
    
    # 主循环
    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            if method == "tools/list":
                send_result(request_id, {"tools": TOOLS})
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await dispatch(tool_name, tool_args)
                send_result(request_id, result)
            elif method == "notifications/initialized":
                pass  # No response needed
            else:
                send_error(request_id, f"Unknown method: {method}")
        
        except Exception as e:
            send_error(request.get("id", 0), str(e))


if __name__ == "__main__":
    asyncio.run(main())
