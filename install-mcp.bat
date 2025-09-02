@echo off
chcp 65001 >nul
title MCP服务器自动安装脚本

echo 🔧 MCP服务器自动安装脚本
echo ================================

:: 检查MCP目录是否存在
if not exist "mcp-feedback-enhanced" (
    echo ❌ 未找到mcp-feedback-enhanced目录
    echo 💡 请确保在正确的项目根目录运行此脚本
    pause
    exit /b 1
)

echo ✅ 找到MCP服务器目录
echo.

:: 进入MCP目录
cd mcp-feedback-enhanced

echo 📦 开始安装MCP依赖...
echo.

:: 方法1：尝试使用豆瓣镜像源安装依赖
echo 🌐 使用豆瓣镜像源安装依赖...
pip install -i https://pypi.douban.com/simple/ --trusted-host pypi.douban.com fastmcp psutil fastapi uvicorn jinja2 websockets aiohttp mcp hatchling maturin setuptools-rust

if errorlevel 1 (
    echo ⚠️ 豆瓣镜像源安装失败，尝试阿里云镜像源...
    pip install -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com fastmcp psutil fastapi uvicorn jinja2 websockets aiohttp mcp hatchling maturin setuptools-rust
    
    if errorlevel 1 (
        echo ❌ 所有镜像源都失败，尝试官方源...
        pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org fastmcp psutil fastapi uvicorn jinja2 websockets aiohttp mcp hatchling maturin setuptools-rust
        
        if errorlevel 1 (
            echo ❌ 依赖安装失败，请检查网络连接
            pause
            exit /b 1
        )
    )
)

echo ✅ 依赖安装成功
echo.

:: 安装MCP服务器
echo 🔨 安装MCP服务器模块...
pip install -e .

if errorlevel 1 (
    echo ❌ MCP服务器安装失败
    echo 💡 尝试直接运行模块...
    
    :: 测试是否可以直接运行
    python -c "import sys; sys.path.insert(0, 'src'); import mcp_feedback_enhanced; print('✅ MCP模块可以直接使用')"
    
    if errorlevel 1 (
        echo ❌ MCP模块无法使用
        pause
        exit /b 1
    )
) else (
    echo ✅ MCP服务器安装成功
)

echo.
echo 🧪 测试MCP服务器...
python -c "import mcp_feedback_enhanced; print('✅ MCP服务器模块导入成功')"

if errorlevel 1 (
    echo ⚠️ 模块导入失败，但可能仍可使用
)

echo.
echo 🎉 MCP安装完成！
echo.
echo 📋 Augment配置信息：
echo ================================
echo 在Augment设置中添加以下MCP服务器配置：
echo.
echo {
echo   "mcpServers": {
echo     "mcp-feedback-enhanced": {
echo       "command": "python",
echo       "args": ["-m", "mcp_feedback_enhanced"],
echo       "cwd": "%CD%",
echo       "timeout": 600,
echo       "env": {
echo         "MCP_DESKTOP_MODE": "false",
echo         "MCP_WEB_HOST": "127.0.0.1",
echo         "MCP_WEB_PORT": "8765",
echo         "MCP_DEBUG": "true"
echo       },
echo       "autoApprove": ["interactive_feedback"]
echo     }
echo   }
echo }
echo.
echo 💡 配置完成后重启Augment即可使用MCP工具
echo.

:: 返回原目录
cd ..

echo 按任意键退出...
pause >nul
