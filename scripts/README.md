# OpenClaw 自动更新系统

## 概述

自动检查 OpenClaw 更新并发送通知的脚本系统。

## 脚本说明

### auto-update.sh
- **功能**: 检查 OpenClaw 更新并自动升级
- **执行时间**: 每 2 天早上 4:00
- **日志**: `/root/.openclaw/workspace/logs/auto-update.log`
- **状态文件**: `/root/.openclaw/workspace/state/update-result.json`

### update-notify.sh
- **功能**: 发送更新结果通知到飞书
- **执行时间**: 每天早上 9:00
- **日志**: `/root/.openclaw/workspace/logs/update-notify.log`

## Cron 配置

```bash
# 每 2 天早上 4 点检查更新
0 4 */2 * * /root/.openclaw/workspace/scripts/auto-update.sh

# 每天早上 9 点发送通知
0 9 * * * /root/.openclaw/workspace/scripts/update-notify.sh
```

## 手动测试

```bash
# 测试更新检查
/root/.openclaw/workspace/scripts/auto-update.sh

# 测试通知发送
/root/.openclaw/workspace/scripts/update-notify.sh
```

## 查看日志

```bash
# 更新检查日志
tail -f /root/.openclaw/workspace/logs/auto-update.log

# 通知发送日志
tail -f /root/.openclaw/workspace/logs/update-notify.log

# 查看更新结果
cat /root/.openclaw/workspace/state/update-result.json
```

## 消息格式

### 无更新时
```
🦞 OpenClaw 自动更新检查

✅ 已是最新版本

当前版本：2026.3.2
检查时间：2026-03-03 04:00
```

### 有更新时
```
🦞 OpenClaw 自动更新完成

✅ 升级成功

升级前：2026.3.1
升级后：2026.3.2
升级时间：2026-03-03 04:00

查看详细更新内容：
https://github.com/openclaw/openclaw/releases
```

## 配置修改

### 修改检查频率
编辑 crontab:
```bash
crontab -e
```

修改第一行的 cron 表达式。

### 修改通知接收人
编辑 `update-notify.sh`, 修改 `--target` 参数的飞书 open_id。

---

**创建时间**: 2026-03-03  
**版本**: 1.0.0
