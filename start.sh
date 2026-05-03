#!/bin/bash

# 电子阅读器启动脚本
# Web-based E-Reader Startup Script

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/ereader.pid"
LOG_FILE="$PROJECT_DIR/ereader.log"
HOST="0.0.0.0"
PORT="5555"

cd "$PROJECT_DIR"

# 检查是否已经运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "❌ 电子阅读器已经在运行中 (PID: $PID)"
        echo "   访问地址: http://$HOST:$PORT"
        exit 1
    else
        # PID文件存在但进程不存在，清理
        rm -f "$PID_FILE"
    fi
fi

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "🔍 检测到虚拟环境，正在激活..."
    source ".venv/bin/activate"
fi

# 检查依赖
echo "📦 检查依赖..."
python -c "import fastapi, uvicorn, jinja2, ebooklib, bs4, sqlalchemy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖，正在安装..."
    pip install -e .
fi

# 创建必要的目录
mkdir -p "$PROJECT_DIR/uploads"
mkdir -p "$PROJECT_DIR/logs"

echo "🚀 启动电子阅读器..."
echo "🌐 访问地址: http://$HOST:$PORT"
echo "📝 日志文件: $LOG_FILE"
echo "📊 PID 文件: $PID_FILE"

# 后台启动服务
nohup python run.py --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

# 等待服务启动
sleep 2

# 检查服务是否启动成功
PID=$(cat "$PID_FILE" 2>/dev/null)
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    echo "✅ 电子阅读器启动成功！"
    echo "📍 PID: $PID"
    echo "🌐 访问地址: http://$HOST:$PORT"
    echo ""
    echo "📌 常用命令:"
    echo "   停止服务: ./stop.sh"
    echo "   重启服务: ./restart.sh"
    echo "   查看日志: tail -f $LOG_FILE"
else
    echo "❌ 电子阅读器启动失败！"
    echo "📝 查看日志获取详情: tail -n 50 $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
