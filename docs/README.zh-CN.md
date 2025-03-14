# Twitter数据抓取与分析系统

这个项目提供了一个完整的Twitter数据抓取和分析系统，可以从Twitter账号获取推文并进行存储和分析。

## 功能特点

- 从Twitter账号URL列表中抓取推文
- 本地数据库存储推文和URL信息
- 支持批量处理和定时更新
- 提供数据分析工具和统计功能
- 支持多种抓取方法（Nitter和Twitter客户端）
- 支持抓取普通推文和回复推文

## 数据库结构

### URL跟踪表 (url_tracking)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| url | TEXT | URL地址（主键） |
| user_id | TEXT | 用户ID |
| description | TEXT | 描述信息 |
| status | TEXT | 状态（active/inactive） |
| last_checked | TEXT | 最后检查时间 |
| error_count | INTEGER | 错误计数 |
| tweet_count | INTEGER | 推文计数 |
| type | TEXT | 类型（kol/institution） |
| added_at | TEXT | 添加时间 |
| last_scraped | TEXT | 最后抓取时间 |
| last_error | TEXT | 最后错误信息 |
| subtype | TEXT | 子类型（exchange/meme/null） |

### 推文表 (tweets)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | TEXT | 推文ID（主键） |
| user_id | TEXT | 用户ID |
| url | TEXT | 来源URL |
| content | TEXT | 推文内容 |
| timestamp | TEXT | 发布时间戳 |
| likes | INTEGER | 点赞数 |
| retweets | INTEGER | 转发数 |
| replies | INTEGER | 回复数 |
| is_reply | INTEGER | 是否为回复（0/1） |
| reply_to | TEXT | 回复的推文ID |
| conversation_id | TEXT | 对话ID |

## 安装与配置

1. 克隆仓库：
   ```bash
   git clone https://github.com/xiayuhkust/nitterlocal.git
   cd nitterlocal
   ```

2. 创建数据目录：
   ```bash
   mkdir -p data
   ```

3. 配置Twitter客户端（可选）：
   ```bash
   cp src/twitter_client/.env.example src/twitter_client/.env
   # 编辑.env文件，添加Twitter账号凭据
   ```

## 使用方法

### 添加URL

```bash
python scripts/utils/add_urls.py --file data/sample_urls.json
```

### 查看URL列表

```bash
python scripts/utils/view_urls.py
```

### 运行每日更新

```bash
python src/daily_update/daily_update.py
```

### 查看推文

```bash
python scripts/utils/view_tweets.py
```

### 数据分析

```bash
# 统计每个URL的推文数量
python scripts/data_analysis.py count-tweets

# 分析热门推文
python scripts/data_analysis.py analyze --type popular

# 分析标签使用情况
python scripts/data_analysis.py analyze --type hashtags
```

## 数据库迁移

如果需要更新数据库结构，可以使用以下迁移脚本：

```bash
# 添加user_id和subtype字段
python scripts/migrations/add_user_id_and_subtype.py

# 更新URL的user_id值
python scripts/migrations/update_url_user_ids.py
```

## 从CoinMarketCap获取数据

可以使用以下脚本从CoinMarketCap获取交易所和meme代币的Twitter账号：

```bash
python scripts/utils/fetch_coinmarketcap_data.py --exchanges 50 --meme-tokens 50
```

## 开发指南

### 项目结构

```
nitterlocal/
├── data/                  # 数据文件和数据库
├── src/                   # 源代码
│   ├── database/          # 数据库模块
│   ├── twitter_client/    # Twitter客户端模块
│   └── daily_update/      # 每日更新模块
├── scripts/               # 实用脚本
│   ├── utils/             # 工具脚本
│   ├── migrations/        # 数据库迁移脚本
│   └── data_analysis/     # 数据分析脚本
└── tests/                 # 测试文件
```

### 添加新功能

1. 在适当的模块中添加功能
2. 编写测试确保功能正常工作
3. 更新文档说明新功能的使用方法

## 贡献指南

欢迎提交问题报告和功能请求。如果您想贡献代码，请遵循以下步骤：

1. Fork仓库
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。详情请参阅LICENSE文件。
