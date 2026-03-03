# Notion → GitHub → Vercel 同步

基于 Claude SRE Agent 和 ClawRouter 架构设计的自动同步系统。

## 🚀 快速开始

### 1. 获取 Notion API Key

1. 访问 https://notion.so/my-integrations
2. 点击 **+ New integration**
3. 选择关联的 Workspace
4. 复制 **Internal Integration Token**（`ntn_` 开头）

### 2. 获取 Notion Database ID

1. 打开要同步的 Database
2. 点击 `⋯⋯` → **Copy link**
3. URL 格式：`https://notion.so/your-workspace/DATABASE_ID?v=xxx`
4. 复制 `DATABASE_ID` 部分

### 3. 配置环境变量

```bash
# 编辑 ~/.openclaw/openclaw.json 或在 Gateway 配置
export NOTION_API_KEY="ntn_xxxxxxxxxxxxxxxxxxxxx"
export NOTION_DATABASE_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export VERCEL_TOKEN="vcp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 4. 运行同步

```bash
cd /root/.openclaw/workspace/notion-sync
python3 sync.py
```

## 📋 MCP 工具

| 工具 | 说明 |
|------|------|
| `notion_query_database` | 查询 Notion 数据库 |
| `notion_get_page` | 获取页面内容 |
| `notion_export_markdown` | 导出为 Markdown |
| `github_commit_file` | 提交到 GitHub |
| `vercel_deploy` | 触发 Vercel 部署 |
| `validate_content` | 验证内容格式 |
| `sync_status` | 查看同步状态 |

## 🔒 安全护栏

- **目录限制**：只能提交到 `posts/` 目录
- **状态过滤**：只同步 Status = "published" 的页面
- **内容验证**：部署前验证 HTML/Markdown 格式
- **幂等操作**：重复运行不会重复提交

## 📅 定时同步（可选）

添加 cron 任务：

```bash
# 每小时同步一次
0 * * * * cd /root/.openclaw/workspace/notion-sync && python3 sync.py >> /var/log/notion-sync.log 2>&1
```

## 🎯 同步流程

```
Notion Database
      │
      ▼
┌─────────────────┐
│  Query Pages    │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Export Markdown │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Validate Content│
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Commit to GitHub│
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Vercel Deploy   │ (auto)
└─────────────────┘
```

## 📝 Notion Database 模板

建议 Database 包含以下属性：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 文章标题 |
| Status | Select | 状态（published/draft） |
| Tags | Multi-select | 标签 |
| Published | Date | 发布日期 |

## 🔧 故障排除

**Q: 同步失败**
```bash
# 检查环境变量
echo $NOTION_API_KEY
echo $NOTION_DATABASE_ID

# 测试 Notion API
curl -X POST "https://api.notion.com/v1/databases/YOUR_DB_ID/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"page_size": 1}'
```

**Q: GitHub 推送失败**
- 检查 Token 权限（需要 `repo` 权限）
- 确认仓库名称正确

**Q: Vercel 没有自动部署**
- 检查 Vercel 项目是否关联 GitHub
- 确认 webhook 已启用

## 📚 参考

- [Claude SRE Agent Cookbook](https://platform.claude.com/cookbook/claude-agent-sdk-03-the-site-reliability-agent)
- [ClawRouter GitHub](https://github.com/blockrunai/clawrouter)
- [Notion API Docs](https://developers.notion.com)
