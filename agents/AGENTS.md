# Agent 军团配置

**架构:** 双层 Prompt + 多 Agent 协作 + Self-Review 进化  
**版本:** v1.0  
**最后更新:** 2026-03-03

---

## 军团成员

| Agent | 角色 | 专长 | 绑定模型 | 状态 |
|-------|------|------|---------|------|
| Alpha | 首席技术官 | 复杂系统、性能优化 | `glm-5` | ✅ 就绪 |
| Bravo | 首席分析师 | 代码审查、风险分析 | `glm-5` | ✅ 就绪 |
| Charlie | 首席战略官 | 方案设计、战略规划 | `qwen3.5-plus` | ✅ 就绪 |
| Delta | 首席工程师 | Bug 修复、文档测试 | `glm-5` | ✅ 就绪 |
| Echo | 首席情报官 | 情报收集、调研分析 | `qwen3.5-plus` | ✅ 就绪 |

**模型分配原则：**
- 代码/架构任务（Alpha/Bravo/Delta）→ `glm-5`
- 文本/思考任务（Charlie/Echo）→ `qwen3.5-plus`
- 图像/视频理解 → `kimi-k2.5` → Fallback `qwen3.5-plus`

---

## 通信协议

### @呼叫格式
```
@agent_id [指令内容]
```

### 并行协作
- 最大并发：10 任务
- Session 复用：sessionKey 固定
- 结果汇总：调度员统一输出

### 冲突解决
- 优先级：Alpha > Bravo > Charlie > Delta > Echo
- 平票：调度员裁决

---

## Self-Review 记录

_任务结束后自动追加_

---

## vNext 进化建议

_从 Self-Review 中自动提取_

## 2026-03-03T13:00:38.181615
- Agent: Echo
- Task: 测试任务
- Status: ✅
