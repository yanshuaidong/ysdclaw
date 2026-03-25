# openclaw-mac-file-map 使用说明

这个说明用于指导如何使用项目里的 `openclaw-mac-file-map/` 工具，把 **Mac mini 上的文件路径** 映射为 **服务器磁盘路径** 和 **可通过 URL 访问的路径**，最后输出为 `openclaw-mac-file-map/table.md`（已在根目录 `.gitignore` 中忽略，避免上传隐私/内部路径信息）。

该映射规则以 `doc/openclaw数据架构.md` 中的 HTTP 路径约定为准：服务器通过 nginx 把 `/openclaw-data/` 映射到磁盘目录 `/root/openclaw-workspace/`。

文档联动：
- 请先阅读：`doc/openclaw数据架构.md`（重点看其中的 `/openclaw-data/*` HTTP 路径与 `alias /root/openclaw-workspace/;` 的对应关系）。

## 1. 工具目录有什么

`openclaw-mac-file-map/` 下目前 4 个文件：

- `generate_table.py`：脚本，SSH 连接到 Mac mini，递归扫描目录，生成表格
- `table.md`：输出的 Markdown 表格（包含 Mac 路径、服务器路径、URL）
- `README.md`：这个目录的说明
- `env.env`：环境配置/敏感信息（IP、账号、密码、以及映射参数）

## 2. 准备条件

在你的 Windows/开发机上：

1. 安装 Python
2. 安装脚本依赖：
   - `python -m pip install paramiko`

## 3. 配置 env.env（关键）

打开 `openclaw-mac-file-map/env.env`，重点确认/填写：

- `MAC_HOST` / `MAC_PORT`：Mac mini 地址与端口
- `MAC_USER` / `MAC_PASS`：Mac mini 账号/密码
- `MAC_BASE_DIR`：要扫描的 Mac mini 目录（默认 `~/.openclaw/workspace`）
- `SERVER_ROOT_DIR`：服务器磁盘目录（默认 `/root/openclaw-workspace`）
- `SERVER_URL_BASE`：浏览器访问的 URL 基础路径（默认 `http://82.157.138.214/openclaw-data`）

其中 `SERVER_ROOT_DIR` 与 `SERVER_URL_BASE` 必须与 `doc/openclaw数据架构.md` 和 `deploy/nginx.conf` 的 nginx `alias` 配置一致，才能保证 `table.md` 里的 URL 能正确访问到对应文件。

## 4. 运行脚本生成表格

在 `openclaw-mac-file-map/` 目录下运行：

- `python generate_table.py`

运行完成后，输出文件会写到：
- `openclaw-mac-file-map/table.md`

表格含义：
- `Mac Path`：文件在 Mac mini 上的绝对路径
- `Server Path`：文件在服务器磁盘上的绝对路径（由 `SERVER_ROOT_DIR` + 相对路径推导）
- `URL`：文件在服务器上可 HTTP 访问的路径（由 `SERVER_URL_BASE` + 相对路径推导）

## 5. 输出表格怎么用（例子）

例如表格中某一行给出：

- `Mac Path`：`~/.openclaw/workspace/skills/xxx/operation.json`
- `Server Path`：`/root/openclaw-workspace/skills/xxx/operation.json`
- `URL`：`http://82.157.138.214/openclaw-data/skills/xxx/operation.json`

那么你在前端（或浏览器）里请求这个 `URL`，就能拿到对应 JSON/文本内容。

## 6. 注意事项

1. `table.md` 里会出现路径/URL 映射信息（可能包含内部结构），所以已经加入根目录 `.gitignore` 忽略，避免误提交到 git。
2. 脚本会忽略“隐藏文件/目录”（文件名以 `.` 开头的项），因此不会把 `~/.openclaw/workspace/.xxx` 这类条目输出到表格里。
3. `MAX_DEPTH` 过小可能导致扫描不全；过大则会扫描更深，耗时更长。

