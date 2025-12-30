# Mac调试模式故障排查

## 问题描述

即使使用Mac本地的真实Chrome（调试模式），验证仍然失败。

## 可能的原因

### 1. Chrome调试模式本身的限制

即使是真实的Chrome，**开启调试端口后仍会有自动化特征**：

```bash
# 这个命令启动的Chrome仍然会被检测
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**问题：**
- ❌ Playwright连接后会注入额外的JavaScript
- ❌ CDP (Chrome DevTools Protocol) 连接会留下痕迹
- ❌ 某些浏览器API会被修改

### 2. 登录状态问题

如果你在Chrome中没有提前登录MCHost，脚本可能无法自动登录：

- ❌ 连接到现有Chrome时，脚本**不会**自动输入用户名密码
- ❌ 如果Chrome中没有保存的cookies，需要手动登录

### 3. Cookie/Session冲突

多个标签页或窗口可能导致session冲突。

## 解决方案

### 方案1: 完全手动模式（推荐Mac用户）

**不使用调试端口，让脚本仅作为监控和点击工具：**

#### 步骤1: 准备配置文件

创建 `config.json`:
```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false,
  "manual_mode": true,
  "test_mode": false
}
```

#### 步骤2: 首次运行，手动登录

```bash
python3 mchost_renew.py
```

- 浏览器会打开
- **你需要手动完成登录**（包括CF验证）
- 登录成功后，脚本会保存cookies
- 之后会自动Renew

**优点：**
- ✅ 完全真实的浏览器环境
- ✅ 手动登录一次后自动化
- ✅ CF验证成功率100%

### 方案2: 使用Chrome User Profile

**让脚本使用你的真实Chrome配置文件（包含已保存的登录）：**

#### 步骤1: 找到Chrome User Data目录

```bash
# Mac默认位置
~/Library/Application Support/Google/Chrome
```

#### 步骤2: 关闭所有Chrome窗口

**重要：** 必须完全关闭Chrome！

```bash
# 确认Chrome已关闭
ps aux | grep Chrome
# 应该没有Chrome进程
```

#### 步骤3: 配置

```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false,
  "use_user_profile": true,
  "chrome_user_data_dir": "~/Library/Application Support/Google/Chrome"
}
```

#### 步骤4: 运行

```bash
python3 mchost_renew.py
```

**优点：**
- ✅ 使用你的真实Chrome配置
- ✅ 已保存的登录信息和cookies
- ✅ 浏览器指纹完全真实

**注意：**
- ⚠️ Chrome必须完全关闭
- ⚠️ 可能会清除某些临时数据

### 方案3: 改进的调试模式（修复版）

如果一定要用调试模式，需要特殊处理：

#### 步骤1: 先在Chrome中手动登录MCHost

1. 正常打开Chrome
2. 访问 https://freemchost.com/auth
3. **手动完成登录**（包括CF验证）
4. 确保能看到Renew按钮
5. **保持Chrome打开**

#### 步骤2: 开启调试端口

在新终端中：
```bash
# 找到Chrome进程ID
ps aux | grep Chrome | grep -v grep

