# MCHost 多任务自动续期管理系统

自动化管理多个 MCHost 服务器，定时点击 Renew 按钮保持在线，提供 Web 管理界面实时监控和手动控制。

## ✨ 功能特性

### 🎯 核心功能
- ✅ **多任务管理** - 同时管理多个 MCHost 服务器
- ✅ **自动续期** - 定时自动点击 Renew 按钮（可自定义间隔）
- ✅ **Cookie认证** - 无需密码，使用浏览器 Cookie 登录
- ✅ **失败重试** - 自动检测会话过期并重连
- ✅ **后台运行** - systemd 服务，开机自启

### 🖥️ Web 管理界面
- ✅ **任务管理** - 创建、编辑、删除、启动、停止任务
- ✅ **实时监控** - 查看任务状态、运行日志、截图
- ✅ **手动控制** - 立即截图、立即 Renew、延迟 Renew
- ✅ **人工校正** - 调整下次点击时间而不改变固定间隔
- ✅ **密码保护** - 安全访问控制
- ✅ **快速刷新** - 5秒自动刷新，操作后立即显示结果

### 📸 智能截图
- ✅ 自动保存每次 Renew 的截图
- ✅ 支持手动立即截图查看当前状态
- ✅ 显示最近 20 张截图
- ✅ Lightbox 全屏查看
- ✅ 自动清理旧截图（保留50张）

## 🚀 快速开始

### 1️⃣ 系统要求

- **操作系统**: Ubuntu 18.04+ / Debian 10+
- **Python**: 3.8+
- **内存**: 至少 1GB RAM
- **磁盘**: 至少 1GB 可用空间

### 2️⃣ 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd test_MC

# 一键部署（安装所有依赖）
chmod +x deploy.sh
bash deploy.sh
```

部署脚本会自动安装：
- Python3 和 pip
- Playwright 和 Chromium
- Flask（Web界面）
- 创建虚拟环境

### 3️⃣ 启动 Web 管理界面

#### 方式一：手动运行（测试用）

```bash
./venv/bin/python web_viewer.py
```

访问: `http://你的服务器IP:5000`
默认密码: `mchost123`

#### 方式二：安装为服务（推荐）

```bash
chmod +x install_viewer.sh
bash install_viewer.sh
```

安装时可设置自定义密码（直接回车使用默认密码）。

### 4️⃣ 创建第一个任务

1. **登录 Web 界面**
   - 访问 `http://你的服务器IP:5000`
   - 输入密码登录

2. **获取 Cookies**（在本地电脑操作）
   - 在浏览器登录 MCHost
   - 按 F12 打开开发者工具
   - 切换到"应用程序"或"Application"标签
   - 左侧找到"Cookie" → 点击你的 MCHost 域名
   - 复制所有 Cookie（或使用插件导出为 JSON）

3. **创建任务**
   - 点击"新建任务"
   - 填写任务信息：
     - **任务 ID**: 例如 `server1`（只能用小写字母、数字、下划线、连字符）
     - **任务名称**: 例如 `我的主服务器`
     - **MCHost URL**: 包含 Renew 按钮的页面 URL
     - **续期间隔**: 推荐 15 分钟
     - **Cookies JSON**: 粘贴从浏览器复制的 Cookie JSON
   - 点击"保存"

4. **启动任务**
   - 在任务列表找到刚创建的任务
   - 点击"启动"按钮
   - 任务将开始自动运行

5. **查看运行状态**
   - 点击"详情"进入任务详情页
   - 查看最新截图和运行日志
   - 使用手动控制功能测试

## 📖 使用指南

### Web 界面操作

#### 任务列表页面

- **新建任务**: 点击右上角"新建任务"
- **查看详情**: 点击任务卡片的"详情"按钮
- **编辑任务**: 修改任务配置、更新 Cookies
- **启动/停止**: 控制任务运行状态
- **重启任务**: 重启正在运行的任务
- **删除任务**: 永久删除任务（不可恢复）

#### 任务详情页面

**截图区域**
- 查看最近 20 张截图（按时间倒序）
- 点击截图可全屏查看
- 点击"立即截图"按钮实时捕获当前页面

**手动控制面板**

1. **立即 Renew**
   - 马上点击 Renew 按钮
   - 点击后重置计时器
   - 继续按原间隔运行

2. **延迟 Renew**
   - 设置 N 分钟后点击 Renew
   - 适用于人工校正时间
   - 点击后继续按原间隔运行
   - 例如：设置 4 分钟，4分钟后点击，然后继续每 15 分钟自动点击

**运行日志**
- 显示最近 100 行日志
- 彩色高亮（错误、警告、成功）
- 实时更新

### Cookie 导出方法

#### 方法一：Chrome DevTools（推荐）

