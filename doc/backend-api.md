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


## 错误返回格式

FastAPI/HTTPException 的错误响应通常为：

- `{"detail":"错误消息"}`

如果发生未捕获异常（500），全局异常处理会返回：

- `{"detail":"<异常字符串>"}`（同时会在后端记录日志）

