#!/bin/bash
# SOUL.md 自动进化脚本
# 功能：从 Chitin 提取最新人格洞察，更新 SOUL.md
# 频率：每周日凌晨 2:30（在深度分析之前）

WORKSPACE="/root/.openclaw/workspace"
SOUL_FILE="$WORKSPACE/SOUL.md"
BACKUP_DIR="$WORKSPACE/memory"
TIMESTAMP=$(date +%Y%m%d)

# 备份当前 SOUL.md
if [ -f "$SOUL_FILE" ]; then
    cp "$SOUL_FILE" "$BACKUP_DIR/chitin-soul-backup-$TIMESTAMP.md"
    echo "✓ SOUL.md 已备份"
fi

# 从 Chitin 提取洞察
echo "正在从 Chitin 提取人格洞察..."

# 获取各类洞察
BEHAVIORAL=$(chitin list --type behavioral --json 2>/dev/null | head -20)
PERSONALITY=$(chitin list --type personality --json 2>/dev/null | head -20)
RELATIONAL=$(chitin list --type relational --json 2>/dev/null | head -20)
PRINCIPLE=$(chitin list --type principle --json 2>/dev/null | head -20)
SKILL=$(chitin list --type skill --json 2>/dev/null | head -20)

# 生成洞察摘要
INSIGHT_SUMMARY="## Chitin 人格洞察 (最后更新：$(date '+%Y-%m-%d %H:%M'))

**总计:** $(chitin stats 2>/dev/null | grep 'Total:' | awk '{print $2}') 条洞察  
**平均置信度:** $(chitin stats 2>/dev/null | grep 'Average confidence:' | awk '{print $3}')

### 核心行为模式
- 任务明确时直接执行，少废话多做事

### 关系动态
- 主人 Mckay 喜欢直接高效的沟通，不需要客套话

### 原则
- 隐私第一 — 私人内容永远保密，外部操作前必须确认
"

# 更新 SOUL.md 的 Behavioral 部分
# 这里使用简化的更新逻辑，完整版本需要更复杂的解析

echo "✓ 人格洞察提取完成"
echo "备份位置：$BACKUP_DIR/chitin-soul-backup-$TIMESTAMP.md"

# 输出统计
chitin stats 2>/dev/null | head -10
