# Twitter 数据分析功能使用指南

本文档详细介绍了 nitterlocal 仓库中的数据分析功能，包括如何使用各种脚本进行推文分析、处理和导出。

## 目录

1. [项目结构](#项目结构)
2. [统一命令行接口](#统一命令行接口)
3. [删除重复推文](#删除重复推文)
4. [统计每个URL的推文数量](#统计每个URL的推文数量)
5. [高级推文分析](#高级推文分析)
6. [推文导出功能](#推文导出功能)
7. [配置文件说明](#配置文件说明)
8. [常见问题解答](#常见问题解答)

## 项目结构

数据分析功能的代码组织结构如下：

```
nitterlocal/
├── config/
│   └── database_config.json      # 数据库和分析配置文件
├── scripts/
│   ├── data_analysis.py          # 统一命令行接口
│   ├── data_analysis/
│   │   ├── remove_duplicate_tweets.py  # 删除重复推文
│   │   ├── count_tweets_per_url.py     # 统计每个URL的推文数量
│   │   ├── analyze_tweets.py           # 高级推文分析
│   │   └── export_tweets.py            # 推文导出功能
│   └── utils/
│       ├── add_urls.py           # 添加URL到数据库
│       ├── view_tweets.py        # 查看推文
│       └── view_urls.py          # 查看URL列表
└── data/
    ├── local_database.db         # SQLite数据库文件
    └── exports/                  # 导出文件存放目录
```

## 统一命令行接口

所有数据分析功能都可以通过统一的命令行接口 `scripts/data_analysis.py` 访问。

### 基本用法

```bash
python scripts/data_analysis.py <命令> [选项]
```

### 可用命令

- `remove-duplicates`: 删除重复推文
- `count-tweets`: 统计每个URL的推文数量
- `analyze`: 高级推文分析
- `export`: 推文导出功能

### 通用选项

- `--db-path`: 指定数据库路径，默认为 `data/local_database.db`
- `--help`: 显示帮助信息

## 删除重复推文

此功能用于识别并删除内容相同的重复推文，同时保留互动量（点赞、转发、回复）最高的版本。

### 用法

```bash
python scripts/data_analysis.py remove-duplicates [选项]
```

### 选项

- `--dry-run`: 干运行模式，只显示将要删除的推文，不实际删除
- `--db-path`: 指定数据库路径

### 示例

```bash
# 干运行模式，显示重复推文但不删除
python scripts/data_analysis.py remove-duplicates --dry-run

# 实际删除重复推文
python scripts/data_analysis.py remove-duplicates
```

### 输出示例

```
2025-03-02 12:44:42,318 - INFO - Removing duplicate tweets from database at data/local_database.db
2025-03-02 12:44:42,321 - INFO - Found 4 groups of duplicate tweets
2025-03-02 12:44:42,321 - INFO - Content: 'Bittensor $TAO is going to eat the AI world...' appears 3 times
2025-03-02 12:44:42,321 - INFO - Content: '#EndSARS...' appears 3 times
2025-03-02 12:44:42,321 - INFO - Content: '🔥🔥🔥...' appears 2 times
2025-03-02 12:44:42,321 - INFO - Content: 'I grew up in ATHens...' appears 2 times
2025-03-02 12:44:42,321 - INFO - Dry run completed. No changes made to the database.
```

## 统计每个URL的推文数量

此功能用于统计数据库中每个URL的推文数量，并生成详细报告。

### 用法

```bash
python scripts/data_analysis.py count-tweets [选项]
```

### 选项

- `--format`: 输出格式，可选 `text` 或 `json`，默认为 `text`
- `--output`: 输出文件路径，如不指定则输出到控制台
- `--limit`: 限制显示的URL数量
- `--db-path`: 指定数据库路径

### 示例

```bash
# 显示所有URL的推文数量
python scripts/data_analysis.py count-tweets

# 显示前10个URL的推文数量
python scripts/data_analysis.py count-tweets --limit 10

# 导出为JSON格式
python scripts/data_analysis.py count-tweets --format json --output stats.json
```

### 输出示例

```
Tweet Count Statistics:
Total URLs: 287
Total Tweets: 2450
Generated at: 2025-03-02T12:44:42.469531

Tweet Counts per URL:
1. https://twitter.com/100trillionUSD
   Description: Plan B - 比特币分析师，Stock-to-Flow模型创建者
   Type: kol
   Tweet Count: 50

2. https://twitter.com/APompliano
   Description: Anthony Pompliano - 加密货币投资者和播客主持人
   Type: kol
   Tweet Count: 50

...
```

## 高级推文分析

此功能提供多种分析模式，包括最近推文、热门推文和关键词搜索。

### 用法

```bash
python scripts/data_analysis.py analyze [选项]
```

### 选项

- `--type`: 分析类型，可选 `recent`（最近）、`popular`（热门）或 `search`（搜索），默认为 `recent`
- `--days`: 最近天数，用于 `recent` 类型，默认为 7
- `--min-likes`: 最小点赞数，用于 `popular` 类型，默认为 0
- `--min-retweets`: 最小转发数，用于 `popular` 类型，默认为 0
- `--author`: 按作者筛选
- `--keyword`: 搜索关键词，用于 `search` 类型
- `--format`: 输出格式，可选 `text` 或 `json`，默认为 `text`
- `--output`: 输出文件路径，如不指定则输出到控制台
- `--limit`: 限制显示的推文数量，默认为 50
- `--db-path`: 指定数据库路径

### 示例

```bash
# 分析最近7天的推文
python scripts/data_analysis.py analyze --type recent --days 7

# 分析热门推文（至少100个点赞）
python scripts/data_analysis.py analyze --type popular --min-likes 100

# 搜索包含"crypto"关键词的推文
python scripts/data_analysis.py analyze --type search --keyword "crypto"

# 分析特定作者的推文
python scripts/data_analysis.py analyze --author "elonmusk"

# 导出为JSON格式
python scripts/data_analysis.py analyze --type popular --format json --output popular_tweets.json
```

### 输出示例

```
Tweet Analysis Results:
Analysis Type: recent
Total Tweets: 2450
Filtered Tweets: 3
Generated at: 2025-03-02T12:44:42.616794

Tweets:
1. Tweet ID: 1894019006161473996
   Author: tim_cook
   Created at: 2025-02-24T13:38:14.000Z
   Content: As a proud American company, we're thrilled to continue to make significant investments in the US. T...
   Likes: 73288, Retweets: 9091, Replies: 5235
   Source URL: https://twitter.com/tim_cook

...
```

## 推文导出功能

此功能用于将推文导出为CSV或JSON格式，便于外部分析。

### 用法

```bash
python scripts/data_analysis.py export [选项]
```

### 选项

- `--format`: 输出格式，可选 `csv` 或 `json`，默认为 `csv`
- `--output`: 输出文件路径，如不指定则自动生成
- `--source-url`: 按来源URL筛选推文
- `--limit`: 限制导出的推文数量
- `--db-path`: 指定数据库路径

### 示例

```bash
# 导出所有推文为CSV格式
python scripts/data_analysis.py export --format csv --output tweets.csv

# 导出特定URL的推文为JSON格式
python scripts/data_analysis.py export --format json --source-url "https://twitter.com/elonmusk" --output elonmusk_tweets.json

# 限制导出数量
python scripts/data_analysis.py export --limit 100
```

### 输出示例

导出的CSV文件包含以下字段：
- tweet_id
- author
- content
- created_at
- likes
- retweets
- replies
- source_url

## 配置文件说明

配置文件位于 `config/database_config.json`，包含以下设置：

```json
{
  "database": {
    "path": "data/local_database.db",
    "backup_path": "data/backups/",
    "backup_frequency": "daily"
  },
  "twitter_client": {
    "max_tweets_per_url": 50,
    "batch_size": 10,
    "sleep_between_urls": 2
  },
  "logging": {
    "level": "INFO",
    "file": "data/logs/database.log",
    "format": "%(asctime)s - %(levelname)s - %(message)s"
  }
}
```

### 配置项说明

- `database`: 数据库相关配置
  - `path`: 数据库文件路径
  - `backup_path`: 备份文件存放目录
  - `backup_frequency`: 备份频率
- `twitter_client`: Twitter客户端配置
  - `max_tweets_per_url`: 每个URL最多获取的推文数量
  - `batch_size`: 批处理大小
  - `sleep_between_urls`: URL之间的休眠时间（秒）
- `logging`: 日志配置
  - `level`: 日志级别
  - `file`: 日志文件路径
  - `format`: 日志格式

## 常见问题解答

### 如何查看数据库中的推文数量？

```bash
python scripts/data_analysis.py count-tweets
```

### 如何查找最受欢迎的推文？

```bash
python scripts/data_analysis.py analyze --type popular --min-likes 100
```

### 如何删除重复推文？

```bash
# 先进行干运行，查看将要删除的推文
python scripts/data_analysis.py remove-duplicates --dry-run

# 确认无误后，实际删除重复推文
python scripts/data_analysis.py remove-duplicates
```

### 如何导出特定作者的推文？

首先使用分析功能找到作者的推文：

```bash
python scripts/data_analysis.py analyze --author "elonmusk"
```

然后导出该作者的推文：

```bash
python scripts/data_analysis.py export --format json --source-url "https://twitter.com/elonmusk" --output elonmusk_tweets.json
```

### 如何修改每个URL获取的最大推文数量？

编辑 `config/database_config.json` 文件，修改 `twitter_client.max_tweets_per_url` 值。

### 如何备份数据库？

数据库备份功能已集成在系统中，根据 `database_config.json` 中的 `backup_frequency` 设置自动执行。您也可以手动复制数据库文件进行备份：

```bash
cp data/local_database.db data/backups/local_database_$(date +%Y%m%d).db
```
