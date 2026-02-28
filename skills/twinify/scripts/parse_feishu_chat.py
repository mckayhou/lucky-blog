#!/usr/bin/env python3
"""Parse Feishu/Lark chat export and extract messages by sender."""

import re
import json
import sys
import os
from collections import Counter, defaultdict

# Feishu export format: YYYY/MM/DD HH:MM:SS\nSender: Message
# Or: YYYY-MM-DD HH:MM:SS\nSender: Message
DATE_PATTERN = re.compile(r'^(\d{4}[-/]\d{2}[-/]\d{2})\s+(\d{2}:\d{2}:\d{2})$')
SENDER_PATTERN = re.compile(r'^(.+?):\s*(.*)$')

def parse_chat(filepath, target_name):
    """Parse Feishu export and return structured data."""
    messages = []
    target_msgs = []
    other_msgs = []
    current_date = None
    current_time = None
    current_sender = None
    current_text = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for date/time line
            date_match = DATE_PATTERN.match(line)
            if date_match:
                # Save previous message if exists
                if current_sender and current_text is not None:
                    msg = {
                        'date': current_date,
                        'time': current_time,
                        'sender': current_sender,
                        'text': current_text
                    }
                    messages.append(msg)
                    if current_sender == target_name:
                        target_msgs.append(msg)
                    else:
                        other_msgs.append(msg)
                
                current_date, current_time = date_match.groups()
                current_sender = None
                current_text = None
                continue
            
            # Check for sender: message line
            if current_date and current_time:
                sender_match = SENDER_PATTERN.match(line)
                if sender_match:
                    # Save previous message if exists
                    if current_sender and current_text is not None:
                        msg = {
                            'date': current_date,
                            'time': current_time,
                            'sender': current_sender,
                            'text': current_text
                        }
                        messages.append(msg)
                        if current_sender == target_name:
                            target_msgs.append(msg)
                        else:
                            other_msgs.append(msg)
                    
                    current_sender, current_text = sender_match.groups()
                elif current_sender:
                    # Continuation of previous message
                    current_text += '\n' + line

    # Don't forget the last message
    if current_sender and current_text is not None:
        msg = {
            'date': current_date,
            'time': current_time,
            'sender': current_sender,
            'text': current_text
        }
        messages.append(msg)
        if current_sender == target_name:
            target_msgs.append(msg)
        else:
            other_msgs.append(msg)

    return messages, target_msgs, other_msgs


def analyze(target_msgs, target_name):
    """Analyze target's messages for patterns."""
    texts = [m['text'] for m in target_msgs if m['text']]

    # Filter out system messages and media placeholders
    text_msgs = [t for t in texts if not t.startswith('[系统消息]') 
                 and '[图片]' not in t 
                 and '[文件]' not in t
                 and '[表情]' not in t]

    # Word frequency (Chinese-aware: split by characters for CJK)
    all_text = ' '.join(text_msgs)
    # Simple character frequency for Chinese
    char_freq = Counter(c for c in all_text if not c.isspace() and not c.isdigit())
    top_chars = char_freq.most_common(100)

    # Message length stats
    lengths = [len(t) for t in text_msgs]
    avg_len = sum(lengths) / len(lengths) if lengths else 0

    # Emoji usage
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U0001f926-\U0001f937"
        "\U0010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+", flags=re.UNICODE
    )
    emojis = []
    for t in text_msgs:
        emojis.extend(emoji_pattern.findall(t))
    emoji_freq = Counter(emojis).most_common(20)

    # Laugh patterns (Chinese and English)
    laugh_pattern = re.compile(r'k{3,}|ha{2,}|hua+|ahu+|kkkk+|哈哈 +|嘻嘻 +|嘿嘿 +|哈哈哈 +', re.IGNORECASE)
    laugh_count = sum(1 for t in text_msgs if laugh_pattern.search(t))

    # Common phrases (2-4 character sequences for Chinese)
    phrases = []
    for t in text_msgs:
        # Extract 2-4 char sequences
        for i in range(len(t) - 1):
            phrases.append(t[i:i+2])
        for i in range(len(t) - 2):
            phrases.append(t[i:i+3])
    phrase_freq = Counter(phrases).most_common(50)

    return {
        'target_name': target_name,
        'total_messages': len(target_msgs),
        'text_messages': len(text_msgs),
        'avg_chars_per_msg': round(avg_len, 1),
        'top_chars': top_chars,
        'top_emojis': emoji_freq,
        'laugh_ratio': round(laugh_count / len(text_msgs), 2) if text_msgs else 0,
        'top_phrases': phrase_freq,
    }


def main():
    if len(sys.argv) < 4:
        print("Usage: parse_feishu_chat.py <chat_export.txt> <target_name> <output_dir>")
        print("  chat_export.txt  - Feishu exported chat file")
        print("  target_name      - Name of person to clone (as in chat)")
        print("  output_dir       - Directory to save output")
        sys.exit(1)

    filepath = sys.argv[1]
    target_name = sys.argv[2]
    output_dir = sys.argv[3]

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Parsing Feishu chat from: {filepath}")
    print(f"Target: {target_name}")

    messages, target_msgs, other_msgs = parse_chat(filepath, target_name)

    print(f"Total messages: {len(messages)}")
    print(f"Target messages: {len(target_msgs)}")
    print(f"Other messages: {len(other_msgs)}")

    # Analyze
    stats = analyze(target_msgs, target_name)
    print(f"Text messages (no media): {stats['text_messages']}")
    print(f"Avg chars per message: {stats['avg_chars_per_msg']}")
    print(f"Laugh ratio: {stats['laugh_ratio']}")

    # Save parsed data
    output = {
        'stats': stats,
        'target_messages': [{'date': m['date'], 'time': m['time'], 'text': m['text']}
                           for m in target_msgs if m['text']],
        'other_messages': [{'date': m['date'], 'time': m['time'], 'sender': m['sender'], 'text': m['text']}
                          for m in other_msgs if m['text']],
    }

    output_path = os.path.join(output_dir, 'parsed_messages.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Output saved to: {output_path}")

    # Also save target messages as plain text for easy reading
    txt_path = os.path.join(output_dir, 'target_messages.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for m in target_msgs:
            if m['text']:
                f.write(f"[{m['date']}, {m['time']}] {m['text']}\n")

    print(f"Target messages text saved to: {txt_path}")


if __name__ == '__main__':
    main()
