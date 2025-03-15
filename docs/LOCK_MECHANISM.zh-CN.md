# 同步锁机制详细说明

## 概述

随着数据量的增长，MySQL同步过程可能需要超过15分钟才能完成。这会导致一个问题：如果一个同步任务仍在运行，而下一个计划任务启动，两个进程会同时尝试修改数据库，可能导致数据不一致或错误。

为了解决这个问题，我们实现了一个基于文件的锁机制，确保同一时间只有一个同步进程在运行。

## 锁机制的工作原理

锁机制使用文件锁（`fcntl`）来实现进程间的互斥。当一个同步进程启动时，它会尝试获取锁文件的独占访问权。如果另一个进程已经持有锁，新进程会等待一段时间（可配置的超时时间），然后如果仍然无法获取锁，就会退出。

### 主要特点

1. **文件锁定**：使用`fcntl`系统调用实现可靠的进程间锁定
2. **超时功能**：防止进程无限等待，可配置超时时间
3. **进程ID存储**：在锁文件中存储当前持有锁的进程ID，便于调试
4. **优雅的失败处理**：如果无法获取锁，进程会优雅地退出而不是强制执行

## 实现细节

锁机制的核心实现在`scripts/sync/sync_lock.py`文件中：

```python
class SyncLock:
    """同步脚本的锁机制，防止重叠执行"""
    
    def __init__(self, lock_file=None, timeout=None):
        """初始化锁
        
        参数:
            lock_file: 锁文件路径
            timeout: 等待锁的最大时间（秒）
        """
        self.lock_file = lock_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data/sync_lock.pid'
        )
        self.timeout = timeout
        self.lock_fd = None
        self.locked = False
    
    def acquire(self):
        """获取锁
        
        返回:
            bool: 如果成功获取锁则为True，否则为False
        """
        try:
            # 如果目录不存在则创建
            lock_dir = os.path.dirname(self.lock_file)
            os.makedirs(lock_dir, exist_ok=True)
            
            # 打开锁文件
            self.lock_fd = open(self.lock_file, 'w')
            
            # 尝试获取锁
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except IOError as e:
                    if e.errno != errno.EAGAIN:
                        raise
                    
                    # 检查是否超时
                    if self.timeout and time.time() - start_time > self.timeout:
                        logging.warning(f"等待锁超时: {self.lock_file}")
                        return False
                    
                    # 等待一段时间后再次尝试
                    time.sleep(1)
            
            # 将进程ID写入锁文件
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            
            self.locked = True
            logging.info(f"获取锁成功: {self.lock_file}")
            return True
        
        except Exception as e:
            logging.error(f"获取锁时出错: {str(e)}")
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            return False
    
    def release(self):
        """释放锁"""
        if self.locked and self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                self.lock_fd = None
                self.locked = False
                logging.info(f"释放锁成功: {self.lock_file}")
            except Exception as e:
                logging.error(f"释放锁时出错: {str(e)}")
```

## 在同步脚本中使用锁机制

锁机制已集成到`scripts/sync/sync_to_mysql_combined.py`脚本中：

```python
# 使用锁防止重叠执行
lock_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                        'data/sync_lock.pid')

# 如果请求则跳过锁
if args.no_lock:
    lock = type('DummyLock', (), {'__enter__': lambda x: x, '__exit__': lambda x, *args: None})()
    logging.info("锁机制已禁用")
else:
    lock = SyncLock(lock_file, args.lock_timeout)

with lock:
    # 如果无法获取锁，退出
    if not getattr(lock, 'locked', True):
        logging.warning("无法获取锁，另一个同步进程正在运行")
        return 0
    
    # 执行同步操作...
```

## 命令行参数

同步脚本支持以下与锁相关的命令行参数：

- `--no-lock`: 禁用锁机制
- `--lock-timeout SECONDS`: 设置等待锁的超时时间（秒）

## 使用示例

### 基本用法（带锁）

```bash
python3 scripts/sync/sync_to_mysql_combined.py --lock-timeout 60
```

这将启动同步进程，并在无法获取锁时等待最多60秒。

### 禁用锁机制

```bash
python3 scripts/sync/sync_to_mysql_combined.py --no-lock
```

这将启动同步进程，但不使用锁机制（不推荐在生产环境中使用）。

### 在Crontab中使用

```
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_combined.py --since-days 1 --lock-timeout 60 >> data/sync_cron.log 2>&1
```

这将每15分钟运行一次同步进程，使用60秒的锁超时时间。

## 故障排除

如果遇到与锁相关的问题：

1. **检查锁文件是否存在**：
   ```bash
   ls -l data/sync_lock.pid
   ```

2. **检查持有锁的进程**：
   ```bash
   cat data/sync_lock.pid
   ps -p $(cat data/sync_lock.pid)
   ```

3. **如果进程已经不存在但锁文件仍然存在**：
   ```bash
   rm data/sync_lock.pid
   ```

4. **检查同步日志**：
   ```bash
   tail -f data/sync_cron.log
   ```

## 总结

锁机制确保同步进程不会重叠执行，这对于大型数据库同步至关重要。通过使用文件锁和超时功能，系统可以优雅地处理并发同步请求，防止数据不一致和错误。