1. 在 Chrome 登录 MCHost
2. 按 F12 打开开发者工具
3. 切换到"应用程序"(Application) 标签
4. 左侧 Cookie → 选择你的域名
5. 手动复制所有字段构造 JSON

JSON 格式示例：
```json
[
  {
    "name": "session",
    "value": "your-session-value",
    "domain": ".freemchost.com",
    "path": "/",
    "expires": 1234567890,
    "httpOnly": true,
    "secure": true,
    "sameSite": "Lax"
  }
]
```

#### 方法二：使用浏览器插件

Chrome/Edge: "EditThisCookie" 或 "Cookie-Editor"
Firefox: "Cookie Quick Manager"

导出为 JSON 格式即可使用。

### 任务配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| 任务 ID | 唯一标识符，创建后不可修改 | `server1` |
| 任务名称 | 显示名称，可随时修改 | `我的主服务器` |
| MCHost URL | 包含 Renew 按钮的页面 URL | `https://freemchost.com/dashboard` |
| 续期间隔 | 自动点击间隔（分钟） | `15` |
| Cookies | 登录会话 Cookie（JSON 数组） | 见上方示例 |

### 手动控制使用场景

**场景 1: Cookie 快过期**
- 使用"立即 Renew"提前续期
- 避免会话失效导致服务中断

**场景 2: 时间不对**
- 当前时间：14:37
- 原计划：15:00 点击
- 你想改到：14:40 点击
- 操作：设置"延迟 3 分钟"
- 结果：14:40 点击，然后 14:55、15:10...

**场景 3: 检查状态**
- 使用"立即截图"查看当前页面
- 确认登录状态、Renew 按钮是否正常

## 🔧 服务管理

### Web Viewer 服务

```bash
# 查看状态
sudo systemctl status mchost-viewer

# 启动/停止/重启
sudo systemctl start mchost-viewer
sudo systemctl stop mchost-viewer
sudo systemctl restart mchost-viewer

# 查看日志
sudo journalctl -u mchost-viewer -f

# 修改密码
sudo nano /etc/systemd/system/mchost-viewer.service
# 修改: Environment="VIEWER_PASSWORD=新密码"
sudo systemctl daemon-reload
sudo systemctl restart mchost-viewer
```

### 任务管理

所有任务通过 Web 界面管理，无需手动操作服务。

任务进程由 `task_manager.py` 统一管理：
- 自动监控任务状态
- 自动重启崩溃的任务
- 每 30 秒检查一次
- 日志位于：`/var/log/mchost_manager.log`

## 📁 文件结构

```
test_MC/
├── mchost_renew.py          # 主程序脚本（支持单/多任务）
├── task_manager.py          # 任务管理器后端
├── web_viewer.py            # Web 管理界面
├── local_login.py           # 本地登录工具（可选）
├── deploy.sh                # 一键部署脚本
├── install_viewer.sh        # Web 服务安装脚本
├── mchost-viewer.service    # Web 服务配置
├── tasks_config.json        # 多任务配置（自动生成）
├── tasks/                   # 任务数据目录
│   └── {task_id}/          # 各任务独立目录
│       ├── cookies.json     # 任务 Cookie
│       ├── screenshots/     # 任务截图
│       └── task.log         # 任务日志
└── venv/                    # Python 虚拟环境
```

## ⚙️ 高级功能

### 本地登录工具（可选）

如果你有本地电脑环境，可以使用 `local_login.py` 生成 Cookie：

```bash
# 在本地电脑
python3 local_login.py
```

脚本会：
1. 打开浏览器窗口
2. 等待你手动登录
3. 自动检测登录成功
4. 保存 `cookies.json`

然后上传到服务器：
```bash
scp cookies.json root@服务器IP:/root/test_MC/tasks/任务ID/
```

### 单任务模式（向后兼容）

如果只需管理一个服务器，可以使用单任务模式：

```bash
# 创建配置文件
cp config.json.example config.json
nano config.json

# 手动运行
./venv/bin/python mchost_renew.py
```

配置文件 `config.json`:
```json
{
  "mchost_url": "https://freemchost.com/dashboard",
  "renew_interval_minutes": 15,
  "headless": true,
  "test_mode": false
}
```

需要手动准备 `cookies.json` 文件。

## ❓ 常见问题

### Q: 任务启动后没有响应？

**A**: 检查以下几点：
1. 查看任务日志：进入任务详情页查看日志
2. 确认 Cookie 是否有效：Cookie 可能已过期
3. 检查 URL 是否正确：必须是包含 Renew 按钮的页面
4. 重启任务：点击"重启"按钮

### Q: 点击"立即截图"没反应？

**A**:
1. 等待 3-5 秒后刷新页面（处理需要时间）
2. 查看任务日志是否有错误信息
3. 确认任务正在运行（状态显示🟢运行中）
4. 检查浏览器是否已初始化（查看日志）

### Q: Cookie 如何更新？

**A**:
1. 进入任务详情页
2. 点击"编辑"按钮
3. 在 Cookies JSON 框中粘贴新的 Cookie
4. 点击"保存"
5. 重启任务使新 Cookie 生效

### Q: 如何修改续期间隔？

**A**:
1. 点击任务的"编辑"按钮
2. 修改"续期间隔"数值
3. 保存并重启任务

### Q: 页面刷新太慢？

**A**:
- 页面每 5 秒自动刷新
- 可以手动按 F5 刷新
- 操作后等待 3-5 秒会自动跳转并显示结果

### Q: 占用多少资源？

**A**:
- 每个任务约 150-300MB 内存（Chromium 浏览器）
- CPU 空闲时几乎为 0
- Web 界面约 50MB 内存
- 建议：2 个任务以下用 1GB RAM，更多任务建议 2GB+

### Q: 如何备份任务数据？

**A**:
```bash
# 备份配置和 Cookie
tar -czf mchost_backup.tar.gz tasks_config.json tasks/

# 恢复
tar -xzf mchost_backup.tar.gz
```

### Q: 如何完全卸载？

**A**:
```bash
# 停止所有服务
sudo systemctl stop mchost-viewer
sudo systemctl disable mchost-viewer
sudo rm /etc/systemd/system/mchost-viewer.service
sudo systemctl daemon-reload

# 删除项目文件
rm -rf /root/test_MC

# 删除日志
sudo rm /var/log/mchost_manager.log
```

## 🔒 安全建议

1. **修改默认密码**
   ```bash
   # 安装时设置密码，或修改服务文件
   sudo nano /etc/systemd/system/mchost-viewer.service
   ```

2. **限制访问 IP**（可选）
   - 使用防火墙规则限制 5000 端口访问
   - 或通过 Nginx 反向代理添加 IP 白名单

3. **定期更新 Cookie**
   - Cookie 可能有有效期
   - 建议每月更新一次

4. **备份配置文件**
   - 定期备份 `tasks_config.json` 和 `tasks/` 目录

## 📊 监控和告警

### 查看管理器日志
```bash
tail -f /var/log/mchost_manager.log
```

### 查看任务日志
```bash
# 通过 Web 界面查看（推荐）
# 或直接查看文件
tail -f /root/test_MC/tasks/任务ID/task.log
```

### 监控任务状态
- Web 界面会显示任务运行状态
- 绿色🟢 = 运行中
- 红色🔴 = 已停止

## 🎯 最佳实践

1. **命名规范**
   - 任务 ID 使用描述性名称：`main_server`, `backup_server`
   - 任务名称用中文方便识别：`主服务器`, `备用服务器`

2. **续期间隔**
   - 推荐 15 分钟
   - 不要设置太短（< 5 分钟）可能被检测为异常
   - 不要设置太长（> 30 分钟）可能超时

3. **定期检查**
   - 每周查看一次任务状态
   - 查看截图确认正常运行
   - 检查日志是否有错误

4. **Cookie 管理**
   - 保存一份 Cookie 备份
   - Cookie 失效时可快速恢复
   - 建议使用浏览器插件管理 Cookie

## 📝 更新日志

### v2.0.0 (2025-11-30)
- ✨ **多任务管理系统** - 支持管理多个服务器
- ✨ **Web 管理界面** - 完整的任务 CRUD 操作
- ✨ **手动触发控制** - 立即截图、立即 Renew、延迟 Renew
- ✨ **人工校正功能** - 灵活调整下次执行时间
- ⚡ **快速响应** - 2秒检测间隔，5秒页面刷新
- 📸 **实时截图** - 随时查看当前页面状态
- 🎨 **美化界面** - 现代化卡片式设计
- 🔧 **架构重构** - task_manager 统一管理所有任务

### v1.1.0 (2025-11-26)
- ✨ 新增 Web 监控界面
- ✅ 支持远程查看 Renew 截图
- ✅ 支持实时查看日志

### v1.0.0 (2025-11-26)
- ✨ 初始版本
- ✅ Cookie-based 登录机制
- ✅ 支持自动续期

## 🛠️ 技术栈

- **Python 3.8+** - 主要编程语言
- **Playwright** - 浏览器自动化
- **Flask** - Web 框架
- **Chromium** - 无头浏览器
- **systemd** - 服务管理

## 📜 许可证

MIT License

## ⚠️ 免责声明

本项目仅供学习和个人使用。使用者需自行承担使用风险，并遵守 MCHost 服务条款。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Made with ❤️ for MCHost users**
