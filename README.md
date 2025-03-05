# Twitter Client Daily Update

This project provides a daily update process that uses the agent-twitter-client library to extract tweets from Twitter URLs stored in a local database.

## 功能特点

- 使用 agent-twitter-client 从 Twitter URL 中提取推文
- 将推文存储在本地 SQLite 数据库中
- 批量处理 URL 以避免速率限制
- 支持从每个 URL 提取最多 50 条推文
- 命令行界面用于自定义更新过程
- 支持通过 user_id 字段关联推文和用户

## 安装

1. 克隆仓库：
   ```
   git clone https://github.com/xiayuhkust/nitterlocal.git
   cd nitterlocal
   ```

2. 安装 Node.js 依赖：
   ```
   cd src/twitter_client
   npm install
   ```

3. 在 `src/twitter_client` 目录中创建一个包含 Twitter 凭据的 `.env` 文件：
   ```
   TWITTER_USERNAME=your_username
   TWITTER_PASSWORD=your_password
   TWITTER_EMAIL=your_email
   ```

## 使用方法

运行每日更新流程：
```
python main.py
```

自定义更新流程：
```
python main.py --batch-size 5 --sleep 3 --max-tweets 30 --limit 20
```

### 命令行参数

- `--batch-size`: 每批处理的 URL 数量（默认：10）
- `--sleep`: URL 之间的睡眠时间（秒）（默认：2）
- `--max-tweets`: 每个 URL 提取的最大推文数（默认：50）
- `--limit`: 限制要处理的 URL 数量（可选）
- `--db-path`: 本地数据库的路径（默认：data/local_database.db）

## 项目结构

- `src/database`: 用于存储推文和管理 URL 的数据库模块
- `src/twitter_client`: 用于提取推文的 Twitter 客户端模块
- `src/daily_update`: 用于批量处理 URL 的每日更新模块
- `scripts/data_analysis`: 用于分析推文数据的脚本
- `data`: 用于存储 SQLite 数据库和其他数据文件的目录
- `config`: 应用程序的配置文件

## 数据分析功能

本项目提供了多种数据分析功能，可以通过命令行工具 `scripts/data_analysis.py` 访问。所有分析功能现在都支持 `user_id` 字段，可以帮助您跟踪和分析特定 Twitter 用户的推文。

### 热门推文分析

分析热门推文并按点赞和转发数排序：

```bash
python scripts/data_analysis.py analyze --type popular --format json --output popular_tweets.json
```

输出示例（JSON 格式）：
```json
{
  "analysis_type": "popular",
  "total_tweets": 13259,
  "filtered_tweets": 50,
  "tweets": [
    {
      "tweet_id": "1837722651940274315",
      "source_url": "https://nitter.net/MattWallace888",
      "content": "示例推文内容",
      "created_at": "2024-09-22T05:16:38.000Z",
      "author": "MattWallace888",
      "user_id": "12345678",
      "likes": 406074,
      "retweets": 31971,
      "replies": 5726,
      "views": 48154770,
      "stored_at": "2025-03-02 11:02:59"
    }
  ]
}
```

### 推文统计分析

统计每个 URL 的推文数量：

```bash
python scripts/data_analysis.py count-tweets --format json --output stats.json
```

输出示例（JSON 格式）：
```json
{
  "total_tweets": 13259,
  "total_urls": 285,
  "url_tweet_counts": [
    {
      "url": "https://nitter.net/0xPolygon",
      "description": "加密货币机构 0xPolygon",
      "type": "institution",
      "user_id": "87654321",
      "tweet_count": 50
    }
  ]
}
```

## 数据库结构

本地数据库使用 SQLite，包含以下表：

### url_tracking

存储 URL 元数据：
- `user_id`: Twitter 账号的唯一用户 ID（主键）
- `url`: 要跟踪的 URL（唯一，非空）
- `description`: URL 的描述
- `status`: URL 的状态（active, error 等）
- `last_checked`: 最后检查的时间戳
- `error_count`: 遇到的错误次数
- `tweet_count`: 提取的推文数量
- `type`: URL 类型（kol, media 等）
- `added_at`: URL 添加时的时间戳
- `last_scraped`: 最后抓取的时间戳
- `last_error`: 最后的错误消息

