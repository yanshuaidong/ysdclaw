# 后端接口文档（FastAPI）

服务地址与文档：

- Base URL：`http://127.0.0.1:8000`
- Swagger UI：`http://127.0.0.1:8000/docs`
- 健康检查：`GET /api/health`

## 鉴权方式（Bearer JWT）

需要鉴权的接口均使用 `Authorization` 头携带 JWT：

- Header：`Authorization: Bearer <access_token>`
- JWT 签名算法：`HS256`
- `get_current_user` 解码要求：
  - `sub`：用户 ID（字符串，最终会转换为 `int`）
  - `role`：由数据库用户的 `role` 再次校验是否为管理员
- 默认过期时间（配置项）：`ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24`（24 小时）

> 管理员接口需要 `role == "admin"`，否则返回 `403`。

## 接口一览（表格）


| 分组   | 方法       | 路径                     | 鉴权        | 入参（请求体/参数）                                             | 出参（响应体）                                                         | 成功状态码 | 常见错误码/消息                                      |
| ---- | -------- | ---------------------- | --------- | ------------------------------------------------------ | --------------------------------------------------------------- | ----- | --------------------------------------------- |
| 健康检查 | `GET`    | `/api/health`          | 否         | 无                                                      | `{"status":"ok"}`                                               | `200` | 无                                             |
| 认证   | `POST`   | `/api/auth/login`      | 否         | `LoginRequest`：`username`, `password`                  | `Token`：`access_token`, `token_type`                            | `200` | `401`：`用户名或密码错误`                              |
| 认证   | `GET`    | `/api/auth/me`         | 是（Bearer） | 无                                                      | `UserOut`：`id`, `username`, `role`, `created_at`, `updated_at?` | `200` | `401`：`无效的认证凭据` / `用户不存在`                     |
| 用户管理 | `GET`    | `/api/users`           | 是（admin）  | `skip`(默认`0`), `limit`(默认`100`)                        | `UserOut[]`                                                     | `200` | `401`：鉴权失败；`403`：`需要管理员权限`                    |
| 用户管理 | `POST`   | `/api/users`           | 是（admin）  | `UserCreate`：`username`, `password`, `role?(默认"user")` | `UserOut`                                                       | `201` | `400`：`用户名已存在`；`401`/`403`：鉴权失败               |
| 用户管理 | `PUT`    | `/api/users/{user_id}` | 是（admin）  | `UserUpdate`（全字段可选）：`username?`, `password?`, `role?`  | `UserOut`                                                       | `200` | `404`：`用户不存在`；`401`/`403`：鉴权失败                |
| 用户管理 | `DELETE` | `/api/users/{user_id}` | 是（admin）  | 路径参数：`user_id`                                         | `{"detail":"删除成功"}`                                             | `200` | `400`：`不能删除自己`；`404`：`用户不存在`；`401`/`403`：鉴权失败 |

| 模拟交易 | `POST`   | `/api/simulations/equity-curve` | 否 | `EquityCurveRequest`：见下文 | `EquityCurveResponse`：见下文 | `200` | `500`：AkShare/数据处理异常（`{"detail":"..."}`） |


## 模拟交易：净值曲线

### `POST /api/simulations/equity-curve`

用途：基于交易记录（买卖流水）与 AkShare 日线收盘价，生成“每日总资产曲线（equity curve）”与“交易标记（trade markers）”。前端用于绘制净值曲线与在 tooltip 里显示买卖点。

鉴权：否（当前路由未加登录/管理员依赖）。

请求体：`EquityCurveRequest`

- `stock_code`（string，必填）：标的代码（兼容字段；当前前端使用该字段）。ETF 示例 `510300`；指数示例可传 `sh000001`/`sz399001`（也支持只传 6 位，服务端会尽力补全）。
- `instrument_type`（`"etf" | "stock" | "index"`，可选，默认 `"etf"`）：标的类型。
- `initial_capital`（number，必填，>0）：初始资金，如 `10000`。
- `operations`（array，必填）：交易流水（会在服务端按 `stock_code` 过滤并按 `timestamp` 排序）。
  - `type`：`"buy"` 或 `"sell"`
  - `stock_code`：代码（建议与请求 `stock_code` 一致）
  - `stock_name`：名称
  - `price`：成交价
  - `quantity`：成交数量
  - `total_amount`：成交金额（用于调整现金）
  - `timestamp`：`"YYYY-MM-DD HH:mm:ss"`
- `adjust`（string，可选，默认 `"qfq"`）：复权参数（用于 A 股/ETF 的 AkShare hist 接口）。
- `days_back`（int，可选，默认 `120`）：向前补足交易日的缓冲天数（覆盖节假日/缺失数据，便于将交易日期对齐到最近交易日）。

响应体：`EquityCurveResponse`

- `stock_code`：请求的标的代码
- `start_date` / `end_date`：曲线点的起止日期（`YYYY-MM-DD`）
- `points`：按交易日的曲线点（每日一条）
  - `date`：`YYYY-MM-DD`
  - `total_assets`：总资产（现金 + 持仓数量 × 当日收盘价）
  - `cash`：现金
  - `market_value`：持仓市值
  - `position_quantity`：持仓数量
  - `close_price`：当日收盘价
  - `nav`：净值（`total_assets / initial_capital`）
- `trade_markers`：交易标记（把每一笔操作对齐到“第一个交易日 >= 操作日期”的点上）
  - `date`：对齐后的交易日（与 `points[].date` 对齐）
  - `total_assets_at_marker`：标记所在日对应的总资产（用于 ECharts `markPoint`）
  - 其余字段与 `operations` 基本一致

请求示例：

```json
{
  "stock_code": "510300",
  "instrument_type": "etf",
  "initial_capital": 10000,
  "operations": [
    {
      "type": "buy",
      "stock_code": "510300",
      "stock_name": "华泰柏瑞沪深300ETF",
      "price": 3.651,
      "quantity": 1000,
      "total_amount": 3651,
      "timestamp": "2025-01-02 10:01:00"
    }
  ],
  "adjust": "qfq",
  "days_back": 120
}
```

响应示例（节选）：

```json
{
  "stock_code": "510300",
  "start_date": "2025-01-02",
  "end_date": "2025-03-25",
  "points": [
    {
      "date": "2025-01-02",
      "total_assets": 10012.34,
      "cash": 6349,
      "market_value": 3663.34,
      "position_quantity": 1000,
      "close_price": 3.66334,
      "nav": 1.001234
    }
  ],
  "trade_markers": [
    {
      "date": "2025-01-02",
      "type": "buy",
      "timestamp": "2025-01-02 10:01:00",
      "stock_code": "510300",
      "stock_name": "华泰柏瑞沪深300ETF",
      "price": 3.651,
      "quantity": 1000,
      "total_amount": 3651,
      "total_assets_at_marker": 10012.34
    }
  ]
}
```

## 错误返回格式

FastAPI/HTTPException 的错误响应通常为：

- `{"detail":"错误消息"}`

如果发生未捕获异常（500），全局异常处理会返回：

- `{"detail":"<异常字符串>"}`（同时会在后端记录日志）

