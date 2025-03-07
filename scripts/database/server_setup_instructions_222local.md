# 服务器设置说明 (222local分支)

本文档提供了在服务器上设置和运行MySQL同步脚本的说明。

## 1. 安装所需的Python包

首先，安装所需的Python包：

```bash
pip3 install mysql-connector-python
pip3 install python-dotenv
```

## 2. 安装Node.js

Twitter客户端功能需要Node.js环境。使用以下命令安装Node.js：

```bash
# 添加NodeSource仓库
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
# 安装Node.js
yum install -y nodejs
```

安装完成后，验证Node.js是否正确安装：

```bash
node --version
```

您应该看到Node.js的版本号，例如v18.20.6。

安装Node.js依赖项：

```bash
cd src/twitter_client
npm install
```

如果在运行kol_info同步脚本时遇到以下错误：

```
Error getting profile for handle: Command '['node', '/root/nitterlocal/src/twitter_client/test_profile.js', '...' returned non-zero exit status 1.
```

这通常表示Node.js未正确安装或Twitter客户端脚本存在问题。您可以使用以下命令测试Twitter客户端脚本：

```bash
cd src/twitter_client && node test_profile.js cz_binance
```

## 3. 创建.env文件

在项目根目录中创建一个.env文件，其中包含MySQL连接参数：

```bash
cat > .env << EOL
MYSQL_HOST=43.135.26.222
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=kol_info
EOL
```

请确保将`your_password_here`替换为实际的MySQL密码。

## 3. Python 3.6兼容脚本

由于服务器使用Python 3.6.8，我们提供了特别兼容的脚本版本：

- `scripts/database/update_mysql_kol_tweet_server_py36.py` - 用于同步tweets表
- `scripts/database/update_mysql_kol_info_py36.py` - 用于同步kol_info表

这些脚本已经移除了所有Python 3.6不支持的特性，包括f-strings和类型注解，并修复了SQLite查询错误。

## 4. 测试脚本

### 4.1 测试tweets同步脚本

使用`--test`标志测试脚本，以确保它可以从SQLite检索tweets而不将它们插入MySQL：

```bash
python3 scripts/database/update_mysql_kol_tweet_server_py36.py --test --limit 5
```

您应该看到类似以下的输出：

```
Starting MySQL update script for tweets
MySQL Host: 43.135.26.222
MySQL Port: 3306
MySQL User: root
MySQL Database: kol_info
SQLite Database: /path/to/data/local_database.db
Got 5 tweets from SQLite
Test mode - not connecting to MySQL database
Test mode - would insert or update record for kol_id: cz_binance, tweet_id: 1614148296788041734
...
Processed 5 tweets
MySQL update script for tweets completed
```

### 4.2 测试kol_info同步脚本

```bash
python3 scripts/database/update_mysql_kol_info_py36.py --test --limit 5
```

## 5. 运行脚本

### 5.1 运行tweets同步脚本

如果测试成功，运行脚本将tweets插入MySQL：

```bash
python3 scripts/database/update_mysql_kol_tweet_server_py36.py --limit 10
```

您也可以运行脚本而不设置限制来处理所有tweets：

```bash
python3 scripts/database/update_mysql_kol_tweet_server_py36.py
```

### 5.2 运行kol_info同步脚本

```bash
python3 scripts/database/update_mysql_kol_info_py36.py
```

## 6. 检查MySQL数据库

检查MySQL数据库以确保数据正确插入：

```bash
# 检查tweets表
mysql -h 43.135.26.222 -u root -p -e "SELECT * FROM kol_info.kol_tweet LIMIT 10;"

# 检查kol_info表
mysql -h 43.135.26.222 -u root -p -e "SELECT * FROM kol_info.kol_info LIMIT 10;"
```

系统会提示您输入密码。

## 7. 故障排除

如果遇到任何问题：

1. 检查.env文件是否存在并包含正确的MySQL连接参数
2. 验证SQLite数据库是否存在并包含数据
3. 确保MySQL数据库和相关表存在
4. 检查日志中是否有任何错误消息

### 7.1 常见问题

#### 如果您看到错误`no such column: t.user_id`或`no such column: user_id`

这意味着您的SQLite数据库架构与脚本预期的不匹配。222local分支的Python 3.6兼容脚本已经修改为使用正确的列名，这应该可以解决这个问题。

#### 如果您看到错误`__init__() got an unexpected keyword argument 'capture_output'`

这是因为Python 3.6不支持subprocess.run的capture_output参数。我们已经修复了Python 3.6兼容版本的脚本，使用stdout=subprocess.PIPE和stderr=subprocess.PIPE代替。

#### 如果您看到MySQL连接错误

确保您的.env文件中的MySQL连接参数正确，并且MySQL服务器正在运行并可以从您的服务器访问。

## 8. 脚本选项

这些脚本支持以下命令行选项：

### 8.1 tweets同步脚本选项

- `--limit N`：将要处理的tweets数量限制为N
- `--since-days N`：仅处理最近N天的tweets
- `--test`：测试模式 - 不在MySQL中插入或更新记录

例如，要仅处理最近7天的tweets：

```bash
python3 scripts/database/update_mysql_kol_tweet_server_py36.py --since-days 7
```

### 8.2 kol_info同步脚本选项

- `--limit N`：将要处理的URL数量限制为N
- `--test`：测试模式 - 不在MySQL中插入或更新记录

## 9. 数据库重新生成

如果需要重新生成数据库，可以使用以下命令：

### 9.1 重新生成url_tracking表

```bash
python scripts/utils/add_urls.py --file data/sample_urls_with_cmc.json --clear
```

### 9.2 添加缺失的列到tweets表

```bash
python scripts/migration/add_user_id_to_tweets.py
python scripts/migration/add_reply_fields_to_tweets.py
```

### 9.3 检查数据库架构

```bash
# 检查url_tracking表
sqlite3 data/local_database.db "PRAGMA table_info(url_tracking);"

# 检查tweets表
sqlite3 data/local_database.db "PRAGMA table_info(tweets);"
```
