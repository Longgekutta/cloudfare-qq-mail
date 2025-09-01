# Linux移植指南

## 1. 代码兼容性分析

### ✅ 无需修改的组件
- 邮件IMAP连接和处理逻辑
- 异步队列处理
- 邮件解析和HTML生成
- 线程管理

### 🔧 需要调整的部分

#### 路径处理
```python
# Windows当前代码
file_path = f"./received_emails\\{filename}"

# Linux兼容代码 (使用os.path.join)
file_path = os.path.join("received_emails", filename)
```

#### 文件权限设置
```python
# Linux需要设置合适的文件权限
os.chmod(file_path, 0o644)  # 读写权限
```

## 2. 环境准备

### Ubuntu/Debian系统
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3 python3-pip python3-venv -y

# 安装系统依赖
sudo apt install git curl -y
```

### CentOS/RHEL系统
```bash
# 更新系统
sudo yum update -y

# 安装Python和pip
sudo yum install python3 python3-pip -y

# 安装git
sudo yum install git -y
```

## 3. 项目部署

### 创建项目目录
```bash
# 创建应用目录
sudo mkdir -p /opt/email-monitor
cd /opt/email-monitor

# 创建普通用户运行服务
sudo useradd -r -s /bin/false emailmonitor
sudo chown emailmonitor:emailmonitor /opt/email-monitor
```

### 上传代码
```bash
# 方法1: 使用git
git clone https://your-repo-url.git .

# 方法2: 使用scp从Windows传输
scp -r D:\github相关\cloudfare-qq-mail/* user@linux-server:/opt/email-monitor/
```

### 安装Python依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 如果没有requirements.txt，创建一个
pip3 install email imaplib2
```

## 4. 服务化部署

### 创建systemd服务
```bash
sudo nano /etc/systemd/system/email-monitor.service
```

### 服务配置文件
```ini
[Unit]
Description=Email Monitor Service
After=network.target

[Service]
Type=simple
User=emailmonitor
Group=emailmonitor
WorkingDirectory=/opt/email-monitor
Environment=PATH=/opt/email-monitor/venv/bin
ExecStart=/opt/email-monitor/venv/bin/python realtime_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 启动服务
```bash
# 重载服务配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start email-monitor

# 设置开机自启
sudo systemctl enable email-monitor

# 查看服务状态
sudo systemctl status email-monitor
```

## 5. 日志管理

### 查看日志
```bash
# 查看服务日志
sudo journalctl -u email-monitor -f

# 查看最近的日志
sudo journalctl -u email-monitor --since "1 hour ago"
```

### 配置日志轮转
```bash
sudo nano /etc/logrotate.d/email-monitor
```

```
/var/log/email-monitor/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 emailmonitor emailmonitor
}
```

## 6. 安全配置

### 防火墙设置
```bash
# 如果需要开放HTTP端口
sudo ufw allow 8080/tcp

# 如果需要SSH访问
sudo ufw allow ssh
sudo ufw enable
```

### 文件权限
```bash
# 设置代码文件权限
sudo chown -R emailmonitor:emailmonitor /opt/email-monitor
sudo chmod -R 755 /opt/email-monitor
sudo chmod 600 /opt/email-monitor/email_config.py  # 配置文件安全权限
```

## 7. 监控和维护

### 进程监控
```bash
# 检查进程
ps aux | grep python | grep realtime_monitor

# 检查内存使用
top -p $(pgrep -f realtime_monitor)
```

### 性能监控脚本
```bash
#!/bin/bash
# monitor.sh
while true; do
    echo "$(date): 检查邮件监控服务状态"
    systemctl is-active email-monitor
    sleep 300  # 5分钟检查一次
done
```

## 8. 故障排除

### 常见问题
1. **权限问题**: 确保emailmonitor用户有读写权限
2. **网络问题**: 检查防火墙和DNS设置
3. **依赖问题**: 确保所有Python包已安装

### 调试模式
```bash
# 手动运行调试
sudo -u emailmonitor /opt/email-monitor/venv/bin/python realtime_monitor.py
```
