# Capsolver 快速设置（推荐方案）

## 为什么推荐Capsolver？

如果你遇到以下情况：
- ✅ VNC中CF验证框不出现，页面无法操作
- ✅ Mac调试模式也失败
- ✅ 浏览器指纹被检测，无论如何都过不了

**Capsolver是目前唯一可靠的解决方案：**
- ✅ 95%+ 成功率
- ✅ 5秒内解决
- ✅ 完全自动化，无需人工干预
- ✅ 绕过所有浏览器指纹检测

## 快速设置（5分钟）

### 步骤1: 注册Capsolver账号

1. 访问：https://www.capsolver.com/
2. 点击右上角 "Sign Up"
3. 填写邮箱和密码
4. 验证邮箱

### 步骤2: 充值

1. 登录后，点击 "Deposit"
2. 最低充值 $5（可以解决约2000次CF验证）
3. 支持信用卡、加密货币等

### 步骤3: 获取API Key

1. 登录Capsolver Dashboard
2. 右上角点击你的头像
3. 选择 "API Key"
4. 复制你的API Key（格式: `CAP-xxxxxxxxxxxxxxxx`）

### 步骤4: 配置脚本

#### 多任务模式（服务器）

编辑 `tasks_config.json`:
```json
{
  "tasks": {
    "default": {
      "name": "我的MCHost服务器",
      "mchost_url": "https://freemchost.com/auth",
      "renew_interval_minutes": 15,

      "cf_solver_type": "capsolver",
      "capsolver_api_key": "CAP-你的API-KEY在这里",

      "manual_mode": true
    }
  }
}
```

**说明：**
- `cf_solver_type`: 设置为 `"capsolver"`
- `capsolver_api_key`: 粘贴你的API Key
- `manual_mode: true`: 作为备份，Capsolver失败时手动处理

#### 单任务模式（本地Mac）

创建 `config.json`:
```json
{
  "mchost_url": "https://freemchost.com/auth",
  "renew_interval_minutes": 15,
  "headless": false,

  "cf_solver_type": "capsolver",
  "capsolver_api_key": "CAP-你的API-KEY在这里"
}
```

### 步骤5: 运行脚本

```bash
# 多任务模式
python3 mchost_renew.py --task-id default

# 单任务模式
python3 mchost_renew.py
```

## 工作流程

1. 脚本访问MCHost
2. 检测到Cloudflare验证
3. **自动调用Capsolver API**
4. Capsolver在云端解决验证
5. 返回验证token
6. 脚本注入token，完成验证
7. 继续正常操作

**全程无需人工干预！**

## 日志示例

成功时你会看到：
```
⚠️ 检测到 Cloudflare 验证
🔐 使用Capsolver解决Cloudflare验证...
✓ 任务已创建: task-xxxxxxxx
等待验证... (3秒)
等待验证... (6秒)
✓ Cloudflare验证成功！
✓ 成功点击Renew按钮！
```

## 成本估算

### Capsolver定价
- **Turnstile**: $0.002 / 次
- **Challenge (5秒盾)**: $0.003 / 次

### 月度成本估算

**场景1：每15分钟Renew一次**
- 每小时：4次
- 每天：96次
- 每月：~2880次
- **月成本：** $5.76 - $8.64

**场景2：只在登录时用Capsolver，Renew不需要**
- 每天登录：1-2次
- 每月：~30-60次
- **月成本：** $0.06 - $0.18

### 节省技巧

1. **混合模式：** 只在登录时用Capsolver
   ```json
   {
     "cf_solver_type": "capsolver",
     "capsolver_api_key": "CAP-xxx",
     "manual_mode": true  // Renew时如果没有CF就不调用API
   }
   ```

2. **延长Renew间隔：**
   ```json
   {
     "renew_interval_minutes": 30  // 改为30分钟
   }
   ```
   月成本减半！

3. **使用cookies：** 手动登录一次，保存cookies
   - 只在session过期时才需要Capsolver
   - 每周手动更新一次cookies
   - 月成本：几乎为0

