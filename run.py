#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
APP_MODULE = "app.main:app"


def check_uv():
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ uv 已安装: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ uv 未安装，请先安装 uv:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("  或者访问: https://docs.astral.sh/uv/getting-started/installation/")
        return False


def check_dependencies():
    print("检查依赖...")
    venv_dir = PROJECT_DIR / ".venv"
    
    if not venv_dir.exists():
        print("创建虚拟环境并安装依赖...")
        subprocess.run(["uv", "sync"], cwd=PROJECT_DIR, check=True)
        print("✓ 依赖安装完成")
    else:
        print("✓ 虚拟环境已存在")


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    print("\n" + "=" * 50)
    print(f"🚀 启动游戏平台服务")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔧 自动重载: {'开启' if reload else '关闭'}")
    print("=" * 50 + "\n")

    cmd = [
        "uv", "run", "uvicorn",
        APP_MODULE,
        "--host", host,
        "--port", str(port),
    ]
    
    if reload:
        cmd.extend(["--reload"])
    
    try:
        subprocess.run(cmd, cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
        sys.exit(0)


def show_help():
    print("""
游戏平台启动脚本

用法:
  python run.py [命令] [选项]

命令:
  dev      开发模式 (默认) - 启用自动重载
  prod     生产模式 - 禁用自动重载
  help     显示帮助信息

选项:
  --host HOST    绑定地址 (默认: 127.0.0.1)
  --port PORT    绑定端口 (默认: 8000)

示例:
  python run.py dev                    # 开发模式，默认端口 8000
  python run.py dev --port 5000        # 开发模式，端口 5000
  python run.py prod --host 0.0.0.0    # 生产模式，绑定所有接口
    """)


def main():
    args = sys.argv[1:]
    
    host = "127.0.0.1"
    port = 8000
    reload = True
    command = "dev"

    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg in ["--help", "-h", "help"]:
            show_help()
            sys.exit(0)
        elif arg == "dev":
            command = "dev"
            reload = True
        elif arg == "prod":
            command = "prod"
            reload = False
        elif arg == "--host":
            if i + 1 < len(args):
                host = args[i + 1]
                i += 1
            else:
                print("错误: --host 需要一个参数")
                sys.exit(1)
        elif arg == "--port":
            if i + 1 < len(args):
                try:
                    port = int(args[i + 1])
                    i += 1
                except ValueError:
                    print("错误: --port 必须是一个数字")
                    sys.exit(1)
            else:
                print("错误: --port 需要一个参数")
                sys.exit(1)
        i += 1

    if not check_uv():
        sys.exit(1)

    check_dependencies()

    run_server(host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
