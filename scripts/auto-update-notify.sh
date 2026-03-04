#!/bin/bash
# OpenClaw 更新通知脚本
# 每天早上 9 点执行，检查是否有更新，有则发送通知

set -e

LOG_FILE="/root/.openclaw/workspace/logs/auto-update-notify.log"
RESULT_FILE="/root/.openclaw/workspace/state/update-result.json"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 检查更新通知 ==="

# 检查结果文件是否存在
if [ ! -f "$RESULT_FILE" ]; then
    log "结果文件不存在，跳过通知"
    exit 0
fi

# 读取结果
HAS_UPDATE=$(jq -r '.hasUpdate' "$RESULT_FILE")
NOTIFIED=$(jq -r '.notified' "$RESULT_FILE")

if [ "$HAS_UPDATE" != "true" ]; then
    log "无更新，跳过通知"
    exit 0
fi

if [ "$NOTIFIED" = "true" ]; then
    log "已通知过，跳过"
    exit 0
fi

# 获取更新信息
PREV_VERSION=$(jq -r '.previousVersion' "$RESULT_FILE")
NEW_VERSION=$(jq -r '.newVersion' "$RESULT_FILE")
UPDATED_AT=$(jq -r '.updatedAt' "$RESULT_FILE")
CHANGELOG=$(jq -r '.changelog // "详见 https://github.com/openclaw/openclaw/releases"' "$RESULT_FILE")

# 发送通知（飞书）
log "发送通知..."

MESSAGE="🦞 OpenClaw 自动更新完成

**版本：** $PREV_VERSION → $NEW_VERSION
**时间：** $UPDATED_AT

**更新内容：**
$CHANGELOG

---
✅ 已自动重启 Gateway，服务正常运行"

# 使用 openclaw message 发送到飞书
# 通过 sessions_send 发送到主 session，会自动路由到飞书
openclaw agent --message "$MESSAGE" --thinking low 2>&1 | tee -a "$LOG_FILE" || {
    log "发送失败，记录到日志..."
    echo "$MESSAGE" >> "$LOG_FILE"
}

# 标记已通知
jq '.notified = true' "$RESULT_FILE" > "${RESULT_FILE}.tmp" && mv "${RESULT_FILE}.tmp" "$RESULT_FILE"

log "通知发送完成"
log "=== 通知检查完成 ==="
