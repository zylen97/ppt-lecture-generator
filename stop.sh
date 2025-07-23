#!/bin/bash

# PPT讲稿生成器 Web版 - 停止脚本
# 停止前后端服务并清理资源

set -e  # 遇到错误继续执行（不同于start.sh）

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

# 通过PID停止进程
stop_by_pid() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "停止${service_name}服务 (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            
            # 等待进程正常结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            # 如果进程仍在运行，强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                log_warning "${service_name}服务未正常结束，强制停止..."
                kill -KILL "$pid" 2>/dev/null || true
                sleep 1
            fi
            
            if ! kill -0 "$pid" 2>/dev/null; then
                log_success "${service_name}服务已停止"
            else
                log_error "${service_name}服务停止失败"
            fi
        else
            log_warning "${service_name}进程 (PID: $pid) 已不存在"
        fi
        rm -f "$pid_file"
    else
        log_info "未找到${service_name}的PID文件"
    fi
}

# 通过端口停止进程
stop_by_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_info "通过端口 $port 停止${service_name}服务..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # 检查是否还有进程在使用该端口
        local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            log_warning "强制停止端口 $port 上的进程..."
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        
        # 验证端口是否已释放
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_success "${service_name}服务 (端口 $port) 已停止"
        else
            log_error "${service_name}服务 (端口 $port) 停止失败"
        fi
    else
        log_info "${service_name}服务 (端口 $port) 未在运行"
    fi
}

# 停止后端服务
stop_backend() {
    log_info "正在停止后端服务..."
    
    # 首先尝试通过PID文件停止
    stop_by_pid "backend.pid" "后端"
    
    # 然后通过端口确保完全停止
    stop_by_port 8000 "后端"
}

# 停止前端服务
stop_frontend() {
    log_info "正在停止前端服务..."
    
    # 首先尝试通过PID文件停止
    stop_by_pid "frontend.pid" "前端"
    
    # 然后通过端口确保完全停止
    stop_by_port 3000 "前端"
}

# 清理临时文件
cleanup_files() {
    log_info "清理临时文件..."
    
    # 清理PID文件
    rm -f backend.pid frontend.pid
    
    # 清理日志文件（可选）
    if [ "$1" = "--clean-logs" ]; then
        log_info "清理日志文件..."
        rm -f frontend.log
        rm -rf backend/logs/*.log 2>/dev/null || true
        log_success "日志文件已清理"
    fi
    
    # 清理临时文件
    rm -rf backend/temp/* 2>/dev/null || true
    
    log_success "临时文件清理完成"
}

# 显示状态信息
show_status() {
    echo ""
    log_info "📊 服务状态检查:"
    
    # 检查后端状态
    if lsof -Pi :7788 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "   后端服务 (7788): ${RED}运行中${NC}"
    else
        echo -e "   后端服务 (7788): ${GREEN}已停止${NC}"
    fi
    
    # 检查前端状态
    if lsof -Pi :9527 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "   前端服务 (9527): ${RED}运行中${NC}"
    else
        echo -e "   前端服务 (9527): ${GREEN}已停止${NC}"
    fi
    
    echo ""
}

# 显示帮助信息
show_help() {
    echo "PPT讲稿生成器 Web版 - 停止脚本"
    echo ""
    echo "用法:"
    echo "  ./stop.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --clean-logs    同时清理日志文件"
    echo "  --help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./stop.sh                # 停止服务"
    echo "  ./stop.sh --clean-logs   # 停止服务并清理日志"
    echo ""
}

# 主函数
main() {
    echo "🛑 PPT讲稿生成器 Web版 - 停止脚本"
    echo "================================"
    
    # 处理参数
    case "${1:-}" in
        --help)
            show_help
            exit 0
            ;;
        --clean-logs)
            CLEAN_LOGS="--clean-logs"
            ;;
        "")
            CLEAN_LOGS=""
            ;;
        *)
            log_error "未知参数: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
    
    # 检查是否在项目根目录
    if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 停止服务
    stop_backend
    stop_frontend
    
    # 清理文件
    cleanup_files "$CLEAN_LOGS"
    
    # 显示状态
    show_status
    
    log_success "🎉 所有服务已停止！"
    
    echo "💡 提示:"
    echo "   重新启动: ./start.sh"
    echo "   查看日志: tail -f backend/logs/app.log"
    echo ""
}

# 运行主函数
main "$@"