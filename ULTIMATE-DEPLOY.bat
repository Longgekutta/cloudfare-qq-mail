@echo off
REM ============================================================================
REM 🚀 终极部署脚本 (Windows版本) - 整合所有部署方案的最强版本
REM ============================================================================
REM 用户信息：
REM GitHub: Longgekutta
REM DockerHub: longgekutta  
REM Gitee: longgekutta
REM ============================================================================
setlocal enabledelayedexpansion

set "PROJECT_NAME=cloudfare-qq-mail"
set "GITHUB_REPO=https://github.com/Longgekutta/cloudfare-qq-mail.git"
set "GITEE_REPO=https://gitee.com/longgekutta/cloudfare-qq-mail.git"
set "DOCKER_IMAGE=longgekutta/cloudfare-qq-mail:latest"
set "VERSION=v3.0-ultimate-windows"
set "DEPLOY_LOG=%TEMP%\%PROJECT_NAME%-deploy-%RANDOM%.log"

REM 默认参数
set "DEPLOY_MODE=auto"
set "USE_PREBUILT_IMAGE=false"
set "VERBOSE=false"

REM 颜色支持（Windows 10+）
for /f "tokens=2 delims=[]" %%i in ('ver') do set "WIN_VER=%%i"

echo ============================================================================ > "%DEPLOY_LOG%"
echo 🚀 终极部署开始 (Windows) - %PROJECT_NAME% >> "%DEPLOY_LOG%"
echo 部署时间: %date% %time% >> "%DEPLOY_LOG%"
echo ============================================================================ >> "%DEPLOY_LOG%"

REM 显示横幅
echo.
echo ================================================================
echo 🚀 终极部署脚本 - Cloudfare QQ Mail Service %VERSION%
echo ================================================================
echo 📅 部署时间: %date% %time%
echo 👤 GitHub: Longgekutta
echo 🐳 DockerHub: longgekutta
echo 📂 工作目录: %~dp0
echo 📋 部署日志: %DEPLOY_LOG%
echo ⚙️ 部署模式: %DEPLOY_MODE%
echo ================================================================
echo.

REM 解析命令行参数
:parse_args
if "%1"=="" goto start_deploy
if "%1"=="--mode" (
    set "DEPLOY_MODE=%2"
    shift
    shift
    goto parse_args
)
if "%1"=="--use-image" (
    set "USE_PREBUILT_IMAGE=true"
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%1"=="--start" (
    call :manage_services start
    goto end
)
if "%1"=="--stop" (
    call :manage_services stop
    goto end
)
if "%1"=="--restart" (
    call :manage_services restart
    goto end
)
if "%1"=="--status" (
    call :manage_services status
    goto end
)
if "%1"=="--logs" (
    call :manage_services logs
    goto end
)
if "%1"=="--clean" (
    call :cleanup_resources
    goto end
)
if "%1"=="--help" (
    call :show_help
    goto end
)
echo ❌ 未知参数: %1
call :show_help
goto error_exit

:start_deploy
echo 🔍 检测环境...

REM 检查Windows版本
echo 💻 Windows版本: %WIN_VER%
echo 💻 Windows版本: %WIN_VER% >> "%DEPLOY_LOG%"

REM 检查Docker Desktop
echo 🐳 检查Docker环境...
docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Docker未安装！请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    echo 安装完成后请重启此脚本
    pause
    goto error_exit
)

echo ✅ Docker已安装: 
docker --version

docker-compose --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Docker Compose未安装！
    echo 请确保Docker Desktop包含Docker Compose
    pause
    goto error_exit
)

echo ✅ Docker Compose已安装:
docker-compose --version

REM 检查Docker服务状态
docker info >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Docker服务未运行！
    echo 请启动Docker Desktop并等待完全启动后重试
    pause
    goto error_exit
)

echo ✅ Docker服务运行正常

