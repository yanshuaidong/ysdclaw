# OpenClaw 数据架构

## 数据流

```
Mac Mini (OpenClaw Agent)
  └─ ~/.openclaw/workspace/
       ├── data/reviews/YYYY-MM-DD.json   ← 每日复盘数据
       ├── IDENTITY.md, MEMORY.md, ...
       └── skills/, memory/, ...
            │
            │  rsync (每天 14:30 自动同步)
            ▼
服务器 82.157.138.214
  └─ /root/openclaw-workspace/            ← 同步目标
            │
            │  nginx 静态服务 (autoindex json)
            ▼
      /openclaw-data/*                    ← HTTP 路径
            │
            │  axios (前端) / vite proxy (开发环境)
            ▼
      前端组件 (ProductBrowse.vue 等)
```

## 关键配置

### Nginx (`deploy/nginx.conf`)

```nginx
location /openclaw-data/ {
    alias /root/openclaw-workspace/;
    autoindex on;
    autoindex_format json;
    add_header Cache-Control "no-cache";
    add_header Access-Control-Allow-Origin *;
}
```

- `autoindex on` + `autoindex_format json`：访问目录时返回 JSON 格式的文件列表
- `Cache-Control: no-cache`：确保每次获取最新数据

### Vite 开发代理 (`frontend/vite.config.ts`)

```typescript
'/openclaw-data': {
  target: 'http://82.157.138.214',
  changeOrigin: true,
}
```

开发环境下请求 `/openclaw-data/*` 会代理到服务器，与生产环境行为一致。

## 前端通用工具 (`frontend/src/api/openclaw.ts`)

独立的 axios 实例，不经过 auth 拦截器，提供三个函数：

| 函数 | 用途 | 示例 |
|------|------|------|
| `listDir(path)` | 列出目录文件 | `listDir('data/reviews')` |
| `fetchJson<T>(path)` | 获取 JSON 文件 | `fetchJson('data/reviews/2026-03-25.json')` |
| `fetchText(path)` | 获取文本文件 | `fetchText('MEMORY.md')` |

### listDir 返回格式

nginx autoindex json 返回的数组结构：

```json
[
  { "name": "2026-03-25.json", "type": "file", "mtime": "Tue, 25 Mar 2026 12:16:00 GMT", "size": 1879 },
  { "name": "subdir", "type": "directory", "mtime": "..." }
]
```

## 每日复盘数据格式 (`data/reviews/YYYY-MM-DD.json`)

```json
{
  "date": "2026-03-25",
  "time": "20:00:00",
  "market_data": {
    "open": null, "high": null, "low": null,
    "close": 4.536, "volume": 7080000, "change_pct": 1.27
  },
  "trade_plan": "...",
  "actual_result": "...",
  "operation": { "action": "hold|buy|sell", "quantity": 0, "price": null },
  "account": {
    "cash": 8596.90,
    "position": 300,
    "position_value": 1360.80,
    "total_asset": 9957.70,
    "unrealized_pnl": -42.30,
    "unrealized_pnl_pct": -3.01
  },
  "good": ["..."],
  "improve": ["..."],
  "lessons": ["..."],
  "next_actions": ["..."],
  "scores": {
    "decision_quality": 4,
    "execution_discipline": 5,
    "risk_control": 3
  }
}
```

## 前端数据映射 (`ProductBrowse.vue`)

| 展示字段 | 数据来源（最新 review） |
|----------|------------------------|
| 总资产 | `account.total_asset` |
| 可用资金 | `account.cash` |
| 持仓市值 | `account.position_value` |
| 持仓数量 | `account.position` |
| 持仓均价 | `(position_value - unrealized_pnl) / position` |
| 交易记录 | 所有 `operation.action !== 'hold'` 的 review |
| 总资产走势 | 每日 `account.total_asset` 构成折线图 |

## 扩展方式

新增数据展示只需两步：

1. Mac Mini 生成文件到 `~/.openclaw/workspace/` 下任意路径 → rsync 自动同步到服务器
2. 前端用 `listDir` + `fetchJson` / `fetchText` 直接读取，无需改后端或 nginx
