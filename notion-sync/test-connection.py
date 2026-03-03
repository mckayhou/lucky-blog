#!/usr/bin/env python3
"""测试 Notion 连接"""

import os
import json
import urllib.request

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

print("🔍 测试 Notion 连接...\n")

if not NOTION_API_KEY:
    print("❌ NOTION_API_KEY 未设置")
    print("\n设置方法:")
    print('  export NOTION_API_KEY="ntn_xxxxx"')
    exit(1)

print(f"✅ NOTION_API_KEY: {NOTION_API_KEY[:10]}...")

if not NOTION_DATABASE_ID:
    print("⚠️  NOTION_DATABASE_ID 未设置（可选）")
else:
    print(f"✅ NOTION_DATABASE_ID: {NOTION_DATABASE_ID}")
    
    # 测试查询
    print("\n📖 测试数据库查询...")
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    data = {"page_size": 5}
    
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
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            pages = result.get("results", [])
            print(f"✅ 查询成功！找到 {len(pages)} 个页面")
            
            if pages:
                print("\n📄 最近页面:")
                for page in pages[:3]:
                    props = page.get("properties", {})
                    title = ""
                    if "Name" in props:
                        title = props["Name"].get("title", [{}])[0].get("plain_text", "")
                    print(f"  - {title}")
    
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误：{e.code}")
        if e.code == 401:
            print("   原因：API Key 无效")
        elif e.code == 404:
            print("   原因：Database ID 不存在或无权限")
        exit(1)
    except Exception as e:
        print(f"❌ 错误：{e}")
        exit(1)

print("\n✅ 连接测试通过！")
print("\n下一步：运行 python3 sync.py")
