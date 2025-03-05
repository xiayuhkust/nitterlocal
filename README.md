# Twitter Client Daily Update

This project provides a daily update process that uses the agent-twitter-client library to extract tweets from Twitter URLs stored in a local database.

## Features

- Extract tweets from Twitter URLs using agent-twitter-client
- Store tweets in a local SQLite database
- Process URLs in batches to avoid rate limits
- Support for extracting up to 50 tweets per URL
- Command-line interface for customizing the update process

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/xiayuhkust/nitterlocal.git
   cd nitterlocal
   ```

2. Install Node.js dependencies:
   ```
   cd src/twitter_client
   npm install
   ```

3. Create a `.env` file in the `src/twitter_client` directory with your Twitter credentials:
   ```
   TWITTER_USERNAME=your_username
   TWITTER_PASSWORD=your_password
   TWITTER_EMAIL=your_email
   ```

## Usage

Run the daily update process:
```
python main.py
```

Customize the update process:
```
python main.py --batch-size 5 --sleep 3 --max-tweets 30 --limit 20
```

### Command-line Arguments

- `--batch-size`: Number of URLs to process in each batch (default: 10)
- `--sleep`: Sleep time between URLs in seconds (default: 2)
- `--max-tweets`: Maximum number of tweets to extract per URL (default: 50)
- `--limit`: Limit the number of URLs to process (optional)
- `--db-path`: Path to the local database (default: data/local_database.db)

## Project Structure

- `src/database`: Database module for storing tweets and managing URLs
- `src/twitter_client`: Twitter client module for extracting tweets
- `src/daily_update`: Daily update module for processing URLs in batches
- `data`: Directory for storing the SQLite database and other data files
- `config`: Configuration files for the application

## 数据分析功能

本项目提供了多种数据分析功能，可以通过命令行工具 `scripts/data_analysis.py` 访问。所有分析功能现在都支持 `user_id` 字段，可以帮助您跟踪和分析特定 Twitter 用户的推文。

### 热门推文分析

分析热门推文并按点赞和转发数排序：

```bash
python scripts/data_analysis.py analyze --type popular --format json --output popular_tweets.json
```

### 推文统计分析

统计每个 URL 的推文数量：

```bash
python scripts/data_analysis.py count-tweets --format json --output stats.json
```

### 列出 URL

列出数据库中的所有 URL，包括 user_id 信息：

```bash
python scripts/data_analysis.py list-urls --format json --output urls.json
```

可用选项：
- `--format`：输出格式，可选 text 或 json，默认为 text
- `--output`：输出文件路径
- `--limit`：限制显示的 URL 数量
- `--type`：按类型筛选 URL

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

## 数据库结构

本地数据库使用 SQLite，包含以下表：

### url_tracking

存储 URL 元数据：
- `url`: 要跟踪的 URL（主键）
- `user_id`: Twitter 账号的唯一用户 ID
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

Stores individual tweet information:
- `tweet_id`: Tweet ID (primary key)
- `source_url`: Source URL of the tweet
- `content`: Content of the tweet
- `created_at`: Timestamp when the tweet was created
- `author`: Author of the tweet
- `likes`: Number of likes
- `retweets`: Number of retweets
- `replies`: Number of replies
- `views`: Number of views
- `stored_at`: Timestamp when the tweet was stored
- `user_id`: Twitter's unique user ID for the account

### hashtags

Stores hashtags from tweets:
- `id`: Hashtag entry ID (primary key)
- `tweet_id`: Foreign key referencing the tweets table
- `hashtag`: The hashtag text (without the # symbol)
- `stored_at`: Timestamp when the hashtag was stored

This table has a many-to-one relationship with the tweets table, allowing multiple hashtags per tweet. The `tweet_id` column has a foreign key constraint with CASCADE delete, ensuring that when a tweet is deleted, its associated hashtags are also removed. The `hashtag` column is indexed for faster queries.

### backup_log

Logs backup operations:
- `id`: Log ID (primary key)
- `timestamp`: Timestamp of the operation
- `operation`: Operation performed
- `details`: Details of the operation
- `success`: Success status (1 for success, 0 for failure)

## Twitter Client

The Twitter client uses the agent-twitter-client library to extract tweets from Twitter URLs. It requires Twitter credentials to authenticate with Twitter.

### Twitter Scraper

The Twitter scraper provides the following functionality:
- Extract usernames from URLs
- Scrape tweets from URLs
- Process tweets in batches
- Handle rate limits and errors

## Daily Update Process

The daily update process performs the following steps:
1. Get active URLs from the database
2. Process URLs in batches
3. Extract tweets from each URL
4. Store tweets in the database
5. Update URL metadata
6. Generate statistics

## License

This project is licensed under the MIT License.
