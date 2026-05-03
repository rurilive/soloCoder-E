import argparse
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from uvicorn import run


def parse_args():
    parser = argparse.ArgumentParser(description='电子阅读器 - Web-based E-Reader')
    parser.add_argument('--host', default='0.0.0.0', help='绑定地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5555, help='端口号 (默认: 5555)')
    parser.add_argument('--reload', action='store_true', help='开发模式，自动重载')
    return parser.parse_args()


def main():
    args = parse_args()
    
    print('=' * 50)
    print('📚 电子阅读器启动中...')
    print(f'🌐 地址: http://{args.host}:{args.port}')
    print('=' * 50)
    
    run(
        'app.main:app',
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == '__main__':
    main()
