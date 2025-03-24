# Twitter Data Extraction and Backend Service

本项目提供了用于提取和分析Twitter数据的工具，以及用于处理包含Twitter URL的Excel文件的后端服务。

## 目录

- [概述](#概述)
- [先决条件](#先决条件)
- [安装](#安装)
- [手动更新操作指南](#手动更新操作指南)
- [.env配置说明](#env配置说明)
- [Crontab定时任务配置](#crontab定时任务配置)
- [后端网页服务](#后端网页服务)
- [服务器迁移与重新配置](#服务器迁移与重新配置)
- [核心脚本说明](#核心脚本说明)
- [URL格式](#url格式)
- [数据库架构](#数据库架构)
- [数据分析](#数据分析)
- [CoinMarketCap集成](#coinmarketcap集成)
- [Twitter客户端](#twitter客户端)
- [MySQL同步](#mysql同步)
- [URL表重新生成](#url表重新生成)
- [服务器IP配置](#服务器ip配置)
- [测试](#测试)
- [简化工作流程](#简化工作流程)

## 概述

该系统从Twitter账户中提取推文，并将其存储在本地数据库中进行分析。它支持各种类型的Twitter账户，包括KOL（关键意见领袖）、机构、交易所和迷因代币。后端服务允许用户上传包含Twitter URL的Excel文件，处理它们，并更新本地数据库。

## 先决条件

- Python 3.8或更高版本
- Node.js 14或更高版本
- Twitter凭据（用户名、密码、电子邮件）
- 用于同步的MySQL数据库

## 安装

1. 克隆仓库:
   ```
   git clone https://github.com/xiayuhkust/nitterlocal.git
   cd nitterlocal
   ```

2. 安装Python依赖:
   ```
   pip install -r app/requirements.txt
   ```

3. 在根目录中创建一个`.env`文件，包含您的凭据:
   ```
   TWITTER_USERNAME=your_username
   TWITTER_PASSWORD=your_password
   TWITTER_EMAIL=your_email
   MYSQL_HOST=your_mysql_host
   MYSQL_PORT=3306
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_mysql_database
   ```

## 手动更新操作指南

### 使用main.py进行手动更新

`main.py`是系统的主要入口点，用于执行Twitter数据的手动更新。它提供了多种参数来自定义更新过程。

#### 基本用法

使用默认设置运行每日更新过程:
```bash
python main.py
```

这将:
1. 从数据库获取活跃的URL
2. 以10个为一批处理URL
3. 每个URL最多提取10条推文
4. 将推文存储在数据库中
5. 生成统计数据

#### 高级用法

自定义每日更新过程:
```bash
python main.py --batch-size 20 --max-tweets 50 --max-replies 10
```

#### 可用参数

| 参数 | 描述 | 默认值 |
|------|-------------|---------|
| `--batch-size` | 处理URL的批量大小 | 10 |
| `--sleep` | URL之间的睡眠时间（秒） | 2 |
| `--max-tweets` | 每个URL的最大推文数 | 10 |
| `--max-replies` | 每个URL的最大回复推文数 | 5 |
| `--limit` | 限制要处理的URL数量 | 无限制 |
| `--db-path` | 本地数据库的路径 | data/local_database.db |
| `--performance` | 启用详细的性能监控 | 禁用 |
| `--parallel` | 启用URL的并行处理 | 禁用 |
| `--threads` | 并行处理的线程数 | 2 |

#### 示例

1. 使用并行处理和性能监控:
   ```bash
   python main.py --parallel --threads 4 --performance
   ```

2. 限制处理的URL数量:
   ```bash
   python main.py --limit 50 --max-tweets 20
   ```

3. 使用自定义数据库路径:
   ```bash
   python main.py --db-path /path/to/your/database.db
   ```

## .env配置说明

`.env`文件包含系统运行所需的所有敏感配置信息。以下是主要参数的详细说明：

### Twitter凭据

```
TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password
TWITTER_EMAIL=your_email
```

这些凭据用于登录Twitter并提取推文。确保使用有效的Twitter账户。

### MySQL数据库连接

```
MYSQL_HOST=your_mysql_host
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_mysql_database
```

这些参数用于连接到MySQL数据库进行数据同步。

### 错误报告邮箱设置

```
ERROR_EMAIL_SENDER=sender@example.com
ERROR_EMAIL_PASSWORD=your_email_password
ERROR_EMAIL_RECIPIENT=recipient@example.com
ERROR_EMAIL_SMTP_SERVER=smtp.example.com
ERROR_EMAIL_SMTP_PORT=587
```

这些设置用于配置错误报告邮件。当系统遇到错误时，它会发送电子邮件通知到指定的收件人。

### 示例完整配置

```
# Twitter凭据
TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password
TWITTER_EMAIL=your_email

# MySQL数据库连接
MYSQL_HOST=your_mysql_host
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_mysql_database

# 错误报告邮箱设置
ERROR_EMAIL_SENDER=sender@example.com
ERROR_EMAIL_PASSWORD=your_email_password
ERROR_EMAIL_RECIPIENT=recipient@example.com
ERROR_EMAIL_SMTP_SERVER=smtp.example.com
ERROR_EMAIL_SMTP_PORT=587

# 其他配置
LOG_LEVEL=INFO
BATCH_SIZE=10
MAX_TWEETS_PER_URL=50
```

### 修改.env文件

1. 使用文本编辑器打开.env文件:
   ```bash
   nano .env
   ```

2. 修改所需的参数

3. 保存并关闭文件:
   - 在nano中: `Ctrl+O`保存, `Ctrl+X`退出
   - 在vim中: `:wq`保存并退出

4. 测试配置是否正确:
   ```bash
   python scripts/tests/test_env_config.py
   ```

## Crontab定时任务配置

系统使用crontab来调度定期任务。以下是主要的crontab配置示例：

```
# 每6小时分析账户活动
0 */6 * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/analyze_activity.py --days 7 >> data/activity_analysis.log 2>&1

# 每15分钟运行动态更新（包含配置文件更新）
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance --update-profile >> data/dynamic_update.log 2>&1

# 每2小时同步url_tracking表（错开30分钟）
30 */2 * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_url_tracking_only.py --lock-timeout 60 >> data/url_tracking_sync.log 2>&1

# 每2小时同步kol_character表
0 */2 * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_kol_character_only.py --lock-timeout 60 >> data/kol_character_sync.log 2>&1

# 每15分钟同步tweets表（使用30天窗口）
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_tweets_only.py --since-days 30 --lock-timeout 60 >> data/tweets_sync.log 2>&1
```

### 如何修改Crontab配置

1. 编辑crontab配置:
   ```bash
   crontab -e
   ```

2. 添加或修改上述任务

3. 保存并关闭编辑器

4. 验证crontab配置:
   ```bash
   crontab -l
   ```

### 使用更新脚本

或者，您可以使用提供的脚本来更新crontab配置:

```bash
./update_crontab.sh
```

这个脚本会自动更新crontab配置。

### Crontab语法说明

crontab使用以下格式:
```
分钟 小时 日期 月份 星期 命令
```

例如:
- `0 */6 * * *`: 每6小时执行一次（在每小时的第0分钟）
- `*/15 * * * *`: 每15分钟执行一次
- `30 */2 * * *`: 每2小时执行一次（在每小时的第30分钟）

## 后端网页服务

后端网页服务是一个FastAPI应用程序，用于处理包含Twitter URL的Excel文件。

### 安装依赖

```bash
cd nitterlocal
pip install -r app/requirements.txt
```

### 启动后端服务

#### 方法1: 使用启动脚本

```bash
./start_backend.sh
```

后端服务将在http://0.0.0.0:8000上可用

#### 方法2: 使用systemd服务（推荐用于生产环境）

1. 安装服务:
   ```bash
   sudo ./install_service.sh
   ```

2. 启动服务:
   ```bash
   sudo systemctl start nitterlocal-backend
   ```

3. 检查服务状态:
   ```bash
   sudo systemctl status nitterlocal-backend
   ```

4. 启用服务在启动时自动启动:
   ```bash
   sudo systemctl enable nitterlocal-backend
   ```

5. 查看服务日志:
   ```bash
   sudo journalctl -u nitterlocal-backend
   ```

6. 卸载服务:
   ```bash
   sudo ./uninstall_service.sh
   ```

### 手动启动后端服务

如果您想手动启动后端服务，可以使用以下命令:

```bash
cd /home/ubuntu/nitterlocal
python -m app.main
```

这将启动FastAPI应用程序，并在http://0.0.0.0:8000上提供服务。

### 后端服务功能

- 上传包含Twitter URL的Excel文件
- 从URL中提取Twitter用户ID
- 处理并更新本地数据库表（url_tracking和kol_character）
- 与MySQL数据库同步数据
- 下载带有提取ID的处理后的Excel文件

## 服务器迁移与重新配置

如果您需要将系统迁移到新服务器或重新配置现有服务器，请按照以下步骤操作：

### 1. 准备新服务器

1. 安装必要的软件:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv git
   ```

2. 克隆仓库:
   ```bash
   git clone https://github.com/xiayuhkust/nitterlocal.git
   cd nitterlocal
   ```

### 2. 设置Python环境

1. 创建虚拟环境:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. 安装依赖:
   ```bash
   pip install -r app/requirements.txt
   ```

### 3. 配置数据库

1. 如果您有现有的数据库备份，恢复它:
   ```bash
   cp /path/to/backup/local_database.db data/local_database.db
   ```

2. 或者，初始化一个新的数据库:
   ```bash
   python scripts/database/initialize_database.py
   ```

### 4. 配置.env文件

1. 创建.env文件:
   ```bash
   cp .env.example .env
   nano .env
   ```

2. 更新配置参数（参见[.env配置说明](#env配置说明)部分）

### 5. 设置后端服务

1. 安装systemd服务:
   ```bash
   sudo ./install_service.sh
   ```

2. 启动服务:
   ```bash
   sudo systemctl start nitterlocal-backend
   ```

3. 检查服务状态:
   ```bash
   sudo systemctl status nitterlocal-backend
   ```

### 6. 配置Crontab

1. 更新crontab配置:
   ```bash
   ./update_crontab.sh
   ```

2. 或者手动编辑crontab:
   ```bash
   crontab -e
   ```

3. 添加必要的任务（参见[Crontab定时任务配置](#crontab定时任务配置)部分）

### 7. 验证配置

1. 测试后端服务:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. 测试数据库连接:
   ```bash
   python scripts/tests/test_database_connection.py
   ```

3. 测试MySQL同步:
   ```bash
   python scripts/sync/sync_to_mysql_combined.py --test
   ```

### 8. 数据迁移（如果需要）

如果您需要从旧服务器迁移数据:

1. 在旧服务器上备份数据库:
   ```bash
   cp /home/ubuntu/nitterlocal/data/local_database.db /tmp/local_database_backup.db
   ```

2. 将备份传输到新服务器:
   ```bash
   scp /tmp/local_database_backup.db user@new-server:/tmp/
   ```

3. 在新服务器上恢复备份:
   ```bash
   cp /tmp/local_database_backup.db /home/ubuntu/nitterlocal/data/local_database.db
   ```

## 核心脚本说明

以下是系统中核心脚本的位置和功能说明：

### 主要脚本

- `main.py`: 系统的主入口点，用于执行Twitter数据的手动更新。
- `app/main.py`: FastAPI后端服务的入口点，用于处理Excel文件上传和处理。

### Crontab相关脚本

- `scripts/activity/analyze_activity.py`: 分析Twitter账户活动，每6小时运行一次。
- `scripts/activity/dynamic_update.py`: 执行动态更新，包括配置文件更新，每15分钟运行一次。
- `scripts/sync/sync_url_tracking_only.py`: 仅同步url_tracking表，每2小时运行一次。
- `scripts/sync/sync_kol_character_only.py`: 仅同步kol_character表，每2小时运行一次。
- `scripts/sync/sync_tweets_only.py`: 仅同步tweets表，每15分钟运行一次。
- `scripts/sync/sync_to_mysql_combined.py`: 综合同步脚本，可以同步所有表。

### 后端网页服务相关脚本

- `app/main.py`: FastAPI应用程序的主入口点。
- `app/excel_processor.py`: 处理Excel文件并提取Twitter URL。
- `app/excel_db_processor.py`: 处理Excel文件并更新数据库。
- `app/twitter_utils.py`: Twitter URL处理工具。
- `start_backend.sh`: 启动后端服务的脚本。
- `install_service.sh`: 安装systemd服务的脚本。
- `uninstall_service.sh`: 卸载systemd服务的脚本。

### 数据库维护脚本

- `scripts/database/maintenance/check_mysql_columns.py`: 检查MySQL列。
- `scripts/database/maintenance/fix_kol_character_table.py`: 修复kol_character表。
- `scripts/database/maintenance/fix_url_tracking_table.py`: 修复url_tracking表。
- `scripts/database/initialize_database.py`: 初始化数据库。
- `scripts/database/regenerate_url_table.py`: 重新生成URL表。

### 测试脚本

- `scripts/tests/database/test_database_reset.py`: 测试数据库重置。
- `scripts/tests/database/test_database_structure.py`: 测试数据库结构。
- `scripts/tests/test_database_connection.py`: 测试数据库连接。
- `scripts/tests/test_env_config.py`: 测试环境配置。

## URL格式

系统使用Twitter URL（https://twitter.com/username）而不是Nitter URL。
数据库中的所有现有URL将在运行迁移脚本时自动转换为Twitter格式。

### 迁移

要将数据库中的现有URL从Nitter格式迁移到Twitter格式，请运行:

```bash
python scripts/migrations/convert_urls_to_twitter.py
```

要验证所有URL是否已转换为Twitter格式，请运行:

```bash
python scripts/tests/test_url_migration.py
```

### 添加URL

添加新URL时，请使用Twitter格式（https://twitter.com/username）:

```bash
python scripts/utils/add_urls.py --file data/sample_urls_with_cmc.json
```

## 数据库架构

数据库架构包括以下表:

- `url_tracking`: 存储要跟踪的Twitter URL的信息
- `tweets`: 存储从跟踪的URL中提取的推文
- `kol_character`: 存储KOL的字符信息

## 数据分析

系统提供了各种工具来分析提取的推文:

- 计算每个URL的推文数
- 分析标签
- 将推文导出为JSON或CSV
- 删除重复的推文

有关详细的数据分析说明:

1. 计算每个URL的推文数:
   ```bash
   python scripts/analysis/count_tweets.py
   ```

2. 分析标签:
   ```bash
   python scripts/analysis/analyze_hashtags.py
   ```

3. 将推文导出为JSON:
   ```bash
   python scripts/export/export_tweets_to_json.py --output data/tweets.json
   ```

4. 删除重复的推文:
   ```bash
   python scripts/cleanup/remove_duplicate_tweets.py
   ```

## CoinMarketCap集成

系统可以从CoinMarketCap获取顶级交易所和迷因代币，并将它们添加到数据库中:

```bash
python scripts/utils/fetch_coinmarketcap_data.py
```

## Twitter客户端

系统使用Twitter客户端直接从Twitter提取推文。客户端需要在`.env`文件中设置身份验证凭据。

### 基本用法

使用默认设置运行每日更新过程:
```
python main.py
```

这将:
1. 从数据库获取活跃的URL
2. 以10个为一批处理URL
3. 每个URL最多提取50条推文
4. 将推文存储在数据库中
5. 生成统计数据

### 高级用法

自定义每日更新过程:
```bash
python main.py --batch-size 20 --max-tweets 100
```

## MySQL同步

系统将数据从本地SQLite数据库同步到MySQL数据库。同步过程处理`kol_character`、`url_tracking`和`tweets`表。

### 同步脚本

主要的同步脚本是`scripts/sync/sync_to_mysql_combined.py`。这个脚本:

1. 连接到本地SQLite数据库和远程MySQL数据库
2. 同步`kol_character`表
3. 将`url_tracking`表同步到MySQL中的`kol_info`表
4. 将`tweets`表同步到MySQL中的`kol_tweet`表
5. 处理SQLite和MySQL之间的列名差异
6. 使用锁机制防止重叠执行
7. 实现动态列映射以处理不同的表结构

### 锁机制

同步过程使用基于文件的锁机制来防止多个同步作业同时运行。这在数据量增长且同步时间超过cron间隔时尤为重要。

锁机制的主要特点:
- 使用`fcntl`的文件锁定来防止重叠执行
- 包括超时功能以防止无限等待
- 在锁文件中存储进程ID（PID）以便调试
- 优雅地处理锁获取失败

### 手动同步

要手动触发同步:
```bash
python scripts/sync/sync_to_mysql_combined.py
```

要在测试模式下运行（不进行实际更改）:
```bash
python scripts/sync/sync_to_mysql_combined.py --test
```

要仅同步推文:
```bash
python scripts/sync/sync_to_mysql_combined.py --tweets-only
```

要使用特定的时间窗口同步:
```bash
python scripts/sync/sync_to_mysql_combined.py --since-days 30
```

要禁用锁机制:
```bash
python scripts/sync/sync_to_mysql_combined.py --no-lock
```

要设置自定义锁超时（以秒为单位）:
```bash
python scripts/sync/sync_to_mysql_combined.py --lock-timeout 120
```

### 错误处理

同步脚本包括强大的错误处理:
- 优雅地处理MySQL表中缺少的列
- 使用动态列映射仅同步兼容的列
- 当kol_id查找失败时回退到user_id
- 提供同步操作的详细日志
- 自动处理"Unread result found"错误

### 数据库检查工具

系统包括用于检查本地SQLite数据库和远程MySQL数据库状态的工具:

要检查本地SQLite数据库中的最新推文:
```bash
python scripts/sync/check_local_tweets.py
```

要检查MySQL数据库中的最新推文:
```bash
python scripts/sync/check_mysql_tweets.py
```

要检查MySQL表的架构:
```bash
python scripts/sync/check_mysql_schema.py kol_tweet
```

要检查SQLite表的架构:
```bash
python scripts/sync/check_sqlite_tables.py tweets
```

这些工具通过显示最新的推文、总推文计数和按日期的推文分布来帮助诊断同步问题。

### 故障排除

如果您遇到同步问题:

1. 检查`.env`文件中的MySQL连接参数
2. 验证MySQL服务器是否可访问
3. 检查两个数据库中的列名
4. 查看`data/sync_cron.log`中的同步日志
5. 查看`data/logs/sync_details.log`中的详细日志
6. 检查`data/sync_lock.pid`是否存在锁文件，如果没有同步正在运行，则删除它
7. 使用数据库检查工具比较本地和远程数据
8. 验证SQLite中的tweets表是否有最新数据

可以安全忽略的常见警告:
- "Could not find kol_id for screen_name" - 系统将使用user_id作为后备
- "Unread result found" - 同步脚本会自动处理这个问题
- "Error getting numeric ID for handle" - 使用替代ID查找方法

## URL表重新生成

如果您需要重新生成URL跟踪表:

1. 备份当前数据库:
   ```bash
   cp data/local_database.db data/local_database.backup.db
   ```

2. 运行重新生成脚本:
   ```bash
   python scripts/database/regenerate_url_table.py
   ```

3. 验证重新生成:
   ```bash
   python scripts/tests/test_url_table.py
   ```

## 服务器IP配置

如果您遇到服务器IP绑定问题:

1. 检查当前服务器IP:
   ```bash
   ./check_server_ip.sh
   ```

2. 使用正确的IP地址更新systemd服务文件
3. 重启服务:
   ```bash
   sudo systemctl restart nitterlocal-backend
   ```

## 测试

项目在`scripts/tests`目录中包含各种测试脚本:

```bash
# 运行所有测试
python -m unittest discover scripts/tests

# 运行特定测试
python scripts/tests/test_database.py
```

## 简化工作流程

对于简化的工作流程:

1. 用户通过Web界面上传Excel文件
2. 系统处理文件并更新本地SQLite数据库
3. Crontab作业每15分钟将数据同步到MySQL
4. 用户可以根据需要手动触发同步

这种方法提供了更快的响应时间，并减少了同步失败的可能性。
