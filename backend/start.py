#!/usr/bin/env python3
"""
ysdclaw 后端本地启动脚本 — 兼容 Windows / macOS / Linux
用法:  python start.py          正常启动
       python start.py --init   先初始化数据库再启动
"""

import importlib
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from typing import List

# ────────────────────────────── paths ──────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
VENV_DIR = os.path.join(BACKEND_DIR, ".venv")
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")
REQUIREMENTS = os.path.join(BACKEND_DIR, "requirements.txt")

REQUIRED_PYTHON = (3, 8)
REQUIRED_ENV_VARS = [
    "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "SECRET_KEY",
]

IS_WIN = platform.system() == "Windows"
VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe") if IS_WIN else os.path.join(VENV_DIR, "bin", "python")
VENV_PIP = os.path.join(VENV_DIR, "Scripts", "pip.exe") if IS_WIN else os.path.join(VENV_DIR, "bin", "pip")


# ────────────────────────────── helpers ────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
if IS_WIN:
    os.system("")  # enable ANSI on Windows 10+
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except Exception:
            pass


def ok(msg: str):
    print(f"  {GREEN}✔{RESET} {msg}")


def warn(msg: str):
    print(f"  {YELLOW}⚠{RESET} {msg}")


def fail(msg: str):
    print(f"  {RED}✘{RESET} {msg}")


def fatal(msg: str):
    fail(msg)
    sys.exit(1)


def heading(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def run(cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, **kwargs)


# ────────────────────────── 1. Python 版本 ─────────────────────────
def check_python():
    heading("检查 Python 版本")
    v = sys.version_info
    ver = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) < REQUIRED_PYTHON:
        fatal(f"Python {ver} 不满足最低要求 {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}，请升级")
    ok(f"Python {ver}  ({sys.executable})")


# ────────────────────────── 2. 虚拟环境 ────────────────────────────
def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


def ensure_venv():
    heading("检查虚拟环境")

    if not os.path.isdir(VENV_DIR):
        warn("虚拟环境不存在，正在创建 .venv ...")
        run([sys.executable, "-m", "venv", VENV_DIR], check=True)
        ok("虚拟环境创建完成")
    else:
        ok(f"虚拟环境已存在  ({VENV_DIR})")

    if not in_venv():
        ok("重新使用 .venv 解释器执行本脚本 ...")
        if IS_WIN:
            # Windows: use os.execv-like behavior via subprocess with proper
            # signal forwarding so Ctrl+C reaches the child process.
            proc = subprocess.Popen(
                [VENV_PYTHON, __file__] + sys.argv[1:],
                creationflags=0,  # share console → Ctrl+C reaches child
            )
            try:
                sys.exit(proc.wait())
            except KeyboardInterrupt:
                proc.wait()
                sys.exit(0)
        else:
            os.execv(VENV_PYTHON, [VENV_PYTHON, __file__] + sys.argv[1:])


# ────────────────────────── 3. 依赖安装 ────────────────────────────
def ensure_deps():
    heading("检查依赖")
    if not os.path.isfile(REQUIREMENTS):
        fatal(f"找不到 {REQUIREMENTS}")

    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"], check=True)
    result = run(
        [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS, "-q"],
    )
    if result.returncode != 0:
        fatal("依赖安装失败，请检查网络或 requirements.txt")
    ok("依赖已安装")


# ────────────────────────── 4. .env 文件 ───────────────────────────
def check_env():
    heading("检查 .env 配置")
    if not os.path.isfile(ENV_FILE):
        example = os.path.join(PROJECT_ROOT, ".env.example")
        if os.path.isfile(example):
            shutil.copy2(example, ENV_FILE)
            warn(f"已从 .env.example 复制到 .env，请填写实际配置后重新运行")
            sys.exit(1)
        else:
            fatal(f"缺少 {ENV_FILE}，请参考 .env.example 创建")

    from dotenv import dotenv_values
    values = dotenv_values(ENV_FILE)

    missing = [k for k in REQUIRED_ENV_VARS if not values.get(k)]
    if missing:
        fatal(f".env 中缺少以下配置项: {', '.join(missing)}")
    ok(".env 配置完整")


# ────────────────────────── 5. 数据库连通 ──────────────────────────
def check_db():
    heading("检查数据库连接")
    try:
        import pymysql
        from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
            connect_timeout=5,
        )
        conn.close()
        ok(f"MySQL 连接正常  ({DB_USER}@{DB_HOST}:{DB_PORT})")
    except Exception as e:
        fatal(f"数据库连接失败: {e}")


# ────────────────────────── 6. 初始化数据库 ────────────────────────
def init_db():
    heading("初始化数据库（建表 + 默认管理员）")
    result = run([sys.executable, os.path.join(BACKEND_DIR, "init_db.py")])
    if result.returncode != 0:
        fatal("数据库初始化失败")
    ok("数据库初始化完成")


# ────────────────────────── 7. 启动服务 ────────────────────────────
def start_server():
    heading("启动 FastAPI 开发服务器")
    print(f"  地址: http://127.0.0.1:8000")
    print(f"  文档: http://127.0.0.1:8000/docs")
    print(f"  健康: http://127.0.0.1:8000/api/health")
    print(f"  按 Ctrl+C 停止\n")

    os.chdir(BACKEND_DIR)
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )
    except KeyboardInterrupt:
        print("\n服务已停止")


# ────────────────────────── main ──────────────────────────────────
def main():
    print(f"\n{'═' * 50}")
    print(f"    ysdclaw 后端启动脚本")
    print(f"    系统: {platform.system()} {platform.release()}")
    print(f"{'═' * 50}")

    do_init = "--init" in sys.argv

    check_python()
    ensure_venv()
    ensure_deps()
    check_env()
    check_db()

    if do_init:
        init_db()

    start_server()


if __name__ == "__main__":
    main()
