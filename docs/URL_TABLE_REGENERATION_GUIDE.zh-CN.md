# URL表重新生成指南

本指南将帮助您重新生成URL表，包括添加新的user_id和subtype字段，以及从CoinMarketCap获取交易所和meme代币数据。

## 1. 准备工作

确保您已经克隆了最新的代码库：

```bash
git clone https://github.com/xiayuhkust/nitterlocal.git
cd nitterlocal
```

## 2. 添加新字段到数据库

运行数据库迁移脚本，为url_tracking表添加user_id和subtype字段：

```bash
python scripts/migrations/add_user_id_and_subtype.py
```

这将为url_tracking表添加以下字段：
- user_id：用户ID，从URL中提取
- subtype：子类型，用于区分不同类型的机构（exchange/meme）

## 3. 添加CoinMarketCap数据到sample_urls.json

您可以使用以下脚本从CoinMarketCap获取前50名交易所和meme代币，并将它们添加到sample_urls.json：

```bash
python scripts/utils/add_coinmarketcap_to_sample.py --exchanges 10 --meme-tokens 10
```

参数说明：
- --exchanges：要获取的交易所数量（默认为10）
- --meme-tokens：要获取的meme代币数量（默认为10）
- --sample-file：sample_urls.json的路径（默认为data/sample_urls.json）
- --output-file：输出文件路径（默认与sample-file相同）

## 4. 清空并重新添加URL

使用以下命令清空URL表并重新添加所有URL：

```bash
python scripts/utils/add_urls.py --file data/sample_urls.json --clear
```

这将：
1. 清空url_tracking表中的所有数据
2. 从sample_urls.json读取URL列表
3. 为每个URL提取user_id
4. 根据URL类型和CoinMarketCap数据确定subtype
5. 将URL添加到数据库中

## 5. 验证结果

您可以使用以下命令验证URL表是否正确生成：

```bash
# 查看所有URL
python scripts/utils/view_urls.py

# 查看特定类型的URL
python scripts/utils/view_urls.py --type institution --subtype exchange
python scripts/utils/view_urls.py --type institution --subtype meme
python scripts/utils/view_urls.py --type kol
```

## 6. 更新现有URL的user_id

如果您想为现有URL更新user_id，可以使用以下命令：

```bash
python scripts/migrations/update_url_user_ids.py
```

## 7. 常见问题

### 7.1 如何只添加特定类型的URL？

您可以创建一个只包含特定类型URL的JSON文件，然后使用add_urls.py脚本添加：

```bash
python scripts/utils/add_urls.py --file your_custom_file.json
```

### 7.2 如何修改现有URL的类型或子类型？

您可以直接编辑sample_urls.json文件，然后重新运行add_urls.py脚本：

```bash
python scripts/utils/add_urls.py --file data/sample_urls.json
```

这将更新现有URL的类型和子类型。

### 7.3 如何查看数据库中的URL统计信息？

```bash
sqlite3 data/local_database.db "SELECT type, subtype, COUNT(*) FROM url_tracking GROUP BY type, subtype;"
```

## 8. 完整流程示例

以下是完整的URL表重新生成流程：

```bash
# 1. 添加新字段到数据库
python scripts/migrations/add_user_id_and_subtype.py

# 2. 添加CoinMarketCap数据到sample_urls.json
python scripts/utils/add_coinmarketcap_to_sample.py --exchanges 20 --meme-tokens 20

# 3. 清空并重新添加URL
python scripts/utils/add_urls.py --file data/sample_urls.json --clear

# 4. 验证结果
python scripts/utils/view_urls.py
```

这将创建一个包含user_id和subtype字段的完整URL表，并添加来自CoinMarketCap的交易所和meme代币数据。
