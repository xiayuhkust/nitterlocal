# Nitter Local 使用指南

本文档提供了在不同操作系统上初始化和使用Nitter Local项目的详细说明。

## 目录

1. [项目概述](#项目概述)
2. [Ubuntu系统安装指南](#ubuntu系统安装指南)
3. [CentOS系统安装指南](#centos系统安装指南)
4. [数据库初始化](#数据库初始化)
5. [URL追踪表初始化](#url追踪表初始化)
6. [MySQL数据同步](#mysql数据同步)
7. [常见问题解决](#常见问题解决)

## 项目概述

Nitter Local是一个用于追踪Twitter账户并收集推文数据的工具。它使用SQLite本地数据库存储URL和推文数据，并可以将数据同步到MySQL数据库中。

主要功能包括：
- 追踪Twitter账户
- 收集推文数据
- 分析推文内容
- 将数据同步到MySQL数据库

## Ubuntu系统安装指南

### 系统要求
- Ubuntu 18.04或更高版本
- Python 3.7或更高版本
- Node.js 14或更高版本

### 安装步骤

1. **安装Node.js和npm**

```bash
# 使用nvm安装Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
source ~/.bashrc
nvm install 14
nvm use 14

# 验证安装
node -v
npm -v
```

2. **安装Python依赖**

```bash
# 安装pip
sudo apt update
sudo apt install python3-pip

# 安装项目依赖
pip3 install -r requirements.txt
```

3. **安装SQLite**

```bash
sudo apt install sqlite3
```

4. **克隆项目**

```bash
git clone https://github.com/xiayuhkust/nitterlocal.git
cd nitterlocal
```

5. **安装项目依赖**

```bash
# 安装Node.js依赖
cd src/twitter_client
npm install
cd ../..

# 安装Python依赖
pip3 install -r requirements.txt
```

## CentOS系统安装指南

### 系统要求
- CentOS 7或更高版本
- Python 3.6（CentOS 7默认版本）
- Node.js 14或更高版本

### 安装步骤

1. **安装Node.js和npm**

```bash
# 安装开发工具
sudo yum groupinstall "Development Tools"

# 使用nvm安装Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
source ~/.bashrc
nvm install 14
nvm use 14

# 验证安装
node -v
npm -v
```

2. **安装Python依赖**

CentOS 7默认使用Python 3.6，需要使用兼容Python 3.6的脚本。

```bash
# 安装pip
sudo yum install python3-pip

# 安装项目依赖
pip3 install -r requirements.txt
```

3. **安装SQLite**

```bash
sudo yum install sqlite
```

4. **克隆项目**

```bash
git clone https://github.com/xiayuhkust/nitterlocal.git
cd nitterlocal
```

5. **安装项目依赖**

```bash
# 安装Node.js依赖
cd src/twitter_client
npm install
cd ../..

# 安装Python依赖
pip3 install -r requirements.txt
```

## 数据库初始化

项目使用SQLite作为本地数据库，可以通过以下步骤初始化数据库：

```bash
# 创建数据目录
mkdir -p data

# 初始化数据库
python3 src/database/init_database.py
```

## URL追踪表初始化

### Ubuntu系统（Python 3.7+）

在Ubuntu系统上，可以使用`add_urls.py`脚本初始化URL追踪表：

```bash
python3 scripts/utils/add_urls.py --file data/sample_urls_with_cmc.json --clear
```

### CentOS系统（Python 3.6）

在CentOS系统上，需要使用兼容Python 3.6的`add_urls_py36.py`脚本：

```bash
python3 scripts/utils/add_urls_py36.py --file data/sample_urls_with_cmc.json --clear
```

这个脚本解决了Python 3.6不支持`subprocess.run`的`capture_output`参数的问题，使用`stdout=subprocess.PIPE`和`stderr=subprocess.PIPE`代替。

## MySQL数据同步

项目支持将数据从SQLite同步到MySQL数据库。首先需要配置MySQL连接参数：

1. **创建.env文件**

```bash
cp .env.template .env
```

2. **编辑.env文件，填入MySQL连接参数**

```
MYSQL_HOST=your_mysql_host
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_mysql_database
```

### 同步KOL信息到MySQL

#### Ubuntu系统（Python 3.7+）

```bash
python3 scripts/database/update_mysql_kol_info.py
```

#### CentOS系统（Python 3.6）

```bash
python3 scripts/database/update_mysql_kol_info_py36.py
```

### 同步推文数据到MySQL

#### Ubuntu系统（Python 3.7+）

```bash
python3 scripts/database/update_mysql_kol_tweet.py
```

#### CentOS系统（Python 3.6）

```bash
python3 scripts/database/update_mysql_kol_tweet_server_py36.py
```

### 使用数值ID同步数据（适用于MySQL bigint类型的kol_id列）

如果MySQL数据库中的`kol_id`列是`bigint`类型，需要使用以下脚本：

#### 同步KOL信息（数值ID）

```bash
python3 scripts/database/update_mysql_kol_info_numeric_id.py
```

#### 同步推文数据（数值ID）

```bash
python3 scripts/database/update_mysql_kol_tweet_numeric_id_fixed2.py
```

## 常见问题解决

### Python 3.6兼容性问题

**问题**：在CentOS系统上运行脚本时出现错误：`Error initializing Twitter scraper: __init__() got an unexpected keyword argument 'capture_output'`

**解决方案**：使用兼容Python 3.6的脚本，例如`add_urls_py36.py`、`update_mysql_kol_info_py36.py`等。这些脚本使用`stdout=subprocess.PIPE`和`stderr=subprocess.PIPE`代替`capture_output`参数。

### SQLite数据库列名问题

**问题**：运行脚本时出现错误：`no such column: user_id`或`no such column: stored_at`

**解决方案**：确保使用正确的列名。在新版本中，`stored_at`列已更名为`added_at`，并添加了`user_id`列。可以使用以下脚本添加缺失的列：

```bash
python3 scripts/migration/add_user_id_to_url_tracking.py
```

### MySQL连接问题

**问题**：无法连接到MySQL数据库

**解决方案**：
1. 确保MySQL服务器正在运行
2. 检查.env文件中的连接参数是否正确
3. 确保MySQL用户有足够的权限
4. 检查防火墙设置，确保MySQL端口（通常是3306）已开放

可以使用以下脚本测试MySQL连接：

```bash
python3 scripts/tests/test_mysql_connection.py
```

### Twitter API限制问题

**问题**：获取Twitter数据时遇到API限制

**解决方案**：
1. 减少请求频率
2. 使用多个Twitter API密钥轮换使用
3. 实现指数退避重试机制