### tweets

存储单个推文信息：
- `tweet_id`: 推文 ID（主键）
- `source_url`: 推文的来源 URL
- `content`: 推文内容
- `created_at`: 推文创建时的时间戳
- `author`: 推文作者
- `likes`: 点赞数
- `retweets`: 转发数
- `replies`: 回复数
- `views`: 浏览数
- `stored_at`: 推文存储时的时间戳
- `user_id`: Twitter 账号的唯一用户 ID
- `is_reply`: 布尔值，表示推文是否为回复
- `in_reply_to_status_id`: 被回复推文的 ID
- `conversation_id`: 对话线程的 ID

### hashtags

存储推文中的话题标签：
- `id`: 话题标签条目 ID（主键）
- `tweet_id`: 引用 tweets 表的外键
- `hashtag`: 话题标签文本（不包含 # 符号）
- `stored_at`: 话题标签存储时的时间戳

该表与 tweets 表有多对一的关系，允许每条推文有多个话题标签。`tweet_id` 列有一个带 CASCADE 删除的外键约束，确保当推文被删除时，其关联的话题标签也被删除。`hashtag` 列已建立索引以加快查询速度。

### backup_log

记录备份操作：
- `id`: 日志 ID（主键）
- `timestamp`: 操作的时间戳
- `operation`: 执行的操作
- `details`: 操作的详细信息
- `success`: 成功状态（1 表示成功，0 表示失败）

## Twitter 客户端

Twitter 客户端使用 agent-twitter-client 库从 Twitter URL 中提取推文。它需要 Twitter 凭据来进行身份验证。

### Twitter 抓取器

Twitter 抓取器提供以下功能：
- 从 URL 中提取用户名
- 从 URL 中抓取推文
- 批量处理推文
- 处理速率限制和错误

## 每日更新流程

每日更新流程执行以下步骤：
1. 从数据库获取活跃的 URL
2. 批量处理 URL
3. 从每个 URL 提取推文
4. 将推文存储到数据库
5. 更新 URL 元数据
6. 生成统计数据

## 其他数据分析功能

除了上述功能外，该项目还提供以下数据分析功能：

### 删除重复推文

```bash
python scripts/data_analysis.py remove-duplicates
```

### 分析话题标签

```bash
python scripts/data_analysis.py analyze-hashtags --limit 20 --output hashtags.json
```

### 导出推文

```bash
python scripts/data_analysis.py export --format csv --output tweets.csv
```

### 分析回复

分析推文回复，支持多种分析类型：

```bash
# 分析用户发出的回复
python scripts/data_analysis/analyze_replies.py --type user-replies --author username

# 分析对用户推文的回复
python scripts/data_analysis/analyze_replies.py --type replies-to-user --author username

# 分析特定对话线程中的所有回复
python scripts/data_analysis/analyze_replies.py --type conversation --conversation conversation_id
```

回复分析支持以下参数：
- `--type`: 分析类型（user-replies, replies-to-user, conversation）
- `--days`: 最近几天的回复（默认：7）
- `--min-likes`: 最小点赞数
- `--author`: 按作者筛选
- `--keyword`: 按关键词搜索
- `--conversation`: 按对话 ID 筛选
- `--format`: 输出格式（text, json）
- `--output`: 输出文件路径
- `--limit`: 限制回复数量

## 用户 ID 字段说明

`user_id` 字段是 Twitter 账号的唯一标识符，在本项目中有以下用途：

1. 在 `url_tracking` 表中作为主键，用于唯一标识每个跟踪的 URL
2. 在 `tweets` 表中作为外键，用于关联推文与其作者的 Twitter 账号
3. 在数据分析功能中，可以通过 `user_id` 字段筛选特定用户的推文
4. 在统计分析中，可以查看每个 `user_id` 对应的推文数量

通过 `user_id` 字段，您可以更精确地跟踪和分析特定 Twitter 用户的活动，而不仅仅依赖于用户名（可能会更改）。

## 许可证

本项目采用 MIT 许可证。
