#!/bin/bash
# 生酮周复盘 - 每周三 21:00

MESSAGE="🦞 生酮周复盘

该交作业了：
• 当前体重：___ kg
• 本周变化：___ kg
• 腰围：___ cm
• 感受：_______

填好发到 /root/.openclaw/workspace/keto-plan.md

坚持住！💪"

# 发送到 Telegram 和飞书
openclaw message send --channel telegram --target 5400943792 --message "$MESSAGE" 2>/dev/null
openclaw message send --channel feishu --target ou_387ea30b17d6ea838f90c47bdb655330 --message "$MESSAGE" 2>/dev/null

echo "周复盘提醒已发送"
