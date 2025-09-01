#!/bin/bash

# 邮箱服务Docker部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|logs|status]

set -e

PROJECT_NAME="cloudfare-qq-mail"
COMPOSE_FILE="docker-compose.yml"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_message $RED "❌ Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "❌ Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    print_message $GREEN "✅ Docker环境检查通过"
}

# 启动服务
start_services() {
    print_message $BLUE "🚀 启动邮箱服务..."
    
    # 创建必要的目录
    mkdir -p uploads temp_attachments received_emails
    
    # 构建并启动服务
    docker-compose -f $COMPOSE_FILE up -d --build
    
    print_message $GREEN "✅ 服务启动成功！"
    print_message $YELLOW "📍 Web应用: http://localhost:5000"
    print_message $YELLOW "📍 phpMyAdmin: http://localhost:8080"
    print_message $YELLOW "📍 MySQL: localhost:3306"
}

# 停止服务
stop_services() {
    print_message $BLUE "🛑 停止邮箱服务..."
    docker-compose -f $COMPOSE_FILE down
    print_message $GREEN "✅ 服务已停止"
}

# 重启服务
restart_services() {
    print_message $BLUE "🔄 重启邮箱服务..."
    stop_services
    start_services
}

# 查看日志
show_logs() {
    print_message $BLUE "📋 查看服务日志..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# 查看状态
show_status() {
    print_message $BLUE "📊 服务状态："
    docker-compose -f $COMPOSE_FILE ps
    
    print_message $BLUE "\n🔍 容器详细信息："
    docker ps --filter "name=${PROJECT_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# 清理资源
cleanup() {
    print_message $BLUE "🧹 清理Docker资源..."
    docker-compose -f $COMPOSE_FILE down -v --remove-orphans
    docker system prune -f
    print_message $GREEN "✅ 清理完成"
}

# 备份数据
backup_data() {
    print_message $BLUE "💾 备份数据库..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="backup_${timestamp}.sql"
    
    docker-compose -f $COMPOSE_FILE exec db mysqldump -u root -p518107qW cloudfare_qq_mail > $backup_file
    print_message $GREEN "✅ 数据库备份完成: $backup_file"
}

# 显示帮助信息
show_help() {
    echo "邮箱服务Docker部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  logs      查看服务日志"
    echo "  status    查看服务状态"
    echo "  cleanup   清理Docker资源"
    echo "  backup    备份数据库"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 logs     # 查看日志"
    echo "  $0 status   # 查看状态"
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            check_docker
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_docker
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup
            ;;
        backup)
            backup_data
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_message $RED "❌ 未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
