# ysdclaw
个人项目

项目结构总览：

backend/ -- FastAPI 后端（Python 3.11）

app/main.py -- 应用入口
app/config.py -- 读取 .env 环境变量（阿里云 MySQL 配置）
app/database.py -- SQLAlchemy 数据库引擎
app/models/user.py -- 用户数据模型
app/schemas/user.py -- Pydantic 请求/响应模型
app/routers/auth.py -- 登录 + 获取当前用户 API
app/routers/user.py -- 用户 CRUD API（仅管理员）
app/services/user.py -- 业务逻辑层
app/dependencies.py -- JWT 认证 + 角色权限校验
init_db.py -- 数据库建表 + 创建默认管理员（admin/admin123）
requirements.txt -- Python 依赖
frontend/ -- Vue3 + Vite + Element Plus + TypeScript

src/views/Login.vue -- 登录页
src/views/UserManagement.vue -- 用户管理页（管理员专属，完整 CRUD）
src/views/ProductBrowse.vue -- 商品数据浏览（占位页面）
src/layouts/DashboardLayout.vue -- 管理后台布局（侧边栏按角色动态显示）
src/stores/auth.ts -- Pinia 认证状态管理
src/router/index.ts -- 路由 + 权限守卫
dist/ -- 已打包好的静态文件
deploy/ -- 部署相关

nginx.conf -- Nginx 配置（静态文件 + API 反向代理）
deploy.sh -- 一键部署脚本
接下来你需要做的：

在项目根目录创建 .env 文件，填入你的阿里云 MySQL 连接信息：
DB_HOST=你的阿里云MySQL地址
DB_PORT=3306
DB_USER=用户名
DB_PASSWORD=密码
DB_NAME=ysdclaw
SECRET_KEY=随便写一个复杂字符串
本地测试后端（先在阿里云 MySQL 中建好 ysdclaw 数据库）：
cd backend
pip3 install -r requirements.txt
python3 init_db.py          # 建表 + 创建 admin 账户
uvicorn app.main:app --reload  # 启动后端
本地测试前端（另开终端）：
cd frontend
npm run dev                 # Vite 会自动代理 /api 到 8000 端口
部署到服务器时：git push → 服务器 git pull → 创建 .env → bash deploy/deploy.sh
