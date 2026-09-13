#!/bin/bash
# 完整问题诊断脚本 - 查看所有日志和状态信息

echo "🔍 开始完整问题诊断..."
echo "=================================="

# 1. 检查当前容器状态
echo "📊 1. 当前容器状态："
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 2. 检查Docker Compose文件存在情况
echo "📁 2. Docker Compose文件检查："
ls -la docker-compose*.yml 2>/dev/null || echo "❌ 没找到docker-compose文件"
echo ""

# 3. 检查最近的Docker构建日志
echo "🔨 3. Docker构建日志（最近的错误）："
# 检查失败的构建
if docker images | grep -q "app-cloudfare-qq-mail"; then
    echo "✅ 找到构建的镜像"
    docker images | grep cloudfare-qq-mail
else
    echo "❌ 没有找到成功构建的镜像"
fi
echo ""

# 4. 检查容器运行日志
echo "📋 4. 容器运行日志："
echo "--- Web容器日志 (如果存在) ---"
web_container=$(docker ps -a --format "{{.Names}}" | grep -E "(web|cloudfare-qq-mail)" | grep -v db | head -1)
if [ -n "$web_container" ]; then
    echo "Web容器名称: $web_container"
    docker logs "$web_container" --tail=20 2>&1
else
    echo "❌ 没有找到Web容器"
fi

echo ""
echo "--- 数据库容器日志 ---"
db_container=$(docker ps -a --format "{{.Names}}" | grep -E "(db|mysql)" | head -1)
if [ -n "$db_container" ]; then
    echo "数据库容器名称: $db_container"
    docker logs "$db_container" --tail=10 2>&1
else
    echo "❌ 没有找到数据库容器"
fi

# 5. 检查系统资源
echo ""
echo "💻 5. 系统资源状态："
echo "--- 磁盘空间 ---"
df -h /
echo ""
echo "--- 内存使用 ---"
free -h
echo ""
echo "--- Docker系统信息 ---"
docker system df
echo ""

# 6. 检查网络和端口
echo "🌐 6. 网络和端口状态："
echo "--- 端口监听状态 ---"
netstat -tuln | grep -E ":(5000|3306|8080)"
echo ""
echo "--- Docker网络 ---"
docker network ls | grep cloudfare || echo "没有找到项目网络"
echo ""

# 7. 检查最近的部署日志
echo "📝 7. 最近的部署日志："
latest_log=$(ls -t /tmp/cloudfare-qq-mail-deploy-* 2>/dev/null | head -1)
if [ -n "$latest_log" ]; then
    echo "最新日志文件: $latest_log"
    echo "--- 最后50行 ---"
    tail -50 "$latest_log"
else
    echo "❌ 没有找到部署日志文件"
fi

# 8. 检查具体的Docker Compose操作
echo ""
echo "🐳 8. Docker Compose状态检查："
for compose_file in docker-compose.yml docker-compose.simple.yml docker-compose.tencent.yml docker-compose.china.yml; do
    if [ -f "$compose_file" ]; then
        echo "--- $compose_file 状态 ---"
        docker-compose -f "$compose_file" ps 2>/dev/null || echo "该compose文件无活动服务"
    fi
done

# 9. 尝试手动构建测试
echo ""
echo "🔧 9. 手动构建测试："
echo "--- 检查Dockerfile ---"
if [ -f "Dockerfile.simple" ]; then
    echo "✅ Dockerfile.simple 存在"
    echo "尝试构建测试（前5步）："
    docker build -f Dockerfile.simple -t test-build . 2>&1 | head -20
else
    echo "❌ Dockerfile.simple 不存在"
fi

echo ""
echo "🎯 10. 问题总结建议："
echo "根据上述日志信息，查看："
echo "- 构建过程中的具体错误信息"
echo "- 容器启动时的错误日志"
echo "- 系统资源是否充足"
echo "- 端口冲突或网络问题"
echo ""
echo "=================================="
echo "✅ 诊断完成，请根据具体错误信息进行修复"
