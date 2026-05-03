#!/bin/bash

# 电子阅读器停止脚本
# Web-based E-Reader Stop Script

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/ereader.pid"

cd "$PROJECT_DIR"

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  未找到PID文件，服务可能未运行"
    
    # 尝试通过进程名查找
    PID=$(pgrep -f "python.*run.py" 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "🔍 发现相关进程 (PID: $PID)"
        read -p "是否停止这些进程? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill "$PID" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "✅ 进程已停止"
            else
                echo "❌ 停止进程失败"
                exit 1
            fi
        fi
    fi
    exit 0
fi

# 读取PID
PID=$(cat "$PID_FILE" 2>/dev/null)

if [ -z "$PID" ]; then
    echo "⚠️  PID文件为空"
    rm -f "$PID_FILE"
    exit 0
fi

# 检查进程是否存在
if ! kill -0 "$PID" 2>/dev/null; then
    echo "⚠️  进程 (PID: $PID) 不存在"
    rm -f "$PID_FILE"
    exit 0
fi

echo "🛑 正在停止电子阅读器 (PID: $PID)..."

# 尝试优雅停止
kill -SIGTERM "$PID" 2>/dev/null

# 等待进程停止
for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi
    echo "⏳ 等待进程停止... ($i/10)"
    sleep 1
done

# 如果进程还在运行，强制停止
if kill -0 "$PID" 2>/dev/null; then
    echo "⚠️  进程未响应，强制停止..."
    kill -SIGKILL "$PID" 2>/dev/null
    sleep 1
fi

# 清理PID文件
rm -f "$PID_FILE"

# 再次检查
if kill -0 "$PID" 2>/dev/null; then
    echo "❌ 停止进程失败 (PID: $PID)"
    exit 1
else
    echo "✅ 电子阅读器已停止"
    echo ""
    echo "📌 重新启动: ./start.sh"
fi
