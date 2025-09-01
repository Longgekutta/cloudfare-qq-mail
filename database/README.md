# 数据库设置和使用说明

## 目录结构

```
database/
├── create_tables.sql     # 创建数据库和表格的SQL脚本
├── setup_database.py     # 设置数据库的Python脚本
├── db_manager.py         # 数据库管理模块
└── README.md            # 本说明文件
```

## 数据库设置步骤

### 1. 确保MySQL服务正在运行

在运行数据库设置脚本之前，请确保MySQL服务正在运行。

### 2. 配置数据库连接

在 `email_config.py` 文件中配置数据库连接信息：

```python
# 数据库配置
DB_HOST = "localhost"      # 数据库主机地址
DB_USER = "root"           # 数据库用户名
DB_PASSWORD = "your_password"  # 数据库密码
DB_NAME = "cloudfare_qq_mail"  # 数据库名称
```

请根据实际情况修改 `DB_PASSWORD` 的值。

### 3. 安装依赖

确保已安装MySQL连接器：

```bash
pip install mysql-connector-python
```

### 4. 创建数据库和表格

运行以下命令创建数据库和表格：

```bash
cd cloudfare-qq-mail
python database/setup_database.py
```

### 5. 测试数据库连接

运行以下命令测试数据库连接和基本查询：

```bash
cd cloudfare-qq-mail
python database/db_manager.py
```
如果一切正常，您将看到类似以下的输出：

```
📋 邮件处理配置已加载
✉️  监控邮箱: 2846117874@qq.com
📁 保存目录: ./received_emails
🗄️ 数据库名称: cloudfare_qq_mail
✅ 数据库连接成功
域名列表:
  - shiep.edu.kg
  - example.com
  - test.org
🔒 数据库连接已关闭
```

## 数据库表结构

### 1. 用户数据表 (users)

存储用户与管理员的信息：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INT (主键, 自增) | 用户ID |
| username | VARCHAR(50) | 用户名 |
| password | VARCHAR(255) | 密码（加密存储） |
| is_vip | BOOLEAN | 是否为VIP用户 |
| balance | DECIMAL(10, 2) | 账号余额 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 2. 域名表 (domains)

存储域名信息：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INT (主键, 自增) | 域名ID |
| domain_name | VARCHAR(100) | 域名名称 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 3. 邮件表 (emails)

存储邮件信息：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INT (主键, 自增) | 邮件ID |
| sender_email | VARCHAR(100) | 发件人邮箱 |
| receiver_email | VARCHAR(100) | 收件人邮箱 |
| subject | VARCHAR(255) | 邮件主题 |
| content | TEXT | 邮件内容 |
| sent_time | TIMESTAMP | 邮件发送时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 4. 用户拥有的邮箱表 (user_emails)

存储用户创建的邮箱信息：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INT (主键, 自增) | 记录ID |
| user_id | INT (外键) | 用户ID |
| email_address | VARCHAR(100) | 邮箱地址 |
| domain_id | INT (外键) | 域名ID |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 使用数据库管理模块

在代码中使用 `db_manager.py` 模块操作数据库：

```python
from database.db_manager import DatabaseManager

# 创建数据库管理器实例
db_manager = DatabaseManager()

# 连接数据库
if db_manager.connect():
    # 执行数据库操作
    # ...
    
    # 断开连接
    db_manager.disconnect()
```

## 注意事项

1. 请确保MySQL服务正在运行
2. 请确保配置的数据库用户具有创建数据库和表格的权限
3. 生产环境中，请使用强密码并妥善保管
4. 建议定期备份数据库