# MCHost 自动续期脚本

自动登录 MCHost 并每隔 15 分钟点击 Renew 按钮，保持服务器在线。

## 功能特性

- ✅ 自动登录 MCHost（支持 Cloudflare 人机验证）
- ✅ 定时自动点击 Renew 按钮（默认 15 分钟）
- ✅ 失败自动重试机制
- ✅ 详细日志记录
- ✅ 后台运行（systemd 服务）
- ✅ 开机自启动
- ✅ 一键部署脚本

## 系统要求

- **操作系统**: Ubuntu 18.04+ / Debian 10+
- **Python**: 3.7+
- **内存**: 至少 512MB RAM（推荐 1GB+）
- **磁盘**: 至少 500MB 可用空间

## 快速开始

### 1️⃣ 克隆或下载项目

```bash
# 如果已经在项目目录，跳过此步
cd /home/user/test_MC
```

### 2️⃣ 一键部署

```bash
chmod +x deploy.sh
bash deploy.sh
```

部署脚本会自动：
- 安装 Python3 和依赖
- 安装 Playwright 和 Chromium 浏览器
- 创建虚拟环境
- 创建配置文件模板

### 3️⃣ 配置账号信息

编辑 `config.json` 文件：

```bash
nano config.json
```

填写以下信息：

```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false,
  "test_mode": true
}
```

**配置说明**：
- `mchost_url`: MCHost 登录页面的完整 URL
- `renew_interval_minutes`: 自动续期间隔（分钟），默认 15
- `headless`: 是否无头模式运行（false=显示浏览器窗口，true=无窗口后台运行）
- `test_mode`: 测试模式（true=只测试登录，false=正式运行）

**注意**：
- ❌ 不再需要在配置文件中填写用户名和密码！
- ✅ 首次需要手动登录一次
- ✅ 登录后会自动保存会话到 `cookies.json`
- ✅ 后续运行自动使用保存的会话，无需再次登录

### 4️⃣ 首次登录（选择一种方式）

由于 VPS 通常没有图形界面，你需要选择以下方式之一完成首次登录：

#### 🌟 方式A：在本地电脑登录（推荐）

**适用于**：你的本地电脑（Windows/Mac/Linux）有浏览器

1️⃣ **在本地电脑克隆项目**：

```bash
git clone <your-repo-url>
cd test_MC
```

2️⃣ **安装依赖**（只需 playwright）：

```bash
# 安装 Python 和 pip（如果没有）
# Windows: 从 python.org 下载安装
# Mac: brew install python3
# Linux: sudo apt-get install python3 python3-pip

# 安装 playwright
pip3 install playwright
playwright install chromium
```

3️⃣ **运行本地登录脚本**：

```bash
python3 local_login.py
```

脚本会：
- 打开浏览器窗口
- 等待你手动登录（填写账号、完成CF验证）
- 自动检测登录成功
- 保存 `cookies.json`

4️⃣ **上传 cookies 到服务器**：

```bash
scp cookies.json root@你的服务器IP:/root/test_MC/
```

5️⃣ **在服务器上配置并运行**：

```bash
# SSH 到服务器
ssh root@你的服务器IP

# 进入项目目录
cd /root/test_MC

# 修改配置
nano config.json
# 设置: "headless": true, "test_mode": false

# 运行脚本
./venv/bin/python mchost_renew.py
```

✅ **完成！** 脚本将自动使用 cookies 登录并开始自动续期。

---

#### 方式B：在 VPS 上使用虚拟显示（不推荐 - 复杂且看不到窗口）

VPS 没有图形界面，需要使用 xvfb（虚拟显示服务器）：

```bash
# 安装 xvfb
sudo apt-get install -y xvfb

# 确保配置
nano config.json
# 设置: "headless": false, "test_mode": true

# 使用 xvfb 运行
xvfb-run -a /root/test_MC/venv/bin/python /root/test_MC/mchost_renew.py
```

**缺点**：
- ❌ 你看不到浏览器窗口
- ❌ 无法人工验证 Cloudflare
- ❌ 只能通过截图判断状态
- ❌ 调试困难

⚠️ **强烈建议使用方式A（本地登录）**，更简单可靠。

---

### 5️⃣ 切换到正式运行模式

确认登录成功后，编辑 `config.json`：

```bash
nano config.json
```

修改以下设置：

```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": true,     // 改为 true（后台运行，不显示窗口）
  "test_mode": false    // 改为 false（正式运行模式）
}
```

再次运行，脚本将：
- ✅ 自动使用保存的 cookies 登录
- ✅ 无需手动操作
- ✅ 每 15 分钟自动点击 Renew 按钮
- ✅ 后台静默运行

```bash
./venv/bin/python mchost_renew.py
```

**如果会话过期**：脚本会提示你重新手动登录，删除 `cookies.json` 后重新运行即可。

### 6️⃣ 安装为系统服务（可选但推荐）

让脚本在后台自动运行并开机自启：

```bash
chmod +x install_service.sh
bash install_service.sh
```

## 使用说明

### 手动运行

```bash
# 在前台运行（用于测试）
./venv/bin/python mchost_renew.py
```

### 服务管理

安装为服务后，可以使用以下命令：

```bash
# 查看服务状态
sudo systemctl status mchost-renew

# 启动服务
sudo systemctl start mchost-renew

# 停止服务
sudo systemctl stop mchost-renew

# 重启服务
sudo systemctl restart mchost-renew

# 禁用开机自启
sudo systemctl disable mchost-renew

# 启用开机自启
sudo systemctl enable mchost-renew
```

### 查看日志

```bash
# 查看最新日志
tail -f /var/log/mchost_renew.log

# 查看 systemd 日志
sudo journalctl -u mchost-renew -f

# 查看最近 100 行日志
sudo journalctl -u mchost-renew -n 100
```

## 常见问题

### Q: Cloudflare 验证无法通过怎么办？

**A**: 脚本已经包含了基本的反检测措施，但 Cloudflare 可能仍然会拦截。解决方法：

1. 增加等待时间（修改脚本中的 `await asyncio.sleep()` 时间）
2. 尝试在本地（非 VPS）先测试，设置 `headless: false` 查看验证过程
3. 考虑使用代理 IP（需要修改脚本添加代理配置）

### Q: 脚本运行一段时间后失败怎么办？

**A**: 服务已配置自动重启（`Restart=always`），失败后会在 60 秒后自动重试。

### Q: 如何修改续期间隔？

**A**: 编辑 `config.json`，修改 `renew_interval_minutes` 的值（单位：分钟）。

### Q: 占用多少资源？

**A**:
- 内存：约 150-300MB（Chromium 浏览器）
- CPU：空闲时几乎为 0，点击时短暂上升
- 磁盘：约 200MB（浏览器 + 依赖）

### Q: 安全吗？密码会泄露吗？

**A**:
- 密码存储在本地 `config.json` 文件中
- 建议设置文件权限：`chmod 600 config.json`
- 所有操作都在本地 VPS 执行，不会发送到第三方

### Q: 如何卸载？

**A**:
```bash
# 停止并删除服务
sudo systemctl stop mchost-renew
sudo systemctl disable mchost-renew
sudo rm /etc/systemd/system/mchost-renew.service
sudo systemctl daemon-reload

# 删除项目文件
cd /home/user
rm -rf test_MC

# 删除日志
sudo rm /var/log/mchost_renew.log
```

## 故障排查

### 检查步骤

1. **检查配置文件**
   ```bash
   cat config.json
   ```

2. **检查服务状态**
   ```bash
   sudo systemctl status mchost-renew
   ```

3. **查看详细日志**
   ```bash
   tail -100 /var/log/mchost_renew.log
   ```

4. **检查截图**
   ```bash
   ls -lh /tmp/mchost_*.png
   ```

5. **手动测试**
   ```bash
   ./venv/bin/python mchost_renew.py
   ```

### 常见错误

| 错误信息 | 可能原因 | 解决方法 |
|---------|---------|---------|
| `配置文件不存在` | 未创建 config.json | 复制 `config.json.example` 为 `config.json` |
| `无法找到用户名输入框` | 网页结构变化或 URL 错误 | 检查 `mchost_url` 是否正确 |
| `登录失败` | 用户名/密码错误 | 检查 `config.json` 中的账号信息 |
| `找不到Renew按钮` | 未登录成功或页面变化 | 查看截图文件，检查实际页面状态 |

## 技术栈

- **Python 3**: 主要编程语言
- **Playwright**: 浏览器自动化框架
- **Chromium**: 无头浏览器
- **systemd**: Linux 服务管理

## 文件说明

```
test_MC/
├── mchost_renew.py          # 主程序脚本
├── config.json              # 配置文件（需要手动创建）
├── config.json.example      # 配置文件模板
├── deploy.sh                # 一键部署脚本
├── install_service.sh       # 服务安装脚本
├── mchost-renew.service     # systemd 服务配置
├── README.md                # 说明文档（本文件）
└── venv/                    # Python 虚拟环境（自动创建）
```

## 更新日志

### v1.0.0 (2025-11-26)
- ✨ 初始版本
- ✅ 支持自动登录和续期
- ✅ 支持 Cloudflare 验证
- ✅ 一键部署
- ✅ systemd 服务支持

## 许可证

MIT License

## 免责声明

本脚本仅供学习和个人使用，使用者需自行承担使用风险。请遵守 MCHost 的服务条款。

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**Made with ❤️ for MCHost users**
