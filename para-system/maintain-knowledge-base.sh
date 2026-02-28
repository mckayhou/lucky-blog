#!/bin/bash
# OpenClaw 知识库维护脚本
# 功能：每天执行知识验证、清理重复内容
# 频率：每天凌晨 4:00

WORKSPACE="/root/.openclaw/workspace"
MEMORY_FILE="$WORKSPACE/MEMORY.md"
CLEANUP_DIR="$WORKSPACE/life/archives/cleanup"
CLEANUP_REPORT="$CLEANUP_DIR/cleanup-report-$(date +%Y%m%d).md"

mkdir -p "$CLEANUP_DIR"

echo "# 知识库维护报告" > "$CLEANUP_REPORT"
echo "执行时间：$(date '+%Y-%m-%d %H:%M:%S')" >> "$CLEANUP_REPORT"
echo "" >> "$CLEANUP_REPORT"

# 1. 检查 MEMORY.md 大小
if [ -f "$MEMORY_FILE" ]; then
    MEMORY_SIZE=$(wc -c < "$MEMORY_FILE")
    MEMORY_LINES=$(wc -l < "$MEMORY_FILE")
    
    echo "## MEMORY.md 状态" >> "$CLEANUP_REPORT"
    echo "- 文件大小：$MEMORY_SIZE 字节" >> "$CLEANUP_REPORT"
    echo "- 行数：$MEMORY_LINES" >> "$CLEANUP_REPORT"
    
    # 如果超过 5000 行，建议清理
    if [ "$MEMORY_LINES" -gt 5000 ]; then
        echo "- ⚠️ 警告：文件过大，建议归档旧内容" >> "$CLEANUP_REPORT"
    else
        echo "- ✓ 文件大小正常" >> "$CLEANUP_REPORT"
    fi
    echo "" >> "$CLEANUP_REPORT"
fi

# 2. 清理旧备份（保留最近 7 天）
echo "## 备份清理" >> "$CLEANUP_REPORT"
BACKUP_COUNT=$(ls -1 "$WORKSPACE/memory/MEMORY-backup-"*.md 2>/dev/null | wc -l)
echo "- 当前备份数量：$BACKUP_COUNT" >> "$CLEANUP_REPORT"

# 删除 7 天前的备份
find "$WORKSPACE/memory" -name "MEMORY-backup-*.md" -mtime +7 -delete 2>/dev/null
REMAINING=$(ls -1 "$WORKSPACE/memory/MEMORY-backup-"*.md 2>/dev/null | wc -l)
echo "- 清理后剩余：$REMAINING" >> "$CLEANUP_REPORT"
echo "" >> "$CLEANUP_REPORT"

# 3. 检查临时文件
echo "## 临时文件清理" >> "$CLEANUP_REPORT"
TEMP_COUNT=$(find "$WORKSPACE" -name "*.tmp" -o -name "*.bak" -o -name "*~" 2>/dev/null | wc -l)
echo "- 发现临时文件：$TEMP_COUNT" >> "$CLEANUP_REPORT"
find "$WORKSPACE" -name "*.tmp" -delete 2>/dev/null
find "$WORKSPACE" -name "*.bak" -delete 2>/dev/null
find "$WORKSPACE" -name "*~" -delete 2>/dev/null
echo "- 已清理临时文件" >> "$CLEANUP_REPORT"
echo "" >> "$CLEANUP_REPORT"

# 4. 磁盘空间检查
echo "## 磁盘空间" >> "$CLEANUP_REPORT"
df -h "$WORKSPACE" | tail -1 | awk '{print "- 使用率："$5"\n- 可用空间："$4}' >> "$CLEANUP_REPORT"
echo "" >> "$CLEANUP_REPORT"

echo "---" >> "$CLEANUP_REPORT"
echo "维护完成：$CLEANUP_REPORT"
