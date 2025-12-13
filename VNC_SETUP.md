# VNC远程桌面设置指南

## 为什么需要VNC？

Cloudflare验证（CF验证）是专门设计来防止机器人的，纯自动化脚本很难通过这种验证。当MCHost网站启用CF验证时，你需要手动完成验证。

VNC远程桌面允许你在浏览器中查看和操作服务器上的浏览器窗口，从而手动完成Cloudflare验证。

## 安装步骤

### 1. 运行VNC安装脚本

```bash
cd /path/to/test_MC
bash install_vnc.sh
```

安装脚本会自动安装以下组件：
- Xvfb：虚拟显示服务器
- x11vnc：VNC服务器
- noVNC：Web界面的VNC客户端

### 2. 启动VNC服务

```bash
# 启动VNC服务
sudo systemctl start mchost-vnc

# 设置开机自启（可选）
sudo systemctl enable mchost-vnc

# 查看服务状态
sudo systemctl status mchost-vnc
```

### 3. 验证VNC正在运行

```bash
# 检查进程
ps aux | grep -E "Xvfb|x11vnc|websockify"

# 检查端口
netstat -tlnp | grep -E "5900|6080"
```

你应该看到：
- Xvfb运行在DISPLAY :99
- x11vnc监听5900端口
- noVNC监听6080端口

## 使用方法

### 启用手动干预模式

1. 打开Web管理界面：`http://服务器IP:5001`
2. 进入任务详情页
3. 找到"VNC远程桌面"部分
4. 点击"启用手动模式"按钮
5. **重启任务**使配置生效：
   ```bash
   # 方法1：通过Web界面停止并启动任务
   # 方法2：通过命令行
   sudo systemctl restart mchost-renew@default  # 替换default为你的任务ID
   ```

### 访问VNC远程桌面

#### 方法1：通过Web界面（推荐）

1. 在任务详情页点击"打开VNC远程桌面"按钮
2. 会在新标签页打开noVNC界面
3. 点击"连接"按钮即可看到服务器上的浏览器

#### 方法2：直接访问

在浏览器中打开：`http://服务器IP:6080/vnc.html`

### 处理Cloudflare验证

1. **自动检测**：当脚本检测到Cloudflare验证时，会在日志中显示：
   ```
   ⚠️ 检测到 Cloudflare 验证
   🖥️ 手动干预模式 - 请在VNC界面中完成Cloudflare验证
      访问: http://服务器IP:6080/vnc.html
   ```

2. **手动处理**：
   - 打开VNC界面
   - 你会看到服务器上的浏览器窗口显示CF验证
   - 完成人机验证（点击复选框、图片验证等）
   - 验证通过后，脚本会自动继续运行

3. **等待超时**：
   - 脚本会等待最多5分钟让你完成验证
   - 每30秒会在日志中显示等待进度
   - 验证通过后会显示：`✓ Cloudflare验证已通过！`

## 工作原理

```
┌─────────────────┐
│   你的浏览器    │
│                 │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  noVNC (6080)   │  ← Web界面的VNC客户端
│                 │
└────────┬────────┘
         │ WebSocket
         ▼
┌─────────────────┐
│  x11vnc (5900)  │  ← VNC服务器
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Xvfb (:99)     │  ← 虚拟显示
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chromium       │  ← MCHost脚本的浏览器
│  (headed mode)  │
└─────────────────┘
```

## 配置说明

### manual_mode参数

在`tasks_config.json`中：

```json
{
  "tasks": {
    "default": {
      "name": "Default Task",
      "mchost_url": "https://freemchost.com/dashboard",
      "renew_interval_minutes": 15,
      "manual_mode": true,  ← 启用手动干预模式
      "enabled": true
    }
  }
}
```

- `manual_mode: false`（默认）：headless模式，遇到CF时等待30秒尝试自动通过
- `manual_mode: true`：headed模式，浏览器显示在VNC上，遇到CF时暂停等待手动处理

## 故障排除

### VNC无法连接

1. 检查VNC服务是否运行：
   ```bash
   sudo systemctl status mchost-vnc
   ```

2. 检查端口是否被占用：
   ```bash
   netstat -tlnp | grep -E "5900|6080"
   ```

3. 查看VNC日志：
   ```bash
   sudo journalctl -u mchost-vnc -n 50
   ```

### 浏览器没有显示在VNC上

1. 确认已启用manual_mode并重启任务
2. 检查DISPLAY环境变量：
   ```bash
   # 在mchost_renew.py日志中应该看到
   🖥️ 手动干预模式已启用 - 浏览器将显示在VNC桌面上
   ```

### CF验证超时

- 默认等待5分钟，如果需要更长时间，可以修改`mchost_renew.py`中的`max_wait`参数
- 检查网络连接是否稳定
- 尝试在VNC中刷新页面

## 安全建议

1. **修改默认端口**（可选）：
   编辑`~/start_vnc.sh`修改6080端口

2. **设置VNC密码**（推荐）：
   ```bash
   # 编辑start_vnc.sh，将x11vnc启动命令中的-nopw改为：
   x11vnc -display :99 -forever -shared -rfbport 5900 -passwd yourpassword &
   ```

3. **使用防火墙**：
   ```bash
   # 只允许特定IP访问VNC端口
   sudo ufw allow from 你的IP地址 to any port 6080
   ```

4. **使用SSH隧道**（最安全）：
   ```bash
   # 在本地电脑执行
   ssh -L 6080:localhost:6080 user@服务器IP
   # 然后在本地访问 http://localhost:6080/vnc.html
   ```

## 性能优化

### 关闭不需要的任务的manual_mode

手动模式会使用更多资源（因为是headed模式），如果某个任务不再需要手动处理CF：

1. 在Web界面关闭该任务的"手动干预模式"
2. 重启该任务

### 资源使用

- headless模式：~100MB内存
- headed模式（VNC）：~300MB内存
- Xvfb + VNC服务：~50MB内存

## 常见问题

**Q: 我必须一直保持VNC连接吗？**
A: 不需要。VNC只在需要处理CF验证时才打开，平时可以关闭VNC标签页。

**Q: 多个任务可以同时使用VNC吗？**
A: 可以，所有启用manual_mode的任务都会显示在同一个VNC桌面上（:99 display）。

**Q: 如果我不在电脑前，脚本会一直等待吗？**
A: 会等待5分钟，超时后任务会失败。建议在预期会遇到CF时才启用manual_mode。

**Q: 可以在手机上使用VNC吗？**
A: 可以，noVNC是基于Web的，在手机浏览器中也可以访问。

## 卸载

如果不再需要VNC功能：

```bash
# 停止并禁用服务
sudo systemctl stop mchost-vnc
sudo systemctl disable mchost-vnc

# 删除服务文件
sudo rm /etc/systemd/system/mchost-vnc.service
sudo systemctl daemon-reload

# 删除VNC相关包（可选）
sudo apt remove xvfb x11vnc  # 或 yum remove
sudo rm -rf /opt/noVNC

# 删除启动脚本
rm ~/start_vnc.sh ~/stop_vnc.sh
```