REM 检查网络连接
echo 🌐 检查网络连接...
ping -n 1 github.com >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ GitHub网络连接正常
    set "REPO_URL=%GITHUB_REPO%"
) else (
    ping -n 1 gitee.com >nul 2>&1
    if !errorlevel! equ 0 (
        echo ⚠️ GitHub连接失败，使用Gitee镜像
        set "REPO_URL=%GITEE_REPO%"
    ) else (
        echo ❌ 网络连接异常，请检查网络设置
        pause
        goto error_exit
    )
)

REM 获取项目代码
echo 📥 获取项目代码...
if exist "docker-compose.yml" if exist "app.py" (
    echo ✅ 检测到已在项目目录中，使用现有代码
    goto create_config
)

if exist "%PROJECT_NAME%" (
    echo ⚠️ 项目目录已存在，删除旧版本...
    rmdir /s /q "%PROJECT_NAME%"
)

echo 📦 克隆项目: !REPO_URL!
git clone "!REPO_URL!" "%PROJECT_NAME%"
if !errorlevel! neq 0 (
    echo ❌ 代码获取失败，请检查网络连接
    pause
    goto error_exit
)

cd "%PROJECT_NAME%"
echo ✅ 代码获取成功

:create_config
echo ⚙️ 创建完整配置...

REM 创建.env文件
echo # ============================================================================ > .env
echo # 📧 邮箱服务系统 - Windows环境配置 >> .env
echo # ============================================================================ >> .env
echo # 自动生成时间: %date% %time% >> .env
echo # 部署版本: %VERSION% >> .env
echo # ============================================================================ >> .env
echo. >> .env
echo # ========== 🌐 应用基础配置 ========== >> .env
echo WEB_PORT=5000 >> .env
echo FLASK_ENV=production >> .env
echo SECRET_KEY=cloudfare_qq_mail_secret_key_%RANDOM%%RANDOM% >> .env
echo DEBUG_MODE=False >> .env
echo DOMAIN=http://localhost:5000 >> .env
echo. >> .env
echo # ========== 🗄️ 数据库配置 ========== >> .env
echo DB_HOST=db >> .env
echo DB_PORT=3306 >> .env
echo DB_USER=root >> .env
echo DB_PASSWORD=518107qW >> .env
echo DB_NAME=cloudfare_qq_mail >> .env
echo. >> .env
echo # ========== 📧 邮箱服务配置 ========== >> .env
echo QQ_EMAIL=YOUR_QQ_EMAIL@qq.com >> .env
echo QQ_AUTH_CODE=YOUR_QQ_AUTH_CODE >> .env
echo TARGET_DOMAIN=shiep.edu.kg >> .env
echo RESEND_API_KEY=re_00000000_REPLACED_DUMMY_KEY_0000 >> .env
echo. >> .env
echo # ========== 💰 支付系统配置 ========== >> .env
echo YIPAY_PID=6166 >> .env
echo YIPAY_KEY=deefc7cc0449be9cb621b7800f5e7f1c >> .env
echo YIPAY_GATEWAY=https://pay.yzhifupay.com/ >> .env
echo. >> .env
echo # ========== 🔧 可选服务配置 ========== >> .env
echo PHPMYADMIN_PORT=8080 >> .env
echo REDIS_PASSWORD=redis%RANDOM% >> .env
echo. >> .env
echo # ========== 🚀 部署配置 ========== >> .env
echo TZ=Asia/Shanghai >> .env
echo COMPOSE_PROJECT_NAME=%PROJECT_NAME% >> .env
echo DOCKER_IMAGE=%DOCKER_IMAGE% >> .env
echo DEPLOY_VERSION=%VERSION% >> .env

REM 创建必要目录
echo 📁 创建数据目录...
mkdir uploads 2>nul
mkdir temp_attachments 2>nul
mkdir received_emails 2>nul
mkdir sent_attachments 2>nul
mkdir logs 2>nul
mkdir mysql_data 2>nul
mkdir database\backup 2>nul
echo ✅ 目录创建完成

REM 选择部署方式
echo 🚀 选择部署方式...
if "%USE_PREBUILT_IMAGE%"=="true" (
    set "DEPLOY_MODE=image"
    echo 📦 使用预构建镜像部署
) else if exist "Dockerfile" (
    set "DEPLOY_MODE=build"
    echo 🔨 使用本地构建部署
) else (
    set "DEPLOY_MODE=image"
    echo 📦 默认使用镜像部署
)

REM 清理旧服务
echo 🛑 清理旧服务...
docker-compose down --remove-orphans >nul 2>&1

REM 执行部署
if "%DEPLOY_MODE%"=="image" (
    call :deploy_with_image
) else (
    call :deploy_with_build
)

if !errorlevel! neq 0 (
    echo ❌ 部署失败！
    goto show_failure
)

REM 等待服务启动
echo ⏳ 等待服务完全启动...
set /a "wait_time=0"
set /a "max_wait=180"

:wait_loop
if !wait_time! geq !max_wait! (
    echo ⚠️ 服务启动超时，请手动检查
    goto verify_deployment
)

timeout /t 5 /nobreak >nul
set /a "wait_time+=5"

REM 检查Web服务
curl -s http://localhost:5000 >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ 服务已就绪 ^(耗时: !wait_time!秒^)
    goto verify_deployment
)

if !wait_time! mod 15 equ 0 (
    echo 等待服务启动... ^(!wait_time!/!max_wait!秒^)
)
goto wait_loop

:verify_deployment
echo 🔍 验证部署结果...

set /a "checks_passed=0"
set /a "total_checks=4"

REM 检查容器状态
docker-compose ps | findstr "Up" >nul
if !errorlevel! equ 0 (
    echo ✅ 容器状态正常
    set /a "checks_passed+=1"
) else (
    echo ❌ 容器状态异常
)

REM 检查Web服务
curl -s http://localhost:5000 >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ Web服务响应正常
    set /a "checks_passed+=1"
) else (
    echo ❌ Web服务无响应
)

REM 检查端口监听
netstat -an | findstr ":5000 " >nul
if !errorlevel! equ 0 (
    echo ✅ Web端口监听正常
    set /a "checks_passed+=1"
) else (
    echo ❌ Web端口未监听
)

netstat -an | findstr ":3306 " >nul
if !errorlevel! equ 0 (
    echo ✅ 数据库端口监听正常
    set /a "checks_passed+=1"
) else (
    echo ❌ 数据库端口未监听
)

REM 计算成功率
set /a "success_rate=!checks_passed! * 100 / !total_checks!"

if !success_rate! geq 80 (
    goto show_success
) else (
    goto show_failure
)

:deploy_with_image
echo 📦 使用预构建镜像部署...
echo 拉取Docker镜像: %DOCKER_IMAGE%
docker pull "%DOCKER_IMAGE%"
if !errorlevel! neq 0 (
    echo ⚠️ 镜像拉取失败，尝试本地构建...
    goto deploy_with_build
)

echo ✅ 镜像拉取成功
docker-compose up -d
goto :eof

:deploy_with_build
echo 🔨 使用本地构建部署...
docker-compose up -d --build --force-recreate
goto :eof

:show_success
echo.
echo ================================================================
echo 🎉 部署成功完成！
echo ================================================================
echo.
echo 📊 部署统计：
echo    验证通过: !checks_passed!/!total_checks!
echo    成功率: !success_rate!%%
echo    部署模式: %DEPLOY_MODE%
echo.
echo 📍 访问地址：
echo    🌐 Web应用:     http://localhost:5000
echo    🗄️ 数据库管理:   http://localhost:8080
echo    💾 MySQL:      localhost:3306
echo.
echo 🔐 默认账号：
echo    👨‍💼 管理员1:     admin / 518107qW
echo    👨‍💼 管理员2:     longgekutta / 518107qW
echo    🗄️ 数据库:      root / 518107qW
echo.
echo 🛠️ 管理命令：
echo    %~nx0 --status    # 查看状态
echo    %~nx0 --logs      # 查看日志
echo    %~nx0 --restart   # 重启服务
echo    %~nx0 --stop      # 停止服务
echo.
echo 📋 项目信息：
echo    GitHub: https://github.com/Longgekutta/cloudfare-qq-mail
echo    DockerHub: https://hub.docker.com/r/longgekutta/cloudfare-qq-mail
echo.
echo 🎉 享受您的邮箱服务系统吧！
echo ================================================================

