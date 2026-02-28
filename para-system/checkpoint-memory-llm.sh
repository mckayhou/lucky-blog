#!/bin/bash
# OpenClaw 智能记忆检查点脚本
# 功能：每 6 小时自动提取关键记忆，更新 MEMORY.md
# 频率：每 6 小时

WORKSPACE="/root/.openclaw/workspace"
MEMORY_FILE="$WORKSPACE/MEMORY.md"
DAILY_DIR="$WORKSPACE/memory"
TODAY=$(date +%Y-%m-%d)
DAILY_LOG="$DAILY_DIR/$TODAY.md"

# 确保目录存在
mkdir -p "$DAILY_DIR"

# 创建或更新今日日志
if [ ! -f "$DAILY_LOG" ]; then
    cat > "$DAILY_LOG" << EOF
# $TODAY 日志

## 活动记录

EOF
fi

# 添加检查点标记
cat >> "$DAILY_LOG" << EOF

---
## 检查点 $(date '+%Y-%m-%d %H:%M:%S')
EOF

# 如果有会话历史工具，提取关键信息
# 这里使用简化的自动记录
echo "- 检查点执行于 $(date '+%H:%M:%S')" >> "$DAILY_LOG"

# 备份 MEMORY.md（如果存在且超过一定大小）
if [ -f "$MEMORY_FILE" ]; then
    LINES=$(wc -l < "$MEMORY_FILE")
    if [ "$LINES" -gt 500 ]; then
        cp "$MEMORY_FILE" "$WORKSPACE/memory/MEMORY-backup-$(date +%Y%m%d-%H%M).md"
        echo "✓ MEMORY.md 已备份（$LINES 行）"
    fi
fi

echo "✓ 记忆检查点完成于 $(date '+%Y-%m-%d %H:%M:%S')"
