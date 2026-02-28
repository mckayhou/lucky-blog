#!/bin/bash
# OpenClaw 夜间深度分析脚本
# 功能：每周日凌晨执行深度分析、模式提取、系统优化
# 频率：每周日 3:00

WORKSPACE="/root/.openclaw/workspace"
REPORT_DIR="$WORKSPACE/life/archives/weekly"
REPORT_FILE="$REPORT_DIR/weekly-report-$(date +%Y%m%d).md"

mkdir -p "$REPORT_DIR"

echo "# 周度深度分析报告" > "$REPORT_FILE"
echo "生成时间：$(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. 统计本周日志文件
echo "## 本周活动统计" >> "$REPORT_FILE"
WEEK_START=$(date -d '7 days ago' +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d 2>/dev/null || echo "unknown")
LOG_COUNT=$(ls -1 "$WORKSPACE/memory/"*.md 2>/dev/null | wc -l)
echo "- 日志文件总数：$LOG_COUNT" >> "$REPORT_FILE"
echo "- 分析周期：$WEEK_START 至今" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 2. MEMORY.md 状态
if [ -f "$WORKSPACE/MEMORY.md" ]; then
    MEMORY_LINES=$(wc -l < "$WORKSPACE/MEMORY.md")
    echo "## 长期记忆状态" >> "$REPORT_FILE"
    echo "- MEMORY.md 行数：$MEMORY_LINES" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

# 3. 决策日志统计
if [ -f "$WORKSPACE/life/decisions/index.json" ]; then
    DECISION_COUNT=$(cat "$WORKSPACE/life/decisions/index.json" | grep -c '"id"' || echo 0)
    echo "## 决策追踪" >> "$REPORT_FILE"
    echo "- 累计决策数：$DECISION_COUNT" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

# 4. 系统健康检查
echo "## 系统健康检查" >> "$REPORT_FILE"
DISK_USAGE=$(df -h "$WORKSPACE" | tail -1 | awk '{print $5}')
echo "- 磁盘使用率：$DISK_USAGE" >> "$REPORT_FILE"

# 检查工作目录大小
WORKSPACE_SIZE=$(du -sh "$WORKSPACE" 2>/dev/null | cut -f1)
echo "- 工作目录大小：$WORKSPACE_SIZE" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 5. 本周亮点（如果有日志内容）
echo "## 本周亮点" >> "$REPORT_FILE"
echo "_待填充 - 需要 LLM 分析日志内容_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 6. 建议
echo "## 优化建议" >> "$REPORT_FILE"
echo "- 定期回顾 MEMORY.md，删除过时信息" >> "$REPORT_FILE"
echo "- 检查决策日志，追踪重要决策的结果" >> "$REPORT_FILE"
echo "- 清理旧的备份文件（保留最近 7 天）" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "---" >> "$REPORT_FILE"
echo "报告生成完成：$REPORT_FILE"
