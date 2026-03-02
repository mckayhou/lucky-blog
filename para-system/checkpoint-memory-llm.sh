#!/bin/bash
# OpenClaw 智能记忆检查点脚本 v2
# 功能：每 6 小时自动提取会话历史，写入记忆文件
# 频率：每 6 小时

set -e

WORKSPACE="/root/.openclaw/workspace"
MEMORY_FILE="$WORKSPACE/MEMORY.md"
DAILY_DIR="$WORKSPACE/memory"
TODAY=$(date +%Y-%m-%d)
DAILY_LOG="$DAILY_DIR/$TODAY.md"
SESSIONS_DIR="/root/.openclaw/sessions"

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

echo "- 检查点执行于 $(date '+%H:%M:%S')" >> "$DAILY_LOG"

# 抓取会话历史（如果有 openclaw CLI）
if command -v openclaw &> /dev/null; then
    echo "- 正在抓取会话历史..." >> "$DAILY_LOG"
    
    # 获取所有会话列表
    SESSIONS=$(openclaw sessions list --limit 10 2>/dev/null || echo "")
    
    if [ -n "$SESSIONS" ]; then
        # 提取关键会话信息
        echo "### 会话活动" >> "$DAILY_LOG"
        echo "$SESSIONS" >> "$DAILY_LOG"
        echo "" >> "$DAILY_LOG"
    fi
fi

# 检查 transcript 文件
TRANSCRIPT_COUNT=$(find "$WORKSPACE" -name "*.jsonl" -type f 2>/dev/null | wc -l)
if [ "$TRANSCRIPT_COUNT" -gt 0 ]; then
    echo "- 发现 $TRANSCRIPT_COUNT 个会话转录文件" >> "$DAILY_LOG"
    
    # 复制最新的转录文件到 memory 目录备份
    find "$WORKSPACE" -name "*.jsonl" -type f -mtime -1 2>/dev/null | while read f; do
        cp "$f" "$DAILY_DIR/" 2>/dev/null || true
        echo "- 已备份：$(basename $f)" >> "$DAILY_LOG"
    done
else
    echo "- ⚠️ 未发现会话转录文件（.jsonl）" >> "$DAILY_LOG"
fi

# 提炼关键记忆到 MEMORY.md（使用 LLM 如果有）
# 这里可以调用 openclaw 或其他 LLM 工具来提炼
# 暂时跳过，等后续集成

# 备份 MEMORY.md（如果存在且超过一定大小）
if [ -f "$MEMORY_FILE" ]; then
    LINES=$(wc -l < "$MEMORY_FILE")
    if [ "$LINES" -gt 500 ]; then
        BACKUP_FILE="$WORKSPACE/memory/MEMORY-backup-$(date +%Y%m%d-%H%M).md"
        cp "$MEMORY_FILE" "$BACKUP_FILE"
        echo "✓ MEMORY.md 已备份（$LINES 行）→ $BACKUP_FILE" >> "$DAILY_LOG"
    fi
fi

# 日志文件大小控制（保留最近 100 行）
if [ -f "$DAILY_LOG" ]; then
    TOTAL_LINES=$(wc -l < "$DAILY_LOG")
    if [ "$TOTAL_LINES" -gt 500 ]; then
        tail -100 "$DAILY_LOG" > "$DAILY_LOG.tmp"
        mv "$DAILY_LOG.tmp" "$DAILY_LOG"
        echo "- 日志已裁剪至 100 行" >> "$DAILY_LOG"
    fi
fi

echo "✓ 记忆检查点完成于 $(date '+%Y-%m-%d %H:%M:%S')" >> "$DAILY_LOG"
