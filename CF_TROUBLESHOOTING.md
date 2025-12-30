# Cloudflare验证故障排查指南

本文档帮助您解决Cloudflare验证失败的问题。

## 问题症状

- VNC中能看到浏览器窗口
- 可以手动点击Cloudflare验证框
- 但验证仍然失败，脚本报错

## 最新改进（已集成到脚本）

### 1. 增强的CF检测

**改进前：** 只检测 `iframe[src*="challenges.cloudflare.com"]`
**改进后：** 检测多种CF元素类型：
- `iframe[src*="challenges.cloudflare.com"]` - CF挑战iframe
- `iframe[src*="cloudflare"]` - 通用CF iframe
- `#cf-wrapper` - CF包装器
- `.cf-browser-verification` - 浏览器验证元素
- `[id^="cf-"]` - 所有CF开头的元素
- `[data-sitekey]` - Turnstile验证组件

### 2. 改进的手动验证检测逻辑

**改进前：**
- 每10秒检查一次
- 只检查iframe是否消失
- 不验证可见性

**改进后：**
- 每3秒检查一次（更快响应）
- 检查所有CF元素类型
- 验证元素可见性（`is_visible()`）
- 双重确认机制（防止瞬时状态误判）
- 等待页面稳定后再确认通过

### 3. 新增诊断功能

脚本现在会自动记录：
- 检测到的所有CF元素及其可见性
- 当前页面URL和标题
- 页面上的错误信息
- 每30秒生成诊断截图

### 4. 防止Playwright干扰手动操作

新增代码移除webdriver标志，减少CF检测到自动化的可能性。

## 故障排查步骤

### 步骤1: 检查配置

确保 `tasks_config.json` 中包含：

```json
{
  "tasks": {
    "default": {
      "name": "我的服务器",
      "mchost_url": "https://freemchost.com/auth",
      "manual_mode": true,  // 必须启用
      "renew_interval_minutes": 15
    }
  }
}
```

**关键点：** `manual_mode: true` 必须存在，否则会强制headless模式！

### 步骤2: 查看最新日志

```bash
# 查看完整日志
tail -100 tasks/default/task.log

# 实时查看日志
tail -f tasks/default/task.log
```

**重点查找：**
- `⚠️ 检测到 Cloudflare 验证`
- `=== CF状态诊断 ===` - 查看哪些CF元素被检测到
- `等待中...` - 查看等待了多久
- `✓ Cloudflare验证已通过！` - 是否成功通过

### 步骤3: 检查诊断截图

脚本现在会自动生成以下截图：

```bash
ls -lht tasks/default/screenshots/cf_*.png
```

**截图说明：**
- `cf_manual_start_*.png` - 开始手动验证时的状态
- `cf_manual_wait_30_*.png` - 等待30秒时的状态
- `cf_manual_wait_60_*.png` - 等待60秒时的状态
- `cf_manual_solved_*.png` - 验证通过时的状态
- `cf_manual_timeout_*.png` - 验证超时时的状态
- `cf_blocked_*.png` - CF仍然存在时的状态

### 步骤4: 分析诊断信息

查看日志中的 `=== CF状态诊断 ===` 部分：

```
=== CF状态诊断 ===
  CF iframe: 存在 (可见: True)
  CF iframe (通用): 不存在
  CF wrapper: 不存在
  CF verification: 不存在
  CF elements: 存在 (可见: False)
  Turnstile: 存在 (可见: True)
  当前URL: https://freemchost.com/auth
  页面标题: MCHost - Login
===================
```

**分析示例：**

1. **如果显示 "Turnstile: 存在 (可见: True)"**
   - 这是Turnstile类型验证
   - 应该能看到一个复选框
   - 点击复选框后等待3-5秒

2. **如果显示 "CF iframe: 存在 (可见: True)"**
   - 这是iframe挑战
   - 可能需要点击图片或等待5秒盾

3. **如果点击后元素仍显示 "可见: True"**
   - CF验证可能失败了
   - 或者需要更长等待时间
   - 检查VNC中是否有错误提示

### 步骤5: 常见问题和解决方案

#### 问题1: 点击后验证框重新出现

**日志显示：**
```
检测到CF元素已消失，等待页面稳定...
CF元素重新出现，继续等待...
```

**可能原因：**
- Cloudflare检测到自动化工具
- IP被标记为可疑
- 浏览器指纹异常

**解决方案：**
1. 尝试使用Capsolver（付费但更可靠）：
   ```json
   {
     "cf_solver_type": "capsolver",
     "capsolver_api_key": "YOUR_KEY"
   }
   ```

2. 或使用FlareSolverr（免费）：
   ```bash
   ./setup_flaresolverr.sh
   ```
   然后配置：
   ```json
   {
     "cf_solver_type": "flaresolverr",
     "flaresolverr_endpoint": "http://localhost:8191/v1"
   }
   ```

#### 问题2: 验证超时

**日志显示：**
```
❌ Cloudflare验证超时
```

**检查：**
1. VNC是否真的可以访问？
   ```bash
   curl http://localhost:6080
   ```

2. 浏览器窗口是否在VNC中可见？
   ```bash
   # 检查浏览器进程
   ps aux | grep chrome

   # 检查窗口
   DISPLAY=:99 xdotool search --class "Chrome"
   ```

3. 手动测试VNC中的浏览器：
   ```bash
   ./test_vnc_browser.py
   ```

#### 问题3: CF元素检测不到

**日志显示：**
```
=== CF状态诊断 ===
  CF iframe: 不存在
  CF iframe (通用): 不存在
  ...所有都不存在...
```

**可能原因：**
- 不是CF验证问题，而是其他登录问题
- CF已经通过，但页面有其他错误

**检查：**
1. 查看截图 `cf_manual_timeout_*.png`
2. 检查页面URL和标题
3. 查看是否有其他错误信息

## 调试技巧

### 实时VNC监控

1. 使用VNC客户端连接到服务器：
   ```
   服务器IP:6080
   ```

2. 在脚本运行时观察浏览器行为

3. 手动点击CF验证框后，观察页面变化

### 手动测试流程

```bash
# 1. 启动脚本
python3 mchost_renew.py --task-id default

# 2. 在另一个终端实时查看日志
tail -f tasks/default/task.log

# 3. 连接VNC观察
# 浏览器: http://服务器IP:6080/vnc.html

# 4. 当看到CF验证时，手动点击

# 5. 观察日志变化
```

### 生成详细调试日志

如果需要更详细的日志，修改脚本：

```python
# mchost_renew.py 第90行
logger.setLevel(logging.DEBUG)  # 改为DEBUG
```

## 高级解决方案

### 方案1: 使用Capsolver（推荐生产环境）

**优点：**
- 成功率高（~95%）
- 速度快（~5秒）
- 全自动，无需人工干预

**缺点：**
- 需要付费（约$0.002-0.003/次）

**配置：**
```json
{
  "cf_solver_type": "capsolver",
  "capsolver_api_key": "CAP-xxxxx",
  "manual_mode": true  // 作为备份
}
```

### 方案2: 使用FlareSolverr（推荐测试环境）

**优点：**
- 完全免费
- 开源可控

**缺点：**
- 成功率中等（~70%）
- 速度较慢（~15-30秒）
- 可能无法绕过最新CF保护

**配置：**
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

### 方案3: 纯手动模式（当前方案）

**适用于：**
- 测试阶段
- CF验证频率低
- 有人值守的环境

**配置：**
```json
{
  "manual_mode": true,
  "headless": false  // 确保不是headless
}
```

## 成功验证的标志

日志应该显示：

```
⚠️ 检测到 Cloudflare 验证
=== CF状态诊断 ===
  Turnstile: 存在 (可见: True)
  ...
===================
🖥️ 手动干预模式 - 请在VNC界面中完成Cloudflare验证
   访问: http://服务器IP:6080/vnc.html
   提示: 请直接在VNC浏览器窗口中点击CF验证框
等待中... (3/300秒)
等待中... (6/300秒)
...
检测到CF元素已消失，等待页面稳定...
✓ Cloudflare验证已通过！
✓ 成功点击Renew按钮！
```

## 获取帮助

如果以上方法都无法解决问题，请提供：

1. 完整日志（最后100行）：
   ```bash
   tail -100 tasks/default/task.log > cf_debug.log
   ```

2. 诊断截图：
   ```bash
   ls -lt tasks/default/screenshots/cf_*.png | head -5
   ```

3. 配置文件（隐藏敏感信息）：
   ```bash
   cat tasks_config.json
   ```

4. VNC截图（显示CF验证界面）

5. CF诊断信息（从日志中复制）

## 参考文档

- [Cloudflare Solver集成指南](CLOUDFLARE_SOLVER.md)
- [VNC诊断脚本](diagnose_vnc.sh)
- [Capsolver官方文档](https://docs.capsolver.com/)
- [FlareSolverr GitHub](https://github.com/FlareSolverr/FlareSolverr)
