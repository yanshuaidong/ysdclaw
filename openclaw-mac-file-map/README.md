# 这个文件夹是用来做“路径映射表”的

它会把你 Mac mini 上某个目录（默认是 `~/.openclaw/workspace`）里的**所有非隐藏文件**（名字不以 `.` 开头）扫描出来，然后生成一张表：

- `Mac Path`：文件在 Mac mini 上的路径
- `Server Path`：文件映射到服务器磁盘上的路径
- `URL`：这个文件在服务器上通过 HTTP 能访问的 URL

## 目录里一共 4 个文件

1. `generate_table.py`（脚本）
   - 从 `env.env` 读取连接配置（IP/账号/密码等）
   - 用 SSH/SFTP 连接到你的 Mac mini
   - 递归扫描 `MAC_BASE_DIR` 指定的目录
   - 忽略隐藏项（文件/目录名以 `.` 开头）
   - 输出结果到 `table.md`（Markdown 表格）

2. `table.md`（内容文件）
   - 脚本运行后生成/覆盖
   - Markdown 表格列包含：`Mac Path`、`Server Path`、`URL`

3. `README.md`（说明）
   - 解释这个文件夹每个文件是干什么的

4. `env.env`（环境文件，敏感信息）
   - 存放你的 Mac mini 连接信息，以及“本地目录 -> 服务器目录 -> URL”的映射参数
   - 注意：这个文件包含敏感信息，不要发到公网/提交到仓库

## 运行方式（在你的 Windows 机器上）
1. 确认已安装 `python`
2. 安装依赖：
   - `python -m pip install paramiko`
3. 运行脚本：
   - `python generate_table.py`

## 你可能需要改的配置
- `env.env` 里的 `MAC_BASE_DIR`
  - 控制要扫描 Mac mini 上哪个目录
- `env.env` 里的 `SERVER_ROOT_DIR` 和 `SERVER_URL_BASE`
  - 必须跟你服务器 nginx 的映射关系一致，生成的 `Server Path` 和 `URL` 才会正确

