#!/bin/bash
# 生酮晨间提醒 - 每天早上 8:00

MESSAGE="🦞 生酮打卡

今日任务：
• 空腹称重并记录
• 碳水 <20g（别碰米饭面条！）
• 喝水 2-3L
• 补电解质

偷吃碳水就等着受罚吧 🥩"

# 发送到 Telegram
openclaw message send --channel telegram --target 5400943792 --message "$MESSAGE" 2>/dev/null

# 发送到飞书
openclaw message send --channel feishu --target ou_387ea30b17d6ea838f90c47bdb655330 --message "$MESSAGE" 2>/dev/null

echo "晨间提醒已发送"
