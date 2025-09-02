@echo off
chcp 65001 >nul
title Docker镜像构建和推送脚本

echo 🚀 Docker镜像优化构建脚本
echo ================================

:: 设置镜像名称
set IMAGE_NAME=longgekutta/cloudfare-qq-mail
set TAG=latest

echo 📦 开始构建镜像: %IMAGE_NAME%:%TAG%
echo.

:: 使用BuildKit和网络优化构建
echo 🔧 使用BuildKit优化构建...
set DOCKER_BUILDKIT=1
docker build --network=host --progress=plain -t %IMAGE_NAME%:%TAG% .

if errorlevel 1 (
    echo ❌ 镜像构建失败
    pause
    exit /b 1
)

echo ✅ 镜像构建成功
echo.

:: 显示镜像信息
echo 📊 镜像信息:
docker images %IMAGE_NAME%:%TAG%
echo.

:: 询问是否推送
set /p PUSH_CONFIRM=是否推送到DockerHub? (y/N): 

if /i "%PUSH_CONFIRM%"=="y" (
    echo 🔐 登录DockerHub...
    docker login
    
    if errorlevel 1 (
        echo ❌ DockerHub登录失败
        pause
        exit /b 1
    )
    
    echo 📤 推送镜像到DockerHub...
    docker push %IMAGE_NAME%:%TAG%
    
    if errorlevel 1 (
        echo ❌ 镜像推送失败
        pause
        exit /b 1
    )
    
    echo ✅ 镜像推送成功
    echo 🌐 镜像地址: https://hub.docker.com/r/%IMAGE_NAME%
) else (
    echo ℹ️ 跳过推送步骤
)

echo.
echo 🎉 构建完成！
echo.
echo 📋 服务器部署命令:
echo docker pull %IMAGE_NAME%:%TAG%
echo docker-compose -f docker-compose.prod.yml up -d
echo.

pause
