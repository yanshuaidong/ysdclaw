import os
import sys
import stat
import posixpath
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import quote


def load_env(env_path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def ensure_paramiko():
    try:
        import paramiko  # noqa: F401
    except ImportError:
        raise SystemExit(
            "Missing dependency: paramiko\n"
            "Please run:\n"
            "  python -m pip install paramiko\n"
        )


def expand_remote_tilde(ssh, remote_path: str) -> str:
    # Expand '~' and '~/' to the remote $HOME.
    if remote_path == "~" or remote_path.startswith("~/"):
        stdin, stdout, stderr = ssh.exec_command("echo $HOME")
        home = stdout.read().decode("utf-8", errors="ignore").strip()
        if not home:
            raise RuntimeError("Could not determine remote $HOME")
        if remote_path == "~":
            return home
        return posixpath.join(home, remote_path[2:])
    return remote_path


def is_dir(st_mode: int) -> bool:
    return stat.S_ISDIR(st_mode)


def main() -> None:
    ensure_paramiko()
    import paramiko

    here = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(here, "env.env")
    out_md_path = os.path.join(here, "table.md")

    env = load_env(env_path)

    mac_host = env.get("MAC_HOST", "").strip()
    mac_port = int(env.get("MAC_PORT", "22").strip())
    mac_user = env.get("MAC_USER", "").strip()
    mac_pass = env.get("MAC_PASS", "").strip()
    mac_base_dir = env.get("MAC_BASE_DIR", "~/.openclaw/workspace").strip()

    server_root_dir = env.get("SERVER_ROOT_DIR", "/root/openclaw-workspace").strip().rstrip("/")
    server_url_base = env.get("SERVER_URL_BASE", "http://82.157.138.214/openclaw-data").strip().rstrip("/")

    max_depth = int(env.get("MAX_DEPTH", "50").strip())

    if not mac_host or not mac_user or not mac_pass:
        raise SystemExit("Missing MAC connection settings in env.env")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"[INFO] Connecting to {mac_host}:{mac_port} as {mac_user} ...")
    ssh.connect(hostname=mac_host, port=mac_port, username=mac_user, password=mac_pass, timeout=20)

    mac_base_dir_abs = expand_remote_tilde(ssh, mac_base_dir)
    mac_base_dir_abs_norm = posixpath.normpath(mac_base_dir_abs)

    print(f"[INFO] Scanning remote base directory: {mac_base_dir_abs_norm}")
    sftp = ssh.open_sftp()

    records: List[Dict[str, Any]] = []

    def walk(current: str, depth: int) -> None:
        if depth > max_depth:
            return

        try:
            items = sftp.listdir_attr(current)
        except FileNotFoundError:
            return

        for attr in items:
            name = getattr(attr, "filename", None)
            if not name:
                continue
            if name.startswith("."):
                continue

            full_path = posixpath.join(current, name)
            if is_dir(attr.st_mode):
                walk(full_path, depth + 1)
            else:
                rel = posixpath.relpath(full_path, mac_base_dir_abs_norm)
                rel = rel if rel != "." else ""
                server_path = server_root_dir + ("/" + rel if rel else "")
                url = server_url_base + ("/" + quote(rel, safe="/") if rel else "")

                records.append(
                    {
                        "mac_path": full_path,
                        "server_path": server_path,
                        "url": url,
                        "mtime": datetime.fromtimestamp(attr.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": int(getattr(attr, "st_size", 0)),
                    }
                )

    walk(mac_base_dir_abs_norm, 0)

    sftp.close()
    ssh.close()

    # Write markdown table
    records.sort(key=lambda r: r["mac_path"])
    lines: List[str] = []
    lines.append("| # | Mac Path | Server Path | URL |")
    lines.append("|---:|---|---|---|")

    for i, r in enumerate(records, start=1):
        mac_path = r["mac_path"].replace("|", "\\|")
        server_path = r["server_path"].replace("|", "\\|")
        url = r["url"].replace("|", "\\|")
        lines.append(f"| {i} | `{mac_path}` | `{server_path}` | `{url}` |")

    if not records:
        lines.append("| 0 | (no non-hidden files found) | - | - |")

    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[INFO] Done. Wrote {len(records)} rows to: {out_md_path}")


if __name__ == "__main__":
    main()

