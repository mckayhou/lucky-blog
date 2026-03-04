#!/bin/bash
# OpenClaw 自动更新检查脚本
# 每 2 天早上 4 点执行

set -e

LOG_FILE="/root/.openclaw/workspace/logs/auto-update.log"
STATE_FILE="/root/.openclaw/workspace/state/last-update-check.json"
RESULT_FILE="/root/.openclaw/workspace/state/update-result.json"

# 确保目录存在
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$STATE_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 开始检查更新 ==="

# 获取当前版本
CURRENT_VERSION=$(openclaw --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
log "当前版本：$CURRENT_VERSION"

# 获取最新版本
LATEST_VERSION=$(npm view openclaw@latest version 2>&1)
log "最新版本：$LATEST_VERSION"

# 比较版本
if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
    log "已是最新版本，无需更新"
    cat > "$RESULT_FILE" << EOF
{
    "hasUpdate": false,
    "currentVersion": "$CURRENT_VERSION",
    "latestVersion": "$LATEST_VERSION",
    "checkedAt": "$(date -Iseconds)"
}
EOF
    exit 0
fi

log "发现新版本，开始升级..."

# 执行升级
npm install -g openclaw@latest 2>&1 | tee -a "$LOG_FILE"

# 重启 Gateway
log "重启 Gateway..."
openclaw gateway restart 2>&1 | tee -a "$LOG_FILE"

# 获取新版本
NEW_VERSION=$(openclaw --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

# 获取更新内容
log "获取更新内容..."
CHANGELOG=$(openclaw changelog 2>&1 | head -50 || echo "更新内容详见 https://github.com/openclaw/openclaw/releases")

# 保存结果（带更新标记，9 点通知脚本会读取）
cat > "$RESULT_FILE" << EOF
{
    "hasUpdate": true,
    "previousVersion": "$CURRENT_VERSION",
    "newVersion": "$NEW_VERSION",
    "updatedAt": "$(date -Iseconds)",
    "notified": false,
    "changelog": $(echo "$CHANGELOG" | jq -Rs '.')
}
EOF

log "升级完成：$CURRENT_VERSION → $NEW_VERSION"
log "=== 检查更新完成 ==="
