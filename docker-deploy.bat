@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 邮箱服务Docker一键部署脚本 (Windows版本)
:: 参考咸鱼自动回复项目的部署方式

set PROJECT_NAME=cloudfare-qq-mail
set IMAGE_NAME=cloudfare-qq-mail
set VERSION=1.0

echo ==================================================================
echo 📧 邮箱服务系统 - Docker一键部署 (Windows版本)
echo ==================================================================
echo 🕐 部署时间: %date% %time%
echo 📁 工作目录: %cd%
echo ==================================================================
echo.

:: 检查Docker环境
echo 🔍 检查Docker环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
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

:: 创建必要目录
echo 📁 创建必要目录...
if not exist "uploads" mkdir uploads
if not exist "temp_attachments" mkdir temp_attachments
if not exist "received_emails" mkdir received_emails
if not exist "mysql_data" mkdir mysql_data
echo ✅ 目录创建完成
echo.

:: 部署服务
echo 🚀 开始部署服务...
docker-compose up -d --build

if errorlevel 1 (
    echo ❌ 服务部署失败
    pause
    exit /b 1
)

echo ✅ 服务部署成功！
echo.

:: 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

:: 检查服务状态
echo 📊 服务状态：
docker-compose ps
echo.

echo 🔍 容器详细信息：
docker ps --filter "name=%PROJECT_NAME%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

:: 显示访问信息
echo ✅ 部署完成！
echo.
echo 📍 访问地址：
echo   - Web应用: http://localhost:5000
echo   - 数据库管理: http://localhost:8080
echo   - MySQL: localhost:3306
echo.
echo 🔐 默认账号：
echo   - 管理员1: admin / 518107qW
echo   - 管理员2: longgekutta / 518107qW
echo   - 数据库: root / 518107qW
echo.
echo 💡 使用说明：
echo   - 查看日志: docker-compose logs -f
echo   - 停止服务: docker-compose down
echo   - 重启服务: docker-compose restart
echo   - 备份数据: docker-deploy.bat backup
echo.

:: 处理命令行参数
if "%1"=="stop" goto :stop
if "%1"=="restart" goto :restart
if "%1"=="status" goto :status
if "%1"=="logs" goto :logs
if "%1"=="backup" goto :backup
if "%1"=="help" goto :help

echo 🎉 部署完成！按任意键退出...
pause >nul
goto :end

:stop
echo 🛑 停止服务...
docker-compose down
echo ✅ 服务已停止
goto :end

:restart
echo 🔄 重启服务...
docker-compose down
docker-compose up -d --build
echo ✅ 服务已重启
goto :end

:status
echo 📊 服务状态：
docker-compose ps
echo.
docker ps --filter "name=%PROJECT_NAME%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
goto :end

:logs
docker-compose logs -f
goto :end

:backup
echo 💾 备份数据库...
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set mytime=%mytime: =0%
set backup_file=backup_%mydate%_%mytime%.sql

docker-compose exec db mysqldump -u root -p518107qW cloudfare_qq_mail > %backup_file%
echo ✅ 数据库备份完成: %backup_file%
goto :end

:help
echo 邮箱服务Docker部署脚本 (Windows版本)
echo.
echo 使用方法:
echo   %~nx0 [命令]
echo.
echo 可用命令:
echo   deploy    部署服务（默认）
echo   stop      停止服务
echo   restart   重启服务
echo   status    查看状态
echo   logs      查看日志
echo   backup    备份数据库
echo   help      显示帮助
echo.
goto :end

:end
if not "%1"=="logs" pause
