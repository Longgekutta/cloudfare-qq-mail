# 邮箱监控系统

这是一个基于Python和Flask的邮箱监控系统，可以实时监控特定域名的邮件并将其解析为可读格式。

## 功能特点

- 实时监控特定域名的邮件
- 邮件内容解析和HTML生成
- 用户认证和权限管理
- 多域名支持
- 数据库存储邮件和用户信息

## 技术栈

- 后端：Python 3, Flask
- 数据库：MySQL
- 前端：HTML5, CSS3, JavaScript, Bootstrap 5
- 邮件协议：IMAP

## 安装和运行

### 环境要求

- Python 3.7+
- MySQL 5.7+
- pip包管理器

### 安装步骤

1. 克隆项目代码：
   ```
   git clone <项目地址>
   cd cloudfare-qq-mail
   ```

2. 安装Python依赖：
   ```
   pip install -r requirements.txt
   ```

3. 配置数据库连接：
   - 修改`email_config.py`文件中的数据库连接信息
   - 确保MySQL服务正在运行

4. 创建数据库和表格：
   ```
   cd cloudfare-qq-mail
   python database/setup_database.py
   ```

5. 运行Flask应用：
   ```
   python app.py
   ```

6. 访问应用：
   在浏览器中打开 `http://localhost:5000`

## 项目结构

```
cloudfare-qq-mail/
├── app.py                 # Flask应用主文件
├── component_connector.py # 组件连接器
├── email_config.py        # 邮箱和数据库配置文件
├── realtime_monitor.py    # 实时邮件监控器
├── email_parser.py        # 邮件解析器
├── auto_email_processor.py# 自动邮件处理器
├── qq_email_monitor.py    # QQ邮箱监控器
├── requirements.txt       # Python依赖包列表
├── README.md              # 项目说明文件
├── database/              # 数据库相关文件
│   ├── db_manager.py      # 数据库管理模块
│   ├── setup_database.py  # 数据库设置脚本
│   └── create_tables.sql  # 创建数据库和表格的SQL脚本
├── frontend/              # 前端相关文件
│   ├── templates/         # HTML模板文件
│   └── static/            # 静态文件（CSS, JS, 图片等）
└── ...
```

## 系统组件

### 1. 实时邮件监控器 (RealtimeEmailMonitor)
负责监控QQ邮箱中的新邮件，每6秒检查一次，只处理启动后收到的目标域名邮件。采用异步队列处理架构，支持高并发邮件处理。

### 2. 邮件解析器 (EmailParser)
负责解析.eml格式的邮件文件，提取邮件内容并生成HTML显示文件。支持文本邮件和HTML邮件的解析，能够处理附件和嵌入图片。

### 3. 自动邮件处理器 (AutoEmailProcessor)
整合了邮件监控、下载、转换、解析和存储的完整流程。提供了一键式邮件处理解决方案。

### 4. Web应用 (Flask App)
提供用户界面，支持用户认证、权限管理和邮件展示。基于Flask框架开发，使用Bootstrap 5实现响应式设计。

### 5. 组件连接器 (ComponentConnector)
连接各个组件，实现完整的邮件监控系统。负责协调邮件监控、数据处理和存储等各个组件的工作。

## 数据库设计

### 用户表 (users)
存储用户信息，包括用户名、密码、VIP状态和余额。

### 域名表 (domains)
存储支持的域名信息。

### 邮件表 (emails)
存储邮件信息，包括发件人、收件人、主题和内容。

### 用户邮箱表 (user_emails)
存储用户创建的邮箱信息。

## API接口

### 用户认证
- `POST /login` - 用户登录
- `POST /register` - 用户注册
- `GET /logout` - 用户退出登录

### 邮件管理
- `GET /mails` - 获取邮件列表
- `GET /mail/<int:mail_id>` - 获取邮件详情

### 用户管理（仅管理员）
- `GET /admin/users` - 获取用户列表
- `POST /api/admin/users` - 添加用户
- `PUT /api/admin/users/<int:user_id>` - 更新用户
- `DELETE /api/admin/users/<int:user_id>` - 删除用户

### 域名管理（仅管理员）
- `GET /admin/domains` - 获取域名列表
- `POST /api/admin/domains` - 添加域名

## 开发指南

### 前端开发
前端页面使用HTML模板和Bootstrap 5框架开发，位于`frontend/templates/`目录下。

### 后端开发
后端使用Flask框架开发，主要逻辑在`app.py`文件中实现。

### 数据库操作
数据库操作通过`database/db_manager.py`模块实现，提供了常用的数据库操作方法。

## 系统启动

### 启动邮件监控系统
```bash
python realtime_monitor.py
```

### 启动Web应用
```bash
python app.py
```

### 启动完整系统（推荐）
```bash
python component_connector.py
```

## 贡献者

- 高升

## 许可证

MIT License
