@echo off
chcp 65001 >nul
title 邮箱监控系统 - 生产环境部署

echo 🚀 开始生产环境部署...
echo.

:: 检查环境变量文件
if not exist ".env" (
    echo ❌ 未找到 .env 文件，请先创建环境变量配置
    echo 💡 可以复制 .env.example 为 .env 并填入真实配置
    pause
    exit /b 1
)

echo ✅ 环境变量文件检查通过
echo.

:: 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker环境检查通过
echo.

:: 创建必要的目录
echo 📁 创建必要的目录...
if not exist "nginx\ssl" mkdir nginx\ssl
if not exist "database\backup" mkdir database\backup
if not exist "logs" mkdir logs
echo ✅ 目录创建完成
echo.

:: 停止现有服务
echo 🛑 停止现有服务...
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>nul
echo ✅ 现有服务已停止
echo.

:: 询问是否清理旧镜像
set /p cleanup="是否清理旧的Docker镜像? (y/N): "
if /i "%cleanup%"=="y" (
    echo 🧹 清理旧镜像...
    docker system prune -f
    docker image prune -f
    echo ✅ 镜像清理完成
    echo.
)

:: 构建并启动服务
echo 🔨 构建并启动服务...
docker-compose -f docker-compose.prod.yml build --no-cache
if errorlevel 1 (
    echo ❌ 镜像构建失败
    pause
    exit /b 1
)

docker-compose -f docker-compose.prod.yml up -d
if errorlevel 1 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

echo ✅ 服务启动成功
echo.

:: 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 30 /nobreak >nul
echo.

:: 检查服务状态
echo 🔍 检查服务状态...
docker-compose -f docker-compose.prod.yml ps
echo.

:: 健康检查
echo 🏥 执行健康检查...
set max_attempts=30
set attempt=1

:health_check_loop
curl -f http://localhost:5000/ >nul 2>&1
if not errorlevel 1 (
    echo ✅ 应用健康检查通过
    goto health_check_success
)

if %attempt% geq %max_attempts% (
    echo ❌ 应用健康检查失败
    echo 📋 查看日志:
    docker-compose -f docker-compose.prod.yml logs --tail=50 web
    pause
    exit /b 1
)

echo ⏳ 等待应用启动... (%attempt%/%max_attempts%)
timeout /t 5 /nobreak >nul
set /a attempt+=1
goto health_check_loop

:health_check_success
echo.

:: 显示部署信息
echo 🎉 部署完成!
echo ============================================================
echo 📍 应用地址: http://localhost:5000
echo 🔐 管理员账号: admin / admin123
echo 📊 服务状态: docker-compose -f docker-compose.prod.yml ps
echo 📋 查看日志: docker-compose -f docker-compose.prod.yml logs -f
echo 🛑 停止服务: docker-compose -f docker-compose.prod.yml down
echo ============================================================
echo.

:: 可选：启动Nginx反向代理
set /p nginx="是否启动Nginx反向代理? (y/N): "
if /i "%nginx%"=="y" (
    echo 🌐 启动Nginx反向代理...
    docker-compose -f docker-compose.prod.yml --profile nginx up -d nginx
    if not errorlevel 1 (
        echo ✅ Nginx已启动，可通过 http://localhost 访问
    ) else (
        echo ⚠️ Nginx启动失败，请检查配置
    )
    echo.
)

:: 可选：启动Redis缓存
set /p redis="是否启动Redis缓存? (y/N): "
if /i "%redis%"=="y" (
    echo 💾 启动Redis缓存...
    docker-compose -f docker-compose.prod.yml --profile cache up -d redis
    if not errorlevel 1 (
        echo ✅ Redis已启动
    ) else (
        echo ⚠️ Redis启动失败，请检查配置
    )
    echo.
)

echo 🎯 部署完成! 系统已就绪。
echo 💡 建议定期备份数据库和重要文件
echo.
echo 按任意键退出...
pause >nul