## 备选方案（如果不想付费）

### 方案1: FlareSolverr（免费）

```bash
# 部署FlareSolverr
./setup_flaresolverr.sh

# 配置
{
  "cf_solver_type": "flaresolverr",
  "flaresolverr_endpoint": "http://localhost:8191/v1",
  "manual_mode": true  // 作为备份
}
```

**成功率：** ~70%
**成本：** 免费

### 方案2: 完全手动模式

```json
{
  "manual_mode": true,
  "renew_interval_minutes": 15
}
```

- 首次运行时手动登录（包括CF验证）
- 保存cookies后自动Renew
- 每1-2周手动更新一次cookies

**成功率：** 100%（你自己手动）
**成本：** 免费（时间成本）

### 方案3: Mac本地运行

在Mac本地运行脚本：
```json
{
  "headless": false,
  "manual_mode": true
}
```

- 让浏览器显示在你的Mac屏幕上
- 遇到CF时你看着屏幕手动点击
- 其他时间自动Renew

**成功率：** 100%
**成本：** 免费（需要Mac一直开机）

## 测试Capsolver

创建测试脚本 `test_capsolver.py`:

```python
import asyncio
import aiohttp

async def test_capsolver():
    api_key = "CAP-你的API-KEY"

    # 创建测试任务
    task_data = {
        "clientKey": api_key,
        "task": {
            "type": "AntiTurnstileTaskProxyLess",
            "websiteURL": "https://freemchost.com/auth",
            "websiteKey": "0x4AAAAAAA..."  # 实际的site key
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.capsolver.com/createTask',
            json=task_data
        ) as resp:
            result = await resp.json()

            if result.get('errorId') == 0:
                print(f"✓ API Key有效！")
                print(f"  任务ID: {result.get('taskId')}")
                print(f"  余额足够")
            else:
                print(f"❌ 错误: {result.get('errorDescription')}")

asyncio.run(test_capsolver())
```

运行：
```bash
python3 test_capsolver.py
```

## 常见问题

### Q: API Key无效

**检查：**
1. API Key格式是否正确（`CAP-` 开头）
2. 是否复制完整（无空格）
3. 账号是否充值

### Q: 余额不足

登录 Capsolver Dashboard 充值。

### Q: 验证超时

Capsolver通常5-10秒解决。如果超时：
- 检查网络连接
- 检查Capsolver服务状态
- 查看日志中的错误信息

### Q: 还是失败

如果Capsolver也失败：
1. 查看日志中的具体错误
2. 可能是site key不正确
3. 联系Capsolver支持

## 推荐配置

### 生产环境（服务器24/7运行）

```json
{
  "cf_solver_type": "capsolver",
  "capsolver_api_key": "CAP-xxx",
  "manual_mode": false,
  "headless": true,
  "renew_interval_minutes": 20
}
```

完全自动化，无需任何人工干预。

### 开发/测试环境

```json
{
  "cf_solver_type": "capsolver",
  "capsolver_api_key": "CAP-xxx",
  "manual_mode": true,
  "headless": false
}
```

Capsolver失败时可以手动处理。

### 成本敏感

```json
{
  "cf_solver_type": "flaresolverr",
  "flaresolverr_endpoint": "http://localhost:8191/v1",
  "manual_mode": true,
  "capsolver_api_key": "CAP-xxx"
}
```

优先用免费的FlareSolverr，失败时才用Capsolver。
（需要修改代码实现fallback逻辑）

## 总结

**如果你的MCHost服务器很重要，强烈推荐Capsolver：**

✅ 可靠性高（95%+成功率）
✅ 完全自动化
✅ 节省时间
✅ 成本可控（~$6-9/月）

**$6/月买个安心，让脚本稳定运行，值得！**

## 获取帮助

- Capsolver官方文档：https://docs.capsolver.com/
- Capsolver Discord：https://discord.gg/capsolver
- 本项目Issues：提供日志和配置文件
