#!/bin/bash
# OpenClaw 更新通知发送脚本
# 每天早上 9 点执行，发送昨晚的更新结果

set -e

LOG_FILE="/root/.openclaw/workspace/logs/update-notify.log"
RESULT_FILE="/root/.openclaw/workspace/state/update-result.json"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 开始发送更新通知 ==="

# 检查结果文件是否存在
if [ ! -f "$RESULT_FILE" ]; then
    log "结果文件不存在，跳过发送"
    exit 0
fi

# 读取结果
HAS_UPDATE=$(cat "$RESULT_FILE" | grep -o '"hasUpdate": [a-z]*' | cut -d' ' -f2)
CURRENT_VERSION=$(cat "$RESULT_FILE" | grep -o '"currentVersion": "[^"]*"' | cut -d'"' -f4)
LATEST_VERSION=$(cat "$RESULT_FILE" | grep -o '"latestVersion": "[^"]*"' | cut -d'"' -f4)
PREV_VERSION=$(cat "$RESULT_FILE" | grep -o '"previousVersion": "[^"]*"' | cut -d'"' -f4)
NEW_VERSION=$(cat "$RESULT_FILE" | grep -o '"newVersion": "[^"]*"' | cut -d'"' -f4)

# 构建消息
if [ "$HAS_UPDATE" = "false" ]; then
    MESSAGE="🦞 OpenClaw 自动更新检查

✅ 已是最新版本

当前版本：$CURRENT_VERSION
检查时间：$(date '+%Y-%m-%d %H:%M')"
else
    MESSAGE="🦞 OpenClaw 自动更新完成

✅ 升级成功

升级前：$PREV_VERSION
升级后：$NEW_VERSION
升级时间：$(date '+%Y-%m-%d %H:%M')

查看详细更新内容：
https://github.com/openclaw/openclaw/releases"
fi

log "发送消息到飞书..."

# 发送飞书消息到主人
openclaw message send --channel feishu --target "ou_387ea30b17d6ea838f90c47bdb655330" --message "$MESSAGE" 2>&1 | tee -a "$LOG_FILE"

log "消息发送成功"
log "=== 更新通知完成 ==="

# 清理结果文件（可选，保留最近一次）
# rm -f "$RESULT_FILE"
