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

# 检测可用的Python运行方式
detect_python_runner() {
    # 1. 优先检查 uv
    if command -v uv &> /dev/null; then
        if [ -f "$PROJECT_DIR/pyproject.toml" ]; then
            echo "🔍 检测到 uv，将使用 uv run 执行"
            echo "uv"
            return
        fi
    fi
    
    # 2. 检查项目内的虚拟环境
    if [ -d "$PROJECT_DIR/.venv" ]; then
        echo "🔍 检测到项目虚拟环境 (.venv)"
        echo "venv"
        return
    fi
    
    # 3. 检查系统python
    if command -v python3 &> /dev/null; then
        echo "🔍 使用系统 Python3"
        echo "python3"
        return
    elif command -v python &> /dev/null; then
        echo "🔍 使用系统 Python"
        echo "python"
        return
    fi
    
    echo "❌ 未找到可用的 Python 环境"
    echo "   请安装 Python 或使用 uv/pip 安装依赖"
    exit 1
}

RUNNER=$(detect_python_runner)
echo "✅ 运行方式: $RUNNER"

# 安装依赖的函数
install_deps() {
    echo "📦 检查/安装依赖..."
    case "$RUNNER" in
        "uv")
            uv sync
            ;;
        "venv")
            source "$PROJECT_DIR/.venv/bin/activate"
            pip install -e .
            ;;
        *)
            $RUNNER -m pip install --user -e . 2>/dev/null || $RUNNER -m pip install -e .
            ;;
    esac
}

# 执行Python命令的函数
run_python() {
    case "$RUNNER" in
        "uv")
            uv run python "$@"
            ;;
        "venv")
            source "$PROJECT_DIR/.venv/bin/activate"
            python "$@"
            ;;
        *)
            $RUNNER "$@"
            ;;
    esac
}

# 检查依赖
echo "📦 检查依赖..."
run_python -c "import fastapi, uvicorn, jinja2, ebooklib, bs4, sqlalchemy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖，正在安装..."
    install_deps
fi

# 创建必要的目录
mkdir -p "$PROJECT_DIR/uploads"
mkdir -p "$PROJECT_DIR/logs"

echo "🚀 启动电子阅读器..."
echo "🌐 访问地址: http://$HOST:$PORT"
echo "📝 日志文件: $LOG_FILE"
echo "📊 PID 文件: $PID_FILE"

# 后台启动服务
case "$RUNNER" in
    "uv")
        nohup uv run python run.py --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
        ;;
    "venv")
        source "$PROJECT_DIR/.venv/bin/activate"
        nohup python run.py --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
        ;;
    *)
        nohup $RUNNER run.py --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
        ;;
esac

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
