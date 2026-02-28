#!/usr/bin/env python3
"""Fetch chat history from Feishu/Lark API."""

import requests
import json
import sys
import os
from datetime import datetime

# Feishu API endpoints
FEISHU_TOKEN_URL = "https://open.feishu.com/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_CHAT_LIST_URL = "https://open.feishu.com/open-apis/im/v1/chats"
FEISHU_MESSAGE_LIST_URL = "https://open.feishu.com/open-apis/im/v1/messages"

def get_tenant_token(app_id, app_secret):
    """Get tenant access token."""
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    response = requests.post(FEISHU_TOKEN_URL, json=payload)
    result = response.json()
    if result.get("code") != 0:
        raise Exception(f"Failed to get token: {result}")
    return result["tenant_access_token"]

def get_chat_id(token, user_id):
    """Get chat ID for a user."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": user_id}
    response = requests.get(FEISHU_CHAT_LIST_URL, headers=headers, params=params)
    result = response.json()
    if result.get("code") != 0:
        raise Exception(f"Failed to get chat: {result}")
    
    items = result.get("data", {}).get("items", [])
    if items:
        return items[0]["chat_id"]
    return None

def get_messages(token, chat_id, user_id, page_size=50):
    """Get messages from a chat."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "chat_id": chat_id,
        "msg_type": "text",
        "page_size": page_size
    }
    
    messages = []
    page_token = None
    
    while True:
        if page_token:
            params["page_token"] = page_token
        
        response = requests.get(FEISHU_MESSAGE_LIST_URL, headers=headers, params=params)
        result = response.json()
        
        if result.get("code") != 0:
            print(f"Error fetching messages: {result}")
            break
        
        items = result.get("data", {}).get("items", [])
        for msg in items:
            # Filter messages from target user
            if msg.get("sender_id", {}).get("user_id") == user_id:
                content = msg.get("content", "{}")
                if isinstance(content, str):
                    content = json.loads(content)
                messages.append({
                    "message_id": msg.get("message_id"),
                    "sender_id": msg.get("sender_id", {}).get("user_id"),
                    "content": content.get("text", ""),
                    "create_time": msg.get("create_time"),
                })
        
        has_more = result.get("data", {}).get("has_more", False)
        if not has_more:
            break
        
        page_token = result.get("data", {}).get("page_token")
    
    return messages

def main():
    if len(sys.argv) < 4:
        print("Usage: fetch_feishu_chat.py <app_id> <app_secret> <user_id> <output_file>")
        print("  app_id      - Feishu app ID (e.g., cli_a90723faf7b9dbc6)")
        print("  app_secret  - Feishu app secret")
        print("  user_id     - User ID to fetch messages from (e.g., ou_387ea30b17d6ea838f90c47bdb655330)")
        print("  output_file - Output JSON file path")
        sys.exit(1)
    
    app_id = sys.argv[1]
    app_secret = sys.argv[2]
    user_id = sys.argv[3]
    output_file = sys.argv[4]
    
    print(f"Fetching messages from Feishu for user: {user_id}")
    
    # Get token
    print("Getting access token...")
    token = get_tenant_token(app_id, app_secret)
    
    # Get chat ID
    print("Getting chat ID...")
    chat_id = get_chat_id(token, user_id)
    if not chat_id:
        print("No chat found with this user")
        sys.exit(1)
    
    print(f"Chat ID: {chat_id}")
    
    # Get messages
    print("Fetching messages...")
    messages = get_messages(token, chat_id, user_id)
    
    print(f"Fetched {len(messages)} messages from target user")
    
    # Save to file
    output = {
        "user_id": user_id,
        "chat_id": chat_id,
        "fetched_at": datetime.now().isoformat(),
        "messages": messages
    }
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Messages saved to: {output_file}")

if __name__ == '__main__':
    main()
