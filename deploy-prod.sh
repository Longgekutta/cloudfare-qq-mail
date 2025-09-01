#!/bin/bash
# 生产环境部署脚本

set -e  # 遇到错误立即退出

echo "🚀 开始生产环境部署..."

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "❌ 未找到 .env 文件，请先创建环境变量配置"
    echo "💡 可以复制 .env.example 为 .env 并填入真实配置"
    exit 1
fi

# 加载环境变量
source .env

# 检查必需的环境变量
required_vars=("DB_PASSWORD" "SECRET_KEY" "QQ_EMAIL" "QQ_AUTH_CODE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ 环境变量 $var 未设置"
        exit 1
    fi
done

echo "✅ 环境变量检查通过"

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p nginx/ssl
mkdir -p database/backup
mkdir -p logs

# 设置权限
chmod +x deploy-prod.sh
chmod 600 .env  # 保护环境变量文件

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# 清理旧镜像 (可选)
read -p "是否清理旧的Docker镜像? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理旧镜像..."
    docker system prune -f
    docker image prune -f
fi

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 健康检查
echo "🏥 执行健康检查..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:5000/ > /dev/null 2>&1; then
        echo "✅ 应用健康检查通过"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ 应用健康检查失败"
        echo "📋 查看日志:"
        docker-compose -f docker-compose.prod.yml logs --tail=50 web
        exit 1
    fi
    
    echo "⏳ 等待应用启动... ($attempt/$max_attempts)"
    sleep 5
    ((attempt++))
done

# 显示部署信息
echo ""
echo "🎉 部署完成!"
echo "=" * 50
echo "📍 应用地址: http://localhost:5000"
echo "🔐 管理员账号: admin / admin123"
echo "📊 服务状态: docker-compose -f docker-compose.prod.yml ps"
echo "📋 查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "🛑 停止服务: docker-compose -f docker-compose.prod.yml down"
echo "=" * 50

# 可选：启动Nginx反向代理
read -p "是否启动Nginx反向代理? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌐 启动Nginx反向代理..."
    docker-compose -f docker-compose.prod.yml --profile nginx up -d nginx
    echo "✅ Nginx已启动，可通过 http://localhost 访问"
fi

# 可选：启动Redis缓存
read -p "是否启动Redis缓存? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💾 启动Redis缓存..."
    docker-compose -f docker-compose.prod.yml --profile cache up -d redis
    echo "✅ Redis已启动"
fi

echo ""
echo "🎯 部署完成! 系统已就绪。"
echo "💡 建议定期备份数据库和重要文件"
