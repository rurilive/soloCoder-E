#!/bin/bash

# 电子阅读器重启脚本
# Web-based E-Reader Restart Script

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/ereader.pid"

cd "$PROJECT_DIR"

echo "🔄 正在重启电子阅读器..."
echo ""

# 检查是否正在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "🛑 停止当前运行的服务 (PID: $PID)..."
        
        # 调用停止脚本
        ./stop.sh
        if [ $? -ne 0 ]; then
            echo "❌ 停止服务失败，重启中止"
            exit 1
        fi
        
        echo "✅ 服务已停止"
        echo ""
    fi
fi

# 启动服务
echo "🚀 启动新服务..."
./start.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 电子阅读器重启成功！"
else
    echo ""
    echo "❌ 电子阅读器重启失败"
    exit 1
fi
