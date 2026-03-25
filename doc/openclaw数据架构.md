# OpenClaw 数据架构

## 数据流

```
Mac Mini (OpenClaw Agent)
  └─ ~/.openclaw/workspace/
       ├── skills/ysd-account/
       │     ├── account.json              ← 账户实时状态
       │     └── operation.json            ← 交易记录
       ├── skills/ysd-review/data/         ← 每日复盘（待启用）
       ├── IDENTITY.md, MEMORY.md, ...
       └── memory/, ...
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
| `listDir(path)` | 列出目录文件 | `listDir('skills/ysd-account')` |
| `fetchJson<T>(path)` | 获取 JSON 文件 | `fetchJson('skills/ysd-account/account.json')` |
| `fetchText(path)` | 获取文本文件 | `fetchText('MEMORY.md')` |

### listDir 返回格式

nginx autoindex json 返回的数组结构：

```json
[
  { "name": "account.json", "type": "file", "mtime": "Tue, 25 Mar 2026 12:16:00 GMT", "size": 1879 },
  { "name": "subdir", "type": "directory", "mtime": "..." }
]
```

## 账户数据格式 (`skills/ysd-account/account.json`)

```json
{
  "available_funds": 8596.90,
  "total_market_value": 1403.10,
  "total_assets": 10000.00,
  "positions": {
    "510300": {
      "name": "华泰柏瑞沪深300ETF",
      "quantity": 300,
      "avg_cost": 4.677
    }
  }
}
```

## 交易记录格式 (`skills/ysd-account/operation.json`)

```json
[
  {
    "type": "buy",
    "stock_code": "510300",
    "stock_name": "华泰柏瑞沪深300ETF",
    "price": 4.677,
    "quantity": 100,
    "total_amount": 467.70,
    "timestamp": "2026-03-13 18:43:51"
  }
]
```

## 前端数据映射 (`ProductBrowse.vue`)

| 展示字段 | 数据来源 |
|----------|----------|
| 总资产 | `account.json → total_assets` |
| 可用资金 | `account.json → available_funds` |
| 持仓市值 | `account.json → total_market_value` |
| 持仓数量 | `account.json → positions["510300"].quantity` |
| 持仓均价 | `account.json → positions["510300"].avg_cost` |
| 交易记录 | `operation.json` 完整数组 |
| 总资产走势 | 基于 `operation.json` 逐笔推算资产变化曲线 |

## 扩展方式

新增数据展示只需两步：

1. Mac Mini 生成文件到 `~/.openclaw/workspace/` 下任意路径 → rsync 自动同步到服务器
2. 前端用 `listDir` + `fetchJson` / `fetchText` 直接读取，无需改后端或 nginx
