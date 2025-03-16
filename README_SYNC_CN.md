# 数据同步流程说明

本文档详细说明了从Excel文件到SQLite数据库再到MySQL数据库的数据同步流程。

## 数据库结构

### SQLite数据库

SQLite数据库包含两个主要表：

1. **url_tracking表**：
   - `id`: 主键，自增整数
   - `url`: Twitter URL，唯一
   - `user_id`: Twitter用户ID
   - `screen_name`: Twitter用户名
   - `type`: 类型（如'kol'）
   - `subtype`: 子类型（如'crypto'）
   - 其他字段：description, status, last_checked, error_count, tweet_count, added_at, last_scraped, last_error

2. **kol_character表**：
   - `id`: 主键，自增整数
   - `kol_id`: KOL ID，对应url_tracking表的user_id
   - `kol_screen_name`: KOL用户名，不能为空
   - `bio`: 简介
   - `lore`: 背景故事
   - `knowledge`: 知识领域
   - `postExamples`: 发帖示例
   - `topics`: 话题
   - `style_all`: 整体风格
   - `style_chat`: 聊天风格
   - `style_post`: 发帖风格
   - `adjectives`: 形容词
   - `url_tracking_id`: 外键，关联url_tracking表的id

### MySQL数据库

MySQL数据库中的kol_character表结构与SQLite中的类似，但有一个重要区别：`kol_screen_name`字段在MySQL中不能为空，必须有值。

## 数据流程

1. **Excel导入到SQLite**：
   - 使用`scripts/database/process_excel.py`脚本处理Excel文件
   - 创建url_tracking和kol_character表
   - 建立两个表之间的关系

2. **SQLite同步到MySQL**：
   - 使用`scripts/sync/sync_kol_character_only.py`脚本同步数据
   - 处理kol_screen_name字段，确保其在MySQL中有值
   - 建立两个数据库之间的映射关系

## 同步脚本说明

### sync_kol_character_only.py

此脚本将SQLite中的kol_character数据同步到MySQL数据库。主要功能：

1. **获取kol_screen_name**：
   - 使用层级方法获取kol_screen_name值
   - 首先尝试使用kol_character表中的kol_screen_name
   - 如果为空，尝试从URL中提取Twitter用户名
   - 如果仍为空，尝试使用url_tracking表中的screen_name
   - 如果都没有，使用默认值"unknown_user_{kol_id}"

2. **同步逻辑**：
   - 检查记录是否已存在于MySQL中
   - 如果存在，更新记录
   - 如果不存在，插入新记录
   - 处理可能的错误情况

## 数据库迁移

### migrate_database.py

此脚本用于更新数据库结构，主要功能：

1. **添加url_tracking_id列**：
   - 在kol_character表中添加url_tracking_id列
   - 创建相应的索引

2. **建立关系**：
   - 根据kol_id和user_id建立关系
   - 如果无法通过kol_id匹配，尝试通过screen_name匹配
   - 更新kol_character记录的url_tracking_id

3. **创建视图**：
   - 创建kol_character_with_url视图，连接两个表

## 使用说明

### 重置数据库

```bash
# 备份当前数据库（可选）
cp /home/ubuntu/nitterlocal/data/local_database.db /home/ubuntu/nitterlocal/data/local_database.db.bak

# 重置数据库结构
sqlite3 /home/ubuntu/nitterlocal/data/local_database.db < /home/ubuntu/nitterlocal/reset_database.sql

# 添加示例数据（可选）
sqlite3 /home/ubuntu/nitterlocal/data/local_database.db < /home/ubuntu/nitterlocal/create_sample_data.sql
```

### 验证数据库结构

```bash
python3 /home/ubuntu/nitterlocal/test_database_structure.py
```

### 同步数据

```bash
# 测试模式（不实际修改MySQL数据库）
python3 /home/ubuntu/nitterlocal/scripts/sync/sync_kol_character_only.py --test --verbose

# 实际同步数据
python3 /home/ubuntu/nitterlocal/scripts/sync/sync_kol_character_only.py --verbose
```

## 故障排除

1. **kol_screen_name错误**：
   - 确保kol_character表中的kol_screen_name字段有值
   - 或者确保url_tracking表中的screen_name字段有值
   - 或者确保URL可以提取出有效的Twitter用户名

2. **关系建立失败**：
   - 检查kol_id和user_id是否匹配
   - 检查kol_screen_name和screen_name是否匹配
   - 手动更新url_tracking_id字段

3. **同步错误**：
   - 检查MySQL连接信息
   - 检查MySQL表结构
   - 查看日志文件了解详细错误信息
