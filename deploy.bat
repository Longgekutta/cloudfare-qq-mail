@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 邮箱服务Docker部署脚本 (Windows版本)
:: 使用方法: deploy.bat [start|stop|restart|logs|status]

set PROJECT_NAME=cloudfare-qq-mail
set COMPOSE_FILE=docker-compose.yml

:: 检查Docker是否安装
:check_docker
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
goto :main

:: 启动服务
:start_services
echo 🚀 启动邮箱服务...

:: 创建必要的目录
if not exist "uploads" mkdir uploads
if not exist "temp_attachments" mkdir temp_attachments
if not exist "received_emails" mkdir received_emails

:: 构建并启动服务
docker-compose -f %COMPOSE_FILE% up -d --build

if errorlevel 1 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

echo.
echo ✅ 服务启动成功！
echo 📍 Web应用: http://localhost:5000
echo 📍 phpMyAdmin: http://localhost:8080
echo 📍 MySQL: localhost:3306
echo 🔐 管理员账号: admin / admin123
echo.
goto :end

:: 停止服务
:stop_services
echo 🛑 停止邮箱服务...
docker-compose -f %COMPOSE_FILE% down
echo ✅ 服务已停止
goto :end

:: 重启服务
:restart_services
echo 🔄 重启邮箱服务...
call :stop_services
call :start_services
goto :end

:: 查看日志
:show_logs
echo 📋 查看服务日志...
docker-compose -f %COMPOSE_FILE% logs -f
goto :end

:: 查看状态
:show_status
echo 📊 服务状态：
docker-compose -f %COMPOSE_FILE% ps
echo.
echo 🔍 容器详细信息：
docker ps --filter "name=%PROJECT_NAME%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
goto :end

:: 清理资源
:cleanup
echo 🧹 清理Docker资源...
docker-compose -f %COMPOSE_FILE% down -v --remove-orphans
docker system prune -f
echo ✅ 清理完成
goto :end

:: 备份数据
:backup_data
echo 💾 备份数据库...
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set mytime=%mytime: =0%
set backup_file=backup_%mydate%_%mytime%.sql

docker-compose -f %COMPOSE_FILE% exec db mysqldump -u root -p518107qW cloudfare_qq_mail > %backup_file%
echo ✅ 数据库备份完成: %backup_file%
goto :end

:: 显示帮助信息
:show_help
echo 邮箱服务Docker部署脚本 (Windows版本)
echo.
echo 使用方法:
echo   %~nx0 [命令]
echo.
echo 可用命令:
echo   start     启动所有服务
echo   stop      停止所有服务
echo   restart   重启所有服务
echo   logs      查看服务日志
echo   status    查看服务状态
echo   cleanup   清理Docker资源
echo   backup    备份数据库
echo   help      显示此帮助信息
echo.
echo 示例:
echo   %~nx0 start    # 启动服务
echo   %~nx0 logs     # 查看日志
echo   %~nx0 status   # 查看状态
echo.
goto :end

:: 主函数
:main
if "%1"=="" goto :show_help
if "%1"=="start" (
    call :check_docker
    call :start_services
) else if "%1"=="stop" (
    call :stop_services
) else if "%1"=="restart" (
    call :check_docker
    call :restart_services
) else if "%1"=="logs" (
    call :show_logs
) else if "%1"=="status" (
    call :show_status
) else if "%1"=="cleanup" (
    call :cleanup
) else if "%1"=="backup" (
    call :backup_data
) else if "%1"=="help" (
    call :show_help
) else (
    echo ❌ 未知命令: %1
    call :show_help
)

:end
if not "%1"=="logs" pause
