#!/usr/bin/env python3
"""OCR using current session's model via OpenAI-compatible API"""
import base64
import requests
import json
import sys

API_KEY = "sk-sp-30bfb5ebf7af498f95812e0aef7b03f4"
API_URL = "https://coding.dashscope.aliyuncs.com/v1/chat/completions"

def ocr_image(image_path):
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine mime type
    mime = 'image/jpeg' if image_path.endswith('.jpg') or image_path.endswith('.jpeg') else 'image/png'
    
    # Try qwen3-max first (supports vision)
    payload = {
        "model": "qwen3-max-2026-01-23",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请提取图片中的所有文字，保持原有格式。"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}}
                ]
            }
        ],
        "max_tokens": 2000
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    result = response.json()
    
    if 'choices' in result and len(result['choices']) > 0:
        content = result['choices'][0]['message']['content']
        # Check if model actually saw the image
        if "无法" in content or "看不到" in content or "上传" in content:
            # Model doesn't support vision, try alternative
            return None
        return content
    else:
        return f"Error: {json.dumps(result, ensure_ascii=False)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr-qwen.py <image_path>")
        sys.exit(1)
    
    result = ocr_image(sys.argv[1])
    if result:
        print(result)
    else:
        print("当前模型不支持视觉识别，需要安装本地 OCR 工具。")
        sys.exit(1)
