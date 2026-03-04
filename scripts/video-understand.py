#!/usr/bin/env python3
"""Video understanding using Kimi K2.5 API"""
import base64
import requests
import json
import sys

API_KEY = "sk-sp-30bfb5ebf7af498f95812e0aef7b03f4"
API_URL = "https://coding.dashscope.aliyuncs.com/v1/chat/completions"

def understand_video(video_path):
    # Read and encode video
    with open(video_path, 'rb') as f:
        video_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine mime type
    mime = 'video/mp4' if video_path.endswith('.mp4') else 'video/quicktime'
    
    payload = {
        "model": "kimi-k2.5",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请分析这个视频的内容，总结关键信息。"},
                    {"type": "video_url", "video_url": {"url": f"data:{mime};base64,{video_data}"}}
                ]
            }
        ],
        "max_tokens": 2000
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    result = response.json()
    
    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    else:
        return f"Error: {json.dumps(result, ensure_ascii=False)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python video-understand.py <video_path>")
        sys.exit(1)
    
    print(understand_video(sys.argv[1]))
