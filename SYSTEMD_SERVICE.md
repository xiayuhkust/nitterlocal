# Nitterlocal Backend Systemd 服务使用指南

本文档详细介绍了如何安装、配置和管理 Nitterlocal Backend 的 systemd 服务，确保服务稳定运行并在系统重启后自动启动。

## 目录

1. [安装服务](#安装服务)
2. [服务管理](#服务管理)
3. [日志查看](#日志查看)
4. [配置修改](#配置修改)
5. [故障排除](#故障排除)
6. [卸载服务](#卸载服务)

## 安装服务

安装 systemd 服务非常简单，只需运行提供的安装脚本：

```bash
cd /home/ubuntu/nitterlocal
sudo ./install_service.sh
```

此脚本会执行以下操作：

1. 安装所需的依赖项
2. 将服务文件复制到 systemd 目录
3. 启用并启动服务
4. 显示初始服务状态

安装完成后，服务将自动运行并在系统启动时自动启动。

## 服务管理

### 查看服务状态

要查看服务的当前状态，运行：

```bash
sudo systemctl status nitterlocal-backend
```

输出示例：
```
● nitterlocal-backend.service - Nitterlocal Backend Service
     Loaded: loaded (/etc/systemd/system/nitterlocal-backend.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2025-03-13 22:05:08 CST; 7s ago
   Main PID: 4010510 (python3)
      Tasks: 5 (limit: 4326)
     Memory: 123.0M
        CPU: 2.090s
     CGroup: /system.slice/nitterlocal-backend.service
             ├─4010510 /usr/bin/python3 -m app.main --host 0.0.0.0 --port 8000
             ├─4010525 /usr/bin/python3 -c "from multiprocessing.resource_tracker import main;main(4)"
             └─4010526 /usr/bin/python3 -c "from multiprocessing.spawn import spawn_main; spawn_main(tracker_fd=5, pipe_handle=7)" --multiprocessing-fork
```

### 启动服务

如果服务未运行，可以使用以下命令启动：

```bash
sudo systemctl start nitterlocal-backend
```

### 停止服务

需要停止服务时，运行：

```bash
sudo systemctl stop nitterlocal-backend
```

### 重启服务

在更新代码或配置后，需要重启服务以应用更改：

```bash
sudo systemctl restart nitterlocal-backend
```

### 启用/禁用自动启动

要使服务在系统启动时自动启动（默认已启用）：

```bash
sudo systemctl enable nitterlocal-backend
```

要禁用自动启动：

```bash
sudo systemctl disable nitterlocal-backend
```

## 日志查看

### 查看所有日志

查看服务的所有日志：

```bash
sudo journalctl -u nitterlocal-backend
```

### 实时查看日志

实时监控日志输出（类似 `tail -f`）：

```bash
sudo journalctl -u nitterlocal-backend -f
```

### 查看最近日志

只查看最近的日志条目：

```bash
sudo journalctl -u nitterlocal-backend -n 50
```

### 按时间过滤日志

查看特定时间段的日志：

```bash
# 查看今天的日志
sudo journalctl -u nitterlocal-backend --since today

# 查看过去一小时的日志
sudo journalctl -u nitterlocal-backend --since "1 hour ago"

# 查看特定时间范围的日志
sudo journalctl -u nitterlocal-backend --since "2025-03-13 10:00:00" --until "2025-03-13 11:00:00"
```

## 配置修改

### 服务配置文件

服务配置文件位于：

```
/etc/systemd/system/nitterlocal-backend.service
```

### 修改服务配置

如需修改服务配置（如端口、主机等），请编辑服务文件：

```bash
sudo nano /etc/systemd/system/nitterlocal-backend.service
```

服务文件内容示例：

```ini
[Unit]
Description=Nitterlocal Backend Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/nitterlocal
ExecStart=/usr/bin/python3 -m app.main --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nitterlocal-backend
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

修改后，需要重新加载 systemd 配置并重启服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart nitterlocal-backend
```

### 环境变量配置

如果需要添加环境变量（如数据库连接信息），可以在服务文件的 `[Service]` 部分添加 `Environment` 行：

```ini
[Service]
...
Environment=MYSQL_HOST=43.135.26.222
Environment=MYSQL_USER=root
Environment=MYSQL_PASSWORD=your_password
Environment=MYSQL_DATABASE=kol_info
...
```

## 故障排除

### 服务启动失败

如果服务无法启动，首先查看详细的错误日志：

```bash
sudo journalctl -u nitterlocal-backend -n 50
```

常见问题及解决方案：

1. **端口被占用**：
   - 错误信息：`ERROR: [Errno 98] Address already in use`
   - 解决方案：更改端口或停止占用该端口的其他服务

2. **IP绑定错误**：
   - 错误信息：`ERROR: [Errno 99] Cannot assign requested address`
   - 解决方案：使用 `0.0.0.0` 而不是特定 IP 地址

3. **依赖项缺失**：
   - 错误信息：`ImportError: No module named 'xxx'`
   - 解决方案：安装缺失的依赖项 `pip install xxx`

4. **权限问题**：
   - 错误信息：`PermissionError: [Errno 13] Permission denied`
   - 解决方案：检查文件权限和用户权限

### 服务运行但无法访问

如果服务显示为运行状态，但无法通过浏览器访问：

1. 检查防火墙设置：
   ```bash
   sudo ufw status
   ```

2. 如果防火墙启用，确保允许端口访问：
   ```bash
   sudo ufw allow 8000
   ```

3. 检查服务是否真正在监听端口：
   ```bash
   sudo netstat -tulpn | grep 8000
   ```

### 服务频繁重启

如果服务频繁重启，可能是由于代码错误或资源问题：

1. 查看详细错误日志：
   ```bash
   sudo journalctl -u nitterlocal-backend -n 100
   ```

2. 修改重启策略（增加重启间隔）：
   ```bash
   sudo nano /etc/systemd/system/nitterlocal-backend.service
   # 修改 RestartSec=10 为更大的值，如 RestartSec=30
   sudo systemctl daemon-reload
   sudo systemctl restart nitterlocal-backend
   ```

## 卸载服务

如果需要卸载服务，可以使用提供的卸载脚本：

```bash
cd /home/ubuntu/nitterlocal
sudo ./uninstall_service.sh
```

或手动卸载：

```bash
sudo systemctl stop nitterlocal-backend
sudo systemctl disable nitterlocal-backend
sudo rm /etc/systemd/system/nitterlocal-backend.service
sudo systemctl daemon-reload
```

## 总结

使用 systemd 管理 Nitterlocal Backend 服务可以确保服务的稳定性和可靠性。通过本文档中的命令，您可以轻松管理服务的启动、停止、重启，查看日志，以及排除常见问题。

如有任何问题，请查看详细的日志输出，这通常能提供解决问题所需的信息。
