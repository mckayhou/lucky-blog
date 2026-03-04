#!/bin/bash
# 生酮每日提醒脚本

MESSAGE="🥩 生酮打卡

今日任务：
• 空腹称重并记录
• 碳水 <20g（别碰米饭面条！）
• 喝水 2-3L
• 补电解质

偷吃碳水就等着受罚吧 🦞"

# 发送到 Telegram 和飞书
curl -s "http://127.0.0.1:18789/api/message/send" \
  -H "Authorization: Bearer 35d02c17385d3f301da357dc8ad32619aebf388822b64c26" \
  -H "Content-Type: application/json" \
  -d "{\"channel\":\"telegram\",\"message\":\"$MESSAGE\"}" 2>/dev/null

curl -s "http://127.0.0.1:18789/api/message/send" \
  -H "Authorization: Bearer 35d02c17385d3f301da357dc8ad32619aebf388822b64c26" \
  -H "Content-Type: application/json" \
  -d "{\"channel\":\"feishu\",\"message\":\"$MESSAGE\"}" 2>/dev/null

echo "提醒已发送"
