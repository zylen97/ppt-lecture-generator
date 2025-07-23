#!/bin/bash

# PPT讲稿生成器 Web版 - 启动脚本
# 自动启动前后端服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}


# 检查端口是否被占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "端口 $1 已被占用，正在尝试停止相关进程..."
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# 检查环境是否准备就绪
check_env_ready() {
    log_info "检查开发环境..."
    
    # 检查虚拟环境
    if [ ! -d "backend/venv" ]; then
        log_error "Python虚拟环境未找到！"
        log_error "请先运行：cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # 检查Node.js依赖
    if [ ! -d "frontend/node_modules" ]; then
        log_error "Node.js依赖未安装！"
        log_error "请先运行：cd frontend && npm install"
        exit 1
    fi
    
    # 检查基本目录
    mkdir -p backend/data backend/uploads backend/logs backend/temp
    
    log_success "开发环境检查通过"
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    cd backend
    
    # 激活虚拟环境并启动服务
    source venv/bin/activate
    nohup python run.py > logs/app.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    
    cd ..
    
    # 等待后端启动
    log_info "等待后端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:7788/health > /dev/null 2>&1; then
            log_success "后端服务启动成功 (PID: $BACKEND_PID)"
            return 0
        fi
        sleep 1
    done
    
    log_error "后端服务启动失败，请检查日志: backend/logs/app.log"
    exit 1
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    cd frontend
    
    # 启动前端开发服务器
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    
    cd ..
    
    # 等待前端启动
    log_info "等待前端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:9527 > /dev/null 2>&1; then
            log_success "前端服务启动成功 (PID: $FRONTEND_PID)"
            return 0
        fi
        sleep 1
    done
    
    log_error "前端服务启动失败，请检查日志: frontend.log"
    exit 1
}

# 显示服务信息
show_info() {
    echo ""
    log_success "🎉 PPT讲稿生成器 Web版启动成功！"
    echo ""
    echo "📍 访问地址:"
    echo "   前端应用: http://localhost:9527"
    echo "   后端API: http://localhost:7788"
    echo "   API文档: http://localhost:7788/docs"
    echo ""
    echo "📋 进程信息:"
    if [ -f backend.pid ]; then
        echo "   后端进程: $(cat backend.pid)"
    fi
    if [ -f frontend.pid ]; then
        echo "   前端进程: $(cat frontend.pid)"
    fi
    echo ""
    echo "🛑 停止服务: ./stop.sh"
    echo "📊 查看日志: tail -f backend/logs/app.log"
    echo ""
}

# 清理函数
cleanup() {
    log_warning "收到中断信号，正在清理..."
    if [ -f backend.pid ]; then
        kill $(cat backend.pid) 2>/dev/null || true
        rm -f backend.pid
    fi
    if [ -f frontend.pid ]; then
        kill $(cat frontend.pid) 2>/dev/null || true
        rm -f frontend.pid
    fi
    exit 130
}

# 主函数
main() {
    echo "🚀 PPT讲稿生成器 Web版 - 启动脚本"
    echo "================================"
    
    # 检查是否在项目根目录
    if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 设置中断处理
    trap cleanup INT TERM
    
    # 基本命令检查
    if ! command -v curl &> /dev/null; then
        log_error "curl 命令不存在，请先安装 curl"
        exit 1
    fi
    
    # 检查端口
    check_port 7788
    check_port 9527
    
    # 检查环境是否准备就绪
    check_env_ready
    
    # 启动服务
    start_backend
    start_frontend
    
    # 显示信息
    show_info
    
    # 保持脚本运行
    log_info "服务运行中... (按 Ctrl+C 停止)"
    while true; do
        # 检查进程是否还在运行
        if [ -f backend.pid ] && ! kill -0 $(cat backend.pid) 2>/dev/null; then
            log_error "后端服务异常停止"
            cleanup
            exit 1
        fi
        if [ -f frontend.pid ] && ! kill -0 $(cat frontend.pid) 2>/dev/null; then
            log_error "前端服务异常停止"
            cleanup
            exit 1
        fi
        sleep 5
    done
}

# 运行主函数
main "$@"