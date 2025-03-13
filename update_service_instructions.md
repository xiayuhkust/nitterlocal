# 更新后端服务配置

我们发现了服务启动失败的原因：尝试绑定到特定IP地址（43.132.129.242）时出错。

## 解决方案

我已经更新了systemd服务配置，将监听地址从特定IP改为0.0.0.0（接受所有网络接口的连接）。

## 更新步骤

1. 拉取最新代码：
```bash
cd /home/ubuntu/nitterlocal
git checkout 242ubuntu
git pull
```

2. 更新服务文件：
```bash
sudo cp nitterlocal-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
```

3. 重启服务：
```bash
sudo systemctl restart nitterlocal-backend
```

4. 检查服务状态：
```bash
sudo systemctl status nitterlocal-backend
```

## 故障排除

如果服务仍然无法启动，请运行以下命令查看详细日志：
```bash
sudo journalctl -u nitterlocal-backend -n 50
```

## 手动测试

您也可以手动测试后端服务是否能正常运行：
```bash
cd /home/ubuntu/nitterlocal
python3 -m app.main --host 0.0.0.0 --port 8000
```

如果手动运行成功但systemd服务仍然失败，可能是环境变量或路径问题。
