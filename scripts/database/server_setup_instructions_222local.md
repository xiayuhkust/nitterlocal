# 服务器设置说明 (222local分支)

本文档提供了在服务器上设置和运行MySQL tweet同步脚本的说明。

## 1. 安装所需的Python包

首先，安装所需的Python包：

```bash
pip3 install mysql-connector-python
pip3 install python-dotenv
```

## 2. 创建.env文件

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

## 3. 测试脚本

使用`--test`标志测试脚本，以确保它可以从SQLite检索tweets而不将它们插入MySQL：

```bash
python3 scripts/database/update_mysql_kol_tweet_server.py --test --limit 5
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

## 4. 运行脚本

如果测试成功，运行脚本将tweets插入MySQL：

```bash
python3 scripts/database/update_mysql_kol_tweet_server.py --limit 10
```

您也可以运行脚本而不设置限制来处理所有tweets：

```bash
python3 scripts/database/update_mysql_kol_tweet_server.py
```

## 5. 检查MySQL数据库

检查MySQL数据库以确保tweets正确插入：

```bash
mysql -h 43.135.26.222 -u root -p -e "SELECT * FROM kol_info.kol_tweet LIMIT 10;"
```

系统会提示您输入密码。

## 6. 故障排除

如果遇到任何问题：

1. 检查.env文件是否存在并包含正确的MySQL连接参数
2. 验证SQLite数据库是否存在并包含tweets
3. 确保MySQL数据库和kol_tweet表存在
4. 检查日志中是否有任何错误消息

### 常见问题

#### 如果您看到错误`no such column: t.user_id`

这意味着您的SQLite数据库架构与脚本预期的不匹配。222local分支的服务器特定脚本`update_mysql_kol_tweet_server.py`已经修改为使用tweets表中的`author`列，而不是`user_id`列，这应该可以解决这个问题。

#### 如果您看到MySQL连接错误

确保您的.env文件中的MySQL连接参数正确，并且MySQL服务器正在运行并可以从您的服务器访问。

## 7. 脚本选项

该脚本支持以下命令行选项：

- `--limit N`：将要处理的tweets数量限制为N
- `--since-days N`：仅处理最近N天的tweets
- `--test`：测试模式 - 不在MySQL中插入或更新记录

例如，要仅处理最近7天的tweets：

```bash
python3 scripts/database/update_mysql_kol_tweet_server.py --since-days 7
```

## 8. 222local分支中的脚本更改

222local分支中的`update_mysql_kol_tweet_server.py`脚本已更新为：

1. 使用tweets表中的`author`列而不是`user_id`列
2. 添加对从.env文件加载环境变量的支持
3. 改进错误处理和日志记录

这些更改确保脚本正确使用作者名称作为kol_id，这在当前数据库架构中是可用的。
