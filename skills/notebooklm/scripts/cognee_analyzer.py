#!/usr/bin/env python3
"""
NotebookLM 替代方案 - 使用本地 cognee API 分析文档
"""

import requests
import sys
import os
import time

COGNEE_BASE = "http://localhost:8000/api/v1"

def upload_file(filepath, dataset_name="default"):
    """上传文件到 cognee"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        return None
    
    print(f"📤 上传文件：{filepath}")
    
    with open(filepath, 'rb') as f:
        files = {'files': f}
        data = {'dataset_name': dataset_name}
        response = requests.post(f"{COGNEE_BASE}/add", files=files, data=data)
    
    if response.status_code == 200:
        print(f"✅ 上传成功")
        return response.json()
    else:
        print(f"❌ 上传失败：{response.text}")
        return None

def process_dataset(dataset_name="default"):
    """处理数据集（cognify）"""
    print(f"🔄 处理数据集：{dataset_name}")
    
    response = requests.post(
        f"{COGNEE_BASE}/cognify",
        json={"dataset_name": dataset_name},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print(f"✅ 处理完成")
        return response.json()
    else:
        print(f"❌ 处理失败：{response.text}")
        return None

def search(query, dataset_name="default"):
    """搜索/问答"""
    print(f"🔍 搜索：{query}")
    
    response = requests.post(
        f"{COGNEE_BASE}/search",
        json={"query": query, "dataset_name": dataset_name},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*60}")
        print(f"📝 答案：\n")
        if isinstance(result, dict) and 'results' in result:
            for i, r in enumerate(result['results'][:3], 1):
                print(f"{i}. {r.get('text', 'N/A')[:500]}")
        else:
            print(result)
        print(f"{'='*60}\n")
        return result
    else:
        print(f"❌ 搜索失败：{response.text}")
        return None

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  上传文件：python3 cognee_analyzer.py upload <文件路径> [数据集名]")
        print("  处理数据：python3 cognee_analyzer.py process [数据集名]")
        print("  搜索问答：python3 cognee_analyzer.py search <问题> [数据集名]")
        print("\n示例:")
        print("  python3 cognee_analyzer.py upload /path/to/doc.pdf my-docs")
        print("  python3 cognee_analyzer.py process my-docs")
        print("  python3 cognee_analyzer.py search '总结文档内容' my-docs")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "upload":
        if len(sys.argv) < 3:
            print("❌ 请提供文件路径")
            sys.exit(1)
        filepath = sys.argv[2]
        dataset = sys.argv[3] if len(sys.argv) > 3 else "default"
        upload_file(filepath, dataset)
    
    elif action == "process":
        dataset = sys.argv[2] if len(sys.argv) > 2 else "default"
        process_dataset(dataset)
    
    elif action == "search":
        if len(sys.argv) < 3:
            print("❌ 请提供搜索问题")
            sys.exit(1)
        query = sys.argv[2]
        dataset = sys.argv[3] if len(sys.argv) > 3 else "default"
        search(query, dataset)
    
    else:
        print(f"❌ 未知操作：{action}")
        sys.exit(1)

if __name__ == '__main__':
    main()
