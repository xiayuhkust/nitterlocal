# 简化的后端工作流程

## 概述
为了简化后端工作流程，我们对系统进行了以下更改：

1. 用户上传Excel文件后，只更新本地SQLite数据库
2. MySQL同步通过crontab定期执行，而不是在用户上传后立即执行
3. 使用统一的同步脚本`sync_to_mysql_combined.py`处理所有表格的同步

## 优势
- 用户上传Excel文件后响应更快
- 减少同步失败的可能性
- 简化了代码和维护工作
- 统一的同步脚本处理所有表格

## 定时任务
系统现在使用以下crontab配置：

```
# 每6小时分析账号活跃度
0 */6 * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/analyze_activity.py --days 7 >> data/activity_analysis.log 2>&1

# 每15分钟运行动态更新
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance >> data/dynamic_update.log 2>&1

# 每15分钟同步到MySQL（使用综合同步脚本）
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_combined.py --since-days 1 >> data/sync_cron.log 2>&1
```

## 使用方法
1. 用户上传Excel文件后，系统会立即处理并更新本地SQLite数据库
2. 系统会告知用户数据已成功处理，并将在下一次定时同步（最多15分钟后）同步到MySQL
3. 用户也可以点击"同步到MySQL"按钮手动触发同步

## 更新crontab
使用以下命令更新crontab配置：

```bash
# 运行更新脚本
bash update_crontab_simplified.sh

# 按照脚本提示的命令更新crontab
```

## 故障排除
如果遇到同步问题，请检查：
1. 本地数据库是否正确更新
2. crontab是否正确配置
3. 日志文件中是否有错误信息
