@echo off
chcp 65001 >nul
title 邮箱监控系统 - 修复版部署脚本

echo 🔧 邮箱监控系统修复版部署脚本
echo ================================

:: 1. 清理现有容器
echo 🧹 清理现有容器...
docker stop qq-mail-app mysql-db-new phpmyadmin-new >nul 2>&1
docker rm qq-mail-app mysql-db-new phpmyadmin-new >nul 2>&1

:: 2. 创建网络
echo 🌐 创建Docker网络...
docker network create qq-mail-network >nul 2>&1

:: 3. 启动MySQL数据库
echo 🗄️ 启动MySQL数据库...
docker run -d ^
    --name mysql-db-new ^
    --network qq-mail-network ^
    -e MYSQL_ROOT_PASSWORD=518107qW ^
    -e MYSQL_DATABASE=cloudfare_qq_mail ^
    -p 3307:3306 ^
    --restart unless-stopped ^
    mysql:8.0

if errorlevel 1 (
    echo ❌ MySQL启动失败
    pause
    exit /b 1
)

:: 4. 等待MySQL启动
echo ⏳ 等待MySQL启动...
timeout /t 30 /nobreak >nul

:: 5. 验证MySQL连接
echo 🔍 验证MySQL连接...
for /l %%i in (1,1,10) do (
    docker exec mysql-db-new mysqladmin ping -h localhost -u root -p518107qW --silent >nul 2>&1
    if not errorlevel 1 (
        echo ✅ MySQL连接成功
        goto mysql_ready
    )
    echo 等待MySQL启动... (%%i/10)
    timeout /t 5 /nobreak >nul
)
echo ❌ MySQL启动超时
pause
exit /b 1

:mysql_ready

:: 6. 启动修复版应用
echo 🚀 启动修复版应用...
docker run -d ^
    --name qq-mail-app ^
    --network qq-mail-network ^
    -p 5000:5000 ^
    -e DB_HOST=mysql-db-new ^
    -e DB_USER=root ^
    -e DB_PASSWORD=518107qW ^
    -e DB_NAME=cloudfare_qq_mail ^
    -e SECRET_KEY=cloudfare_qq_mail_secret_key_2025_fixed ^
    -e QQ_EMAIL=2846117874@qq.com ^
    -e QQ_AUTH_CODE=ajqnryrvvjmsdcgi ^
    -e TARGET_DOMAIN=shiep.edu.kg ^
    -e FLASK_ENV=production ^
    -e DEBUG_MODE=False ^
    --restart unless-stopped ^
    longgekutta/cloudfare-qq-mail:fixed

if errorlevel 1 (
    echo ❌ 应用启动失败
    pause
    exit /b 1
)

:: 7. 启动phpMyAdmin
echo 🔧 启动phpMyAdmin...
docker run -d ^
    --name phpmyadmin-new ^
    --network qq-mail-network ^
    -e PMA_HOST=mysql-db-new ^
    -e PMA_USER=root ^
    -e PMA_PASSWORD=518107qW ^
    -p 8080:80 ^
    --restart unless-stopped ^
    phpmyadmin/phpmyadmin >nul 2>&1

:: 8. 等待应用启动
echo ⏳ 等待应用启动...
timeout /t 20 /nobreak >nul

:: 9. 检查服务状态
echo 📊 检查服务状态...
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

:: 10. 测试应用
echo 🧪 测试应用...
curl -f -s http://localhost:5000/ >nul 2>&1
if not errorlevel 1 (
    echo ✅ 应用运行正常！
    
    :: 测试管理员登录
    echo 👤 测试管理员登录...
    curl -s -X POST http://localhost:5000/login ^
        -H "Content-Type: application/x-www-form-urlencoded" ^
        -d "username=admin&password=518107qW" | findstr "Redirecting" >nul
    
    if not errorlevel 1 (
        echo ✅ 管理员登录测试成功！
    ) else (
        echo ⚠️ 管理员登录可能有问题，请手动测试
    )
    
) else (
    echo ❌ 应用启动失败，查看日志：
    docker logs qq-mail-app --tail 20
)

:: 11. 显示访问信息
echo.
echo 🎉 修复版部署完成！
echo ================================
echo 🌐 访问地址: http://localhost:5000
echo 👤 管理员账号: admin / 518107qW
echo 🔧 phpMyAdmin: http://localhost:8080
echo ================================
echo 📋 管理命令:
echo 查看应用日志: docker logs qq-mail-app -f
echo 查看数据库日志: docker logs mysql-db-new -f
echo 重启应用: docker restart qq-mail-app
echo 停止所有服务: docker stop qq-mail-app mysql-db-new phpmyadmin-new
echo ================================

echo.
echo 🔧 修复内容:
echo ✅ 修复了数据库初始化问题
echo ✅ 修复了管理员密码哈希问题
echo ✅ 修复了前端CDN资源加载问题
echo ✅ 修复了Python依赖版本冲突
echo ✅ 添加了完整的数据库初始化脚本
echo ✅ 使用国内CDN确保资源加载稳定

pause
