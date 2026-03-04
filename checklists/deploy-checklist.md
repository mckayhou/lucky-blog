# 部署检查清单

**来源：** ClawHub MVP 部署失败复盘 (2026-03-04)

---

## 部署前检查

### 1. 技术选型验证
- [ ] 读过平台文档，确认限制（SQLite？原生模块？）
- [ ] 数据库选择与平台兼容（Vercel → Neon/PostgreSQL，Railway → SQLite OK）
- [ ] 依赖包无平台兼容性问题

### 2. 本地验证
- [ ] 所有 API 端点本地测试通过
- [ ] 前端页面能正常访问
- [ ] 数据库连接正常
- [ ] 环境变量配置正确

### 3. Git 配置
- [ ] `git config user.email` 与部署平台账号一致
- [ ] `git remote -v` 指向正确仓库
- [ ] `.gitignore` 已配置（node_modules, .env, *.db）

### 4. 代码检查
- [ ] 路由顺序正确（API 路由 → 静态资源）
- [ ] 无硬编码本地路径
- [ ] 环境变量用 `process.env.XXX`
- [ ] Serverless 环境导出正确（`module.exports = app`）

---

## 部署流程

### Vercel
```bash
# 1. 检查 Git 配置
git config user.email

# 2. 提交代码
git add -A && git commit -m "..."

# 3. 部署
vercel --prod --yes

# 4. 设置环境变量（如需要）
vercel env add DATABASE_URL
```

### Railway
```bash
# 1. 登录
railway login

# 2. 初始化项目
railway init

# 3. 部署
railway up

# 4. 设置环境变量
railway variables set DATABASE_URL=xxx
```

### Render
```bash
# 通过 Dashboard 创建
# 1. New Web Service
# 2. 连接 GitHub 仓库
# 3. 配置环境变量
# 4. Deploy
```

---

## 故障排查

### 同样错误出现 2 次
→ 停止重试，分析根本原因

### 同样错误出现 3 次
→ 触发 Plan B，换平台

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `Exit handler never called` | Vercel npm bug | 换 Railway/Render |
| `404 Not Found` (API) | 路由顺序错误 | 静态资源放最后 |
| `Git author must have access` | Git 邮箱无权限 | 改 `git config user.email` |
| `Cannot find module 'better-sqlite3'` | 原生模块不兼容 | 换 PostgreSQL 或换平台 |

---

## 平台选择指南

| 需求 | 推荐平台 |
|------|----------|
| 纯前端/静态站点 | Vercel ⭐⭐⭐⭐⭐ |
| 无状态后端 API | Vercel ⭐⭐⭐⭐ |
| 需要 SQLite | Railway ⭐⭐⭐⭐⭐ / Render ⭐⭐⭐⭐ |
| 需要 PostgreSQL | Vercel + Neon ⭐⭐⭐⭐ / Railway ⭐⭐⭐⭐⭐ |
| Docker 部署 | Railway ⭐⭐⭐⭐⭐ / Render ⭐⭐⭐⭐ |
| 快速上线（5 分钟） | Railway ⭐⭐⭐⭐⭐ |

---

**最后更新：** 2026-03-04