# 如果Chrome已经在运行，需要重启并加上调试端口
# 1. 完全关闭Chrome
# 2. 用调试模式启动
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome" &
```

#### 步骤3: 手动访问MCHost并登录

在Chrome中：
1. 访问 https://freemchost.com/auth
2. 手动登录（如果需要）
3. 完成CF验证
4. 确保看到Renew按钮

#### 步骤4: 运行脚本

修改配置：
```json
{
  "connect_to_existing_chrome": true,
  "chrome_debug_port": 9222,
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15
}
```

运行：
```bash
python3 mchost_renew.py
```

**脚本会：**
- 连接到已运行的Chrome
- 在新标签页打开MCHost
- 自动点击Renew（每15分钟）

**关键点：**
- ✅ Chrome中已经登录
- ✅ 脚本只负责打开标签页和点击
- ✅ 不涉及自动输入或CF处理

### 方案4: Capsolver自动化（终极方案）

如果上述方案都不行，使用专业的CF解决服务：

```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false,
  "cf_solver_type": "capsolver",
  "capsolver_api_key": "CAP-YOUR-API-KEY"
}
```

**优点：**
- ✅ 完全自动化
- ✅ 95%+ 成功率
- ✅ 不需要手动干预

**成本：**
- 约 $0.002-0.003 每次验证
- 每天Renew 100次 ≈ $6-9/月

### 方案5: 分离登录和Renew

**最稳定的方案：**

#### 原理
1. 手动登录一次（在真实Chrome中）
2. 导出cookies
3. 脚本只做Renew（使用cookies）

#### 步骤

**A. 手动登录并导出cookies**

使用浏览器插件导出cookies：
- [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/)
- [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/)

1. 在Chrome中登录MCHost
2. 完成CF验证
3. 使用插件导出cookies为JSON
4. 保存为 `cookies.json`

**B. 配置脚本使用cookies**

将 `cookies.json` 放到项目目录下，脚本会自动加载。

**C. 运行脚本**

```bash
python3 mchost_renew.py
```

脚本会：
1. 加载cookies
2. 直接访问MCHost（已登录状态）
3. 定期点击Renew

**优点：**
- ✅ 绕过所有登录问题
- ✅ 绕过CF验证（已经在真实浏览器中完成）
- ✅ 脚本只需点击Renew

**维护：**
- 每隔1-2周手动更新一次cookies（session过期时）

## 诊断工具

### 1. 测试当前状态

```bash
python3 diagnose_current_state.py
```

这会告诉你：
- 浏览器能否访问MCHost
- 是否被CF阻止
- 是否有登录表单
- JavaScript环境是否正常

### 2. 检查Chrome调试端口

```bash
# 检查端口是否开启
lsof -i :9222

# 测试连接
curl http://localhost:9222/json
```

应该返回Chrome的调试信息JSON。

### 3. 手动测试CDP连接

创建测试脚本：
```python
import asyncio
from playwright.async_api import async_playwright

async def test_cdp():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9222')
        print(f"✓ 连接成功")
        print(f"  Contexts: {len(browser.contexts)}")

        if browser.contexts:
            context = browser.contexts[0]
            print(f"  Pages: {len(context.pages)}")
            print(f"  Cookies: {len(await context.cookies())}")

        await browser.close()

asyncio.run(test_cdp())
```

## 常见错误和解决

### 错误1: "ECONNREFUSED"

**原因：** Chrome调试端口未开启

**解决：**
```bash
# 确认Chrome以调试模式启动
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### 错误2: "验证失败"即使在真实Chrome中

**原因：** CDP连接改变了浏览器环境

**解决：** 使用方案1（完全手动模式）或方案5（分离登录）

### 错误3: "No contexts available"

**原因：** Chrome刚启动，还没有打开任何页面

**解决：** 先在Chrome中打开一个标签页

### 错误4: Session冲突

**原因：** 多个标签页同时操作MCHost

**解决：**
- 关闭其他MCHost标签页
- 只让脚本管理一个标签页

## 推荐配置（Mac用户）

### 最简单：完全手动模式

```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false,
  "manual_mode": true
}
```

首次运行手动登录，之后自动化。

### 最稳定：Cookie模式

```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false
}
```

手动导出cookies到 `cookies.json`，脚本自动加载。

### 最自动：Capsolver

```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false,
  "cf_solver_type": "capsolver",
  "capsolver_api_key": "YOUR_KEY"
}
```

完全自动，无需任何手动操作。

## 总结

**Mac调试模式失败的根本原因：**
- CDP连接会改变浏览器环境
- Playwright注入会留下痕迹
- 即使是真实Chrome，连接后也有自动化特征

**最佳实践（Mac）：**

1. 🥇 **首选：完全手动模式** - 首次手动登录，之后自动Renew
2. 🥈 **次选：Cookie分离** - 真实浏览器登录，脚本只做Renew
3. 🥉 **备选：Capsolver** - 完全自动化，无需手动

**不推荐（Mac）：**
- ❌ 调试端口模式（connect_to_existing_chrome）- 问题太多
- ❌ Headless模式 - 更容易被检测

关键是：**让真实浏览器处理登录和CF，脚本只负责定期点击Renew**。
