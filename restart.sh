#!/bin/bash

# 电子阅读器重启脚本
# Web-based E-Reader Restart Script

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/ereader.pid"

cd "$PROJECT_DIR"

echo "🔄 正在重启电子阅读器..."
echo ""

# 检查是否正在运行
NEED_STOP=false

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        NEED_STOP=true
    fi
fi

# 尝试通过进程名查找
if [ "$NEED_STOP" = false ]; then
    PIDS=$(pgrep -f "uv.*run.*python.*run.py" 2>/dev/null || pgrep -f "python.*run.py" 2>/dev/null || pgrep -f "uvicorn.*app.main" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        NEED_STOP=true
    fi
fi

if [ "$NEED_STOP" = true ]; then
    echo "🛑 停止当前运行的服务..."
    
    # 调用停止脚本
    ./stop.sh
    
    # 等待服务完全停止
    sleep 1
    
    # 检查是否还有进程
    REMAINING_PIDS=$(pgrep -f "uv.*run.*python.*run.py" 2>/dev/null || pgrep -f "python.*run.py" 2>/dev/null || pgrep -f "uvicorn.*app.main" 2>/dev/null)
    if [ -n "$REMAINING_PIDS" ]; then
        echo "⚠️  等待服务完全停止..."
        for i in {1..5}; do
            REMAINING_PIDS=$(pgrep -f "uv.*run.*python.*run.py" 2>/dev/null || pgrep -f "python.*run.py" 2>/dev/null || pgrep -f "uvicorn.*app.main" 2>/dev/null)
            if [ -z "$REMAINING_PIDS" ]; then
                break
            fi
            echo "⏳ 等待中... ($i/5)"
            sleep 1
        done
    fi
    
    echo "✅ 服务已停止"
    echo ""
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
