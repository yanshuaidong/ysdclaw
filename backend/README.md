# ysdclaw 后端

FastAPI + MySQL 管理后台 API，默认监听 `8000` 端口。

## 快速启动

```bash
cd backend
python start.py          # 首次会自动创建虚拟环境并安装依赖
python start.py --init   # 加 --init 会先初始化数据库（建表 + 创建默认管理员 admin/admin123）
```

脚本会自动完成以下检查：

1. **Python 版本** — 需要 >= 3.8
2. **虚拟环境** — 不存在则自动创建 `.venv`，并切换到 `.venv` 内的解释器重新执行
3. **依赖安装** — 自动 `pip install -r requirements.txt`
4. **`.env` 配置** — 检查项目根目录 `.env` 是否存在且包含所有必需变量
5. **数据库连接** — 测试 MySQL 是否可达
6. **启动服务** — `uvicorn app.main:app --reload`

## 环境变量

后端从**项目根目录**的 `.env` 读取配置（不是 `backend/.env`）。必需变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DB_HOST` | MySQL 主机地址 | `rm-xxx.mysql.rds.aliyuncs.com` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | 数据库用户名 | `ysd` |
| `DB_PASSWORD` | 数据库密码 | |
| `DB_NAME` | 数据库名 | `ysdclaw` |
| `SECRET_KEY` | JWT 签名密钥 | 任意复杂字符串 |

## 项目结构

```
backend/
├── start.py              # 一键启动脚本（跨平台）
├── init_db.py            # 数据库初始化（建表 + 默认管理员）
├── requirements.txt
└── app/
    ├── main.py           # FastAPI 入口
    ├── config.py          # 环境变量 & 常量
    ├── database.py        # SQLAlchemy 引擎 & Session
    ├── dependencies.py    # 鉴权依赖（get_current_user / require_admin）
    ├── models/
    │   └── user.py        # User ORM 模型
    ├── schemas/
    │   └── user.py        # Pydantic 请求/响应模型
    ├── routers/
    │   ├── auth.py        # POST /api/auth/login  GET /api/auth/me
    │   └── user.py        # CRUD /api/users
    └── services/
        └── user.py        # 业务逻辑 & 密码工具
```

## API 概览

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/health` | 健康检查 | 无 |
| POST | `/api/auth/login` | 登录，返回 JWT | 无 |
| GET | `/api/auth/me` | 当前用户信息 | 登录 |
| GET | `/api/users` | 用户列表 | 管理员 |
| POST | `/api/users` | 创建用户 | 管理员 |
| PUT | `/api/users/{id}` | 修改用户 | 管理员 |
| DELETE | `/api/users/{id}` | 删除用户 | 管理员 |

交互式文档: 启动后访问 `http://127.0.0.1:8000/docs`