REM 询问是否打开浏览器
echo.
set /p "open_browser=是否打开浏览器访问应用? (y/n): "
if /i "!open_browser!"=="y" (
    start http://localhost:5000
    echo ✅ 浏览器已打开
)

echo.
echo 部署成功！ > "%DEPLOY_LOG%.result"
goto end

:show_failure
echo.
echo ================================================================
echo ❌ 部署失败！
echo ================================================================
echo.
echo 📊 验证结果：
echo    通过检查: !checks_passed!/!total_checks!
echo    成功率: !success_rate!%%
echo.
echo 🔧 故障排查：
echo    1. 查看详细日志: type "%DEPLOY_LOG%"
echo    2. 检查容器状态: docker-compose ps
echo    3. 查看服务日志: docker-compose logs -f
echo    4. 重新部署: %~nx0 --clean
echo    5. 检查Docker Desktop是否正常运行
echo.
echo 💡 常见问题：
echo    • 确保Docker Desktop完全启动
echo    • 检查端口5000和3306是否被占用
echo    • 确保有足够的磁盘空间
echo    • 检查防火墙设置
echo.
echo ================================================================

echo 部署失败！ > "%DEPLOY_LOG%.result"
goto error_exit

:manage_services
if "%1"=="start" (
    echo 🚀 启动服务...
    docker-compose up -d
    echo ✅ 服务已启动
)
if "%1"=="stop" (
    echo 🛑 停止服务...
    docker-compose down
    echo ✅ 服务已停止
)
if "%1"=="restart" (
    echo 🔄 重启服务...
    docker-compose restart
    echo ✅ 服务已重启
)
if "%1"=="status" (
    echo 📊 服务状态：
    docker-compose ps
)
if "%1"=="logs" (
    echo 📋 实时日志：
    docker-compose logs -f
)
goto :eof

:cleanup_resources
echo 🧹 清理部署资源...
docker-compose down --remove-orphans >nul 2>&1
docker system prune -f >nul 2>&1
echo ✅ 资源清理完成
goto :eof

:show_help
echo 🚀 终极部署脚本 - Cloudfare QQ Mail Service (Windows版本)
echo.
echo 用法: %~nx0 [选项]
echo.
echo 部署模式:
echo   --mode build           本地构建部署
echo   --mode image           预构建镜像部署 (推荐)
echo.
echo 配置选项:
echo   --use-image            使用预构建镜像
echo   --verbose              详细输出
echo.
echo 操作命令:
echo   --start                启动服务
echo   --stop                 停止服务
echo   --restart              重启服务
echo   --status               查看状态
echo   --logs                 查看日志
echo   --clean                清理资源
echo   --help                 显示帮助
echo.
echo 示例:
echo   %~nx0                        # 自动部署
echo   %~nx0 --use-image            # 使用镜像部署
echo   %~nx0 --start                # 仅启动服务
echo.
echo 项目信息:
echo   GitHub:    https://github.com/Longgekutta/cloudfare-qq-mail
echo   DockerHub: https://hub.docker.com/r/longgekutta/cloudfare-qq-mail
echo   Gitee:     https://gitee.com/longgekutta/cloudfare-qq-mail
echo.
goto :eof

:error_exit
echo.
echo 部署失败，查看日志获取详细信息: %DEPLOY_LOG%
pause
exit /b 1

:end
pause
exit /b 0

