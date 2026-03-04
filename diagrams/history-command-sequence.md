# OpenClaw `/history` 命令时序图 - 双模式对比

## 完整时序图（合并对比）

```mermaid
sequenceDiagram
    autonumber
    box "用户端" #f0f0f0
        participant UF as 👤 用户（飞书）
        participant UT as 👤 用户（Telegram）
    end
    
    box "OpenClaw Gateway（单进程）" #e8f4f8
        participant CA as Channel Adapter
        participant GW as Gateway
        participant SM as Session Manager
        participant ST as 📁 Session 存储（JSONL）
    end
    
    participant LLM as 🤖 外部 LLM API

    %% ============ 场景1：飞书用户发送命令 ============
    rect rgb(230, 247, 255)
        note right of UF: 场景 A：飞书用户发送 /history
        UF->>CA: /history (channel=feishu, peer_id=user123)
        CA->>GW: 解析命令，提取 peer_id=user123
        GW->>SM: 请求 session 历史
    end
    
    %% 两种模式的分叉点 - 飞书
    alt per-peer 模式（共享 session）
        rect rgb(200, 255, 200)
            SM->>SM: 🔑 dmScope = peer_id<br/>key = "user123"
            note right of SM: ✅ 忽略 channel<br/>两个平台共享同一 session
        end
    else per-channel-peer 模式（独立 session）
        rect rgb(255, 230, 200)
            SM->>SM: 🔑 dmScope = channel:peer_id<br/>key = "feishu:user123"
            note right of SM: 🔒 包含 channel<br/>每个平台独立 session
        end
    end
    
    SM->>ST: 加载 session(key)
    ST-->>SM: 返回历史记录 JSONL
    
    alt per-peer 模式（有历史）
        rect rgb(200, 255, 200)
            SM-->>GW: ✅ 返回合并的历史（飞书+Telegram 混合）
            note right of SM: 包含另一平台的历史消息
        end
    else per-channel-peer 模式（独立历史）
        rect rgb(255, 230, 200)
            SM-->>GW: ✅ 返回该平台专属历史
            note right of SM: 仅飞书平台的历史
        end
    end
    
    GW->>LLM: 调用 LLM（带历史上下文）
    LLM-->>GW: 返回响应
    GW-->>CA: 格式化响应
    CA-->>UF: 返回历史记录摘要

    %% ============ 场景2：Telegram用户发送命令 ============
    rect rgb(255, 245, 230)
        note right of UT: 场景 B：Telegram 用户发送 /history
        UT->>CA: /history (channel=telegram, peer_id=user123)
        CA->>GW: 解析命令，提取 peer_id=user123
        GW->>SM: 请求 session 历史
    end
    
    %% 两种模式的分叉点 - Telegram
    alt per-peer 模式（共享 session）
        rect rgb(200, 255, 200)
            SM->>SM: 🔑 dmScope = peer_id<br/>key = "user123"
            note right of SM: ✅ 与飞书使用相同 key<br/>命中同一 session
        end
    else per-channel-peer 模式（独立 session）
        rect rgb(255, 230, 200)
            SM->>SM: 🔑 dmScope = channel:peer_id<br/>key = "telegram:user123"
            note right of SM: 🔒 与飞书使用不同 key<br/>独立 session
        end
    end
    
    SM->>ST: 加载 session(key)
    ST-->>SM: 返回历史记录 JSONL
    
    alt per-peer 模式
        rect rgb(200, 255, 200)
            SM-->>GW: ✅ 返回共享历史（飞书+Telegram）
            note right of SM: ⚠️ 飞书的对话也被加载
        end
    else per-channel-peer 模式
        rect rgb(255, 230, 200)
            SM-->>GW: ✅ 返回 Telegram 专属历史
            note right of SM: ✅ 仅 Telegram 平台历史
        end
    end
    
    GW->>LLM: 调用 LLM（带历史上下文）
    LLM-->>GW: 返回响应
    GW-->>CA: 格式化响应
    CA-->>UT: 返回历史记录摘要
```

---

## 简化版时序图（核心对比）

```mermaid
sequenceDiagram
    autonumber
    participant UF as 用户（飞书）
    participant UT as 用户（Telegram）
    participant GW as Gateway
    participant SM as Session Manager
    participant ST as Session 存储
    participant LLM as LLM API

    %% ===== 飞书命令 =====
    UF->>GW: /history (peer_id=A, channel=feishu)
    GW->>SM: getSessionHistory(peer_id=A)
    
    alt per-peer 模式
        SM->>SM: key = "A"
        note right of SM: 🟢 共享 key
    else per-channel-peer 模式
        SM->>SM: key = "feishu:A"
        note right of SM: 🟡 平台隔离 key
    end
    
    SM->>ST: load(key)
    ST-->>SM: history data
    SM-->>GW: 历史记录
    GW-->>UF: 响应
    
    %% ===== Telegram命令 =====
    UT->>GW: /history (peer_id=A, channel=telegram)
    GW->>SM: getSessionHistory(peer_id=A)
    
    alt per-peer 模式
        SM->>SM: key = "A"
        note right of SM: 🟢 命中同一 session
    else per-channel-peer 模式
        SM->>SM: key = "telegram:A"
        note right of SM: 🟡 独立 session
    end
    
    SM->>ST: load(key)
    ST-->>SM: history data
    
    alt per-peer 模式
        SM-->>GW: 共享历史（含飞书记录）
        note right of SM: ⚠️ 跨平台混合
    else per-channel-peer 模式
        SM-->>GW: Telegram 专属历史
        note right of SM: ✅ 平台隔离
    end
    
    GW-->>UT: 响应
```

---

## 关键差异点总结

| 维度 | per-peer 模式 | per-channel-peer 模式 |
|------|--------------|---------------------|
| **Session Key 计算** | `peer_id` | `channel:peer_id` |
| **飞书用户 key** | `user123` | `feishu:user123` |
| **Telegram 用户 key** | `user123` ✅ 相同 | `telegram:user123` ❌ 不同 |
| **历史记录** | 跨平台共享 | 平台独立隔离 |
| **上下文连贯性** | 高（但可能混乱） | 低（平台隔离） |
| **隐私性** | 低（跨平台泄露） | 高（平台隔离） |
| **适用场景** | 单平台用户 | 多平台用户 |

---

## 配置示例

```yaml
# per-peer 模式
session:
  dmScope: "peer"  # 仅按 peer_id 计算

# per-channel-peer 模式  
session:
  dmScope: "channel-peer"  # 按 channel + peer_id 计算
```

---

## 实现关键代码位置

```typescript
// Session Manager 中的 key 计算逻辑
function computeDmScope(channel: string, peerId: string, dmScope: string): string {
  switch (dmScope) {
    case 'peer':
      return peerId;  // 忽略 channel
    case 'channel-peer':
      return `${channel}:${peerId}`;  // 包含 channel
    default:
      return `${channel}:${peerId}`;
  }
}
```

---

## 视觉说明

- **🟢 绿色背景** - per-peer 模式的流程（共享 session）
- **🟡 橙色背景** - per-channel-peer 模式的流程（独立 session）
- **🔑** - Session key 计算的关键步骤
- **✅** - 优势点
- **⚠️** - 潜在问题/注意点