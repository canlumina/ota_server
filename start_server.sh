#!/bin/bash

# STM32 OTA Server 一键启动脚本
# 支持后台运行，关闭终端不会影响服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 日志目录
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# PID文件目录
PID_DIR="$SCRIPT_DIR/pids"
mkdir -p "$PID_DIR"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

# 打印带颜色的消息
print_message() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 停止服务
stop_services() {
    print_message "停止服务..."
    
    # 停止后端
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            print_message "停止后端服务 (PID: $BACKEND_PID)"
            kill "$BACKEND_PID"
            rm -f "$BACKEND_PID_FILE"
        fi
    fi
    
    # 停止前端
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            print_message "停止前端服务 (PID: $FRONTEND_PID)"
            kill "$FRONTEND_PID"
            rm -f "$FRONTEND_PID_FILE"
        fi
    fi
    
    # 强制杀死可能残留的进程
    pkill -f "python.*server/app.py" 2>/dev/null || true
    pkill -f "python.*http.server.*3000" 2>/dev/null || true
    
    print_success "服务已停止"
}

# 检查服务状态
check_status() {
    print_message "检查服务状态..."
    
    local backend_running=false
    local frontend_running=false
    
    # 检查后端
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            print_success "后端服务运行中 (PID: $BACKEND_PID, 端口: 5000)"
            backend_running=true
        else
            print_warning "后端PID文件存在但进程未运行"
            rm -f "$BACKEND_PID_FILE"
        fi
    fi
    
    if ! $backend_running; then
        if check_port 5000; then
            print_warning "端口5000被占用，但不是本脚本启动的后端服务"
        else
            print_error "后端服务未运行"
        fi
    fi
    
    # 检查前端
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            print_success "前端服务运行中 (PID: $FRONTEND_PID, 端口: 3000)"
            frontend_running=true
        else
            print_warning "前端PID文件存在但进程未运行"
            rm -f "$FRONTEND_PID_FILE"
        fi
    fi
    
    if ! $frontend_running; then
        if check_port 3000; then
            print_warning "端口3000被占用，但不是本脚本启动的前端服务"
        else
            print_error "前端服务未运行"
        fi
    fi
    
    # 访问地址
    if $backend_running && $frontend_running; then
        echo
        print_success "服务正在运行:"
        echo "  前端地址: http://localhost:3000"
        echo "  后端API: http://localhost:5000/api/v1"
        echo "  日志目录: $LOG_DIR"
    fi
}

# 启动服务
start_services() {
    print_message "启动 STM32 OTA Server..."
    
    # 检查Python环境
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        print_error "未找到Python环境"
        exit 1
    fi
    
    # 使用python3优先，fallback到python
    PYTHON_CMD="python3"
    if ! command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python"
    fi
    
    # 检查依赖
    if ! $PYTHON_CMD -c "import flask" >/dev/null 2>&1; then
        print_warning "Flask未安装，尝试安装依赖..."
        if [ -f "requirements.txt" ]; then
            pip3 install -r requirements.txt || pip install -r requirements.txt
        else
            print_error "requirements.txt文件不存在"
            exit 1
        fi
    fi
    
    # 检查端口占用
    if check_port 5000; then
        print_error "端口5000已被占用，请先停止占用该端口的服务"
        exit 1
    fi
    
    if check_port 3000; then
        print_error "端口3000已被占用，请先停止占用该端口的服务"
        exit 1
    fi
    
    # 确保storage目录存在
    mkdir -p storage/{firmware,uploads,logs}
    
    print_message "启动后端服务 (端口: 5000)..."
    # 启动后端 - 使用nohup确保后台运行
    nohup $PYTHON_CMD server/app.py > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"
    
    # 等待后端启动
    sleep 3
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        print_error "后端启动失败，请查看日志: $LOG_DIR/backend.log"
        exit 1
    fi
    
    # 检查后端是否正常响应
    for i in {1..10}; do
        if curl -s "http://localhost:5000/api/v1/system/health" >/dev/null 2>&1; then
            print_success "后端服务启动成功 (PID: $BACKEND_PID)"
            break
        fi
        if [ $i -eq 10 ]; then
            print_error "后端服务启动超时，请查看日志: $LOG_DIR/backend.log"
            exit 1
        fi
        sleep 1
    done
    
    print_message "启动前端服务 (端口: 3000)..."
    # 启动前端 - 使用nohup确保后台运行
    cd client/public
    nohup $PYTHON_CMD -m http.server 3000 > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
    cd "$SCRIPT_DIR"
    
    # 等待前端启动
    sleep 2
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        print_error "前端启动失败，请查看日志: $LOG_DIR/frontend.log"
        exit 1
    fi
    
    # 检查前端是否正常响应
    for i in {1..5}; do
        if curl -s "http://localhost:3000" >/dev/null 2>&1; then
            print_success "前端服务启动成功 (PID: $FRONTEND_PID)"
            break
        fi
        if [ $i -eq 5 ]; then
            print_error "前端服务启动超时，请查看日志: $LOG_DIR/frontend.log"
            exit 1
        fi
        sleep 1
    done
    
    echo
    print_success "所有服务启动完成!"
    echo "  前端地址: http://localhost:3000"
    echo "  后端API: http://localhost:5000/api/v1"
    echo "  日志目录: $LOG_DIR"
    echo
    print_message "服务已在后台运行，关闭终端不会影响服务"
    print_message "使用 '$0 stop' 停止服务"
    print_message "使用 '$0 status' 查看服务状态"
    print_message "使用 '$0 logs' 查看实时日志"
}

# 查看日志
show_logs() {
    local service=${2:-all}
    
    case $service in
        "backend")
            if [ -f "$LOG_DIR/backend.log" ]; then
                tail -f "$LOG_DIR/backend.log"
            else
                print_error "后端日志文件不存在"
            fi
            ;;
        "frontend")
            if [ -f "$LOG_DIR/frontend.log" ]; then
                tail -f "$LOG_DIR/frontend.log"
            else
                print_error "前端日志文件不存在"
            fi
            ;;
        *)
            print_message "显示所有服务日志 (Ctrl+C 退出)..."
            if [ -f "$LOG_DIR/backend.log" ] && [ -f "$LOG_DIR/frontend.log" ]; then
                tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
            elif [ -f "$LOG_DIR/backend.log" ]; then
                print_warning "只有后端日志文件存在"
                tail -f "$LOG_DIR/backend.log"
            elif [ -f "$LOG_DIR/frontend.log" ]; then
                print_warning "只有前端日志文件存在"
                tail -f "$LOG_DIR/frontend.log"
            else
                print_error "日志文件不存在"
            fi
            ;;
    esac
}

# 重启服务
restart_services() {
    print_message "重启服务..."
    stop_services
    sleep 2
    start_services
}

# 显示帮助信息
show_help() {
    echo "STM32 OTA Server 管理脚本"
    echo
    echo "用法: $0 [COMMAND] [OPTIONS]"
    echo
    echo "命令:"
    echo "  start         启动服务（默认）"
    echo "  stop          停止服务"
    echo "  restart       重启服务"
    echo "  status        查看服务状态"
    echo "  logs [TYPE]   查看日志 (TYPE: backend/frontend/all，默认all)"
    echo "  help          显示帮助信息"
    echo
    echo "示例:"
    echo "  $0              # 启动服务"
    echo "  $0 start        # 启动服务"
    echo "  $0 stop         # 停止服务"
    echo "  $0 status       # 查看状态"
    echo "  $0 logs         # 查看所有日志"
    echo "  $0 logs backend # 只查看后端日志"
}

# 主逻辑
case "${1:-start}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        check_status
        ;;
    "logs")
        show_logs $@
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac