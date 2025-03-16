# 数据库清理脚本

此目录包含用于清理数据库的脚本，根据Excel文件中的Twitter URL列表筛选数据。

## 主要脚本

### data_cleaning.py

此脚本执行以下操作：

1. 读取Excel文件中的Twitter URL列表
2. 更新url_tracking表中的screen_name字段
3. 删除url_tracking表中URL不在Excel文件中的记录
4. 删除tweets表中author字段不在url_tracking的screen_name字段中的记录
5. 删除kol_character表中kol_screen_name字段不在url_tracking的screen_name字段中的记录

## 使用方法

```bash
# 默认使用以下路径
# Excel文件: /home/ubuntu/attachments/5d1276b2-78dc-49dc-b222-b11d9f4d9039/kol+characte_.xlsx
# 数据库: /home/ubuntu/repos/nitterlocal/data/local_database.db
python data_cleaning.py

# 或者指定路径
python data_cleaning.py --excel /path/to/excel/file.xlsx --db-path /path/to/database.db
```

## 注意事项

- 脚本会自动处理Twitter URL格式差异（twitter.com和x.com）
- 脚本执行前建议备份数据库
- 脚本会输出详细的日志信息，包括删除的记录数量
