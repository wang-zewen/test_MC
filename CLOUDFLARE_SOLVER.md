# Cloudflare 验证解决方案

本项目支持两种自动化Cloudflare验证的方案，帮助您在服务器端自动处理Cloudflare人机验证。

## 方案对比

| 特性 | Capsolver | FlareSolverr |
|------|-----------|--------------|
| **类型** | 商业服务 | 开源工具 |
| **费用** | 付费（按次计费） | 免费 |
| **成功率** | 高（~95%） | 中等（受CF更新影响） |
| **速度** | 快（~5秒） | 较慢（~10-30秒） |
| **维护** | 官方维护 | 社区维护 |
| **推荐场景** | 生产环境 | 测试/个人使用 |

## 方案一：Capsolver（推荐）

### 1. 注册获取API Key

访问 [Capsolver官网](https://www.capsolver.com/) 注册账号并充值。

### 2. 配置脚本

在 `config.json` 或 `tasks_config.json` 中添加：

```json
{
  "cf_solver_type": "capsolver",
  "capsolver_api_key": "YOUR_API_KEY_HERE"
}
```

### 3. 安装依赖

```bash
pip install aiohttp
```

### 4. 运行脚本

脚本会自动检测Cloudflare验证并使用Capsolver解决。

## 方案二：FlareSolverr（免费）

### 1. 安装Docker

FlareSolverr需要Docker环境：

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
```

**CentOS/RHEL:**
```bash
sudo yum install docker
sudo systemctl start docker
```

**Mac:**
```bash
brew install --cask docker
# 然后打开Docker Desktop应用
```

### 2. 部署FlareSolverr

使用提供的一键部署脚本：

```bash
chmod +x setup_flaresolverr.sh
./setup_flaresolverr.sh
```

或手动部署：

```bash
docker run -d \
  --name flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

### 3. 配置脚本

在 `config.json` 或 `tasks_config.json` 中添加：

```json
{
  "cf_solver_type": "flaresolverr",
  "flaresolverr_endpoint": "http://localhost:8191/v1"
}
```

### 4. 运行脚本

脚本会自动使用FlareSolverr解决Cloudflare验证。

## 验证类型支持

### Capsolver支持：
- ✅ Cloudflare Turnstile
- ✅ Cloudflare Challenge (5秒盾)
- ✅ reCAPTCHA v2/v3
- ✅ hCaptcha

### FlareSolverr支持：
- ✅ Cloudflare Challenge (部分)
- ⚠️ Turnstile（效果不稳定）
- ❌ 最新的Cloudflare保护（可能失败）

## 工作原理

### Capsolver工作流程：
1. 脚本检测到Cloudflare验证
2. 提取site_key和页面URL
3. 调用Capsolver API创建任务
4. 轮询获取验证token
5. 将token注入页面完成验证

### FlareSolverr工作流程：
1. 脚本检测到Cloudflare验证
2. 向FlareSolverr发送请求
3. FlareSolverr使用真实浏览器访问页面
4. 等待Cloudflare验证自动通过
5. 返回cookies给脚本使用

## 故障排查

### Capsolver问题

**问题：API Key无效**
```
解决：检查API Key是否正确复制，是否有余额
```

**问题：验证失败**
```
解决：检查网络连接，确保能访问Capsolver API
日志：查看详细错误信息
```

**问题：余额不足**
```
解决：登录Capsolver充值
```

### FlareSolverr问题

**问题：容器无法启动**
```bash
# 查看日志
docker logs flaresolverr

# 常见原因：端口8191被占用
lsof -i :8191
# 解决：修改端口映射
docker run -d --name flaresolverr -p 8192:8191 ...
# 然后更新配置中的端口
```

**问题：验证失败率高**
```
原因：FlareSolverr可能无法绕过最新的Cloudflare保护
解决：
1. 更新到最新版本: docker pull ghcr.io/flaresolverr/flaresolverr:latest
2. 考虑使用Capsolver
3. 启用manual_mode手动验证
```

**问题：连接超时**
```bash
# 检查FlareSolverr是否运行
docker ps | grep flaresolverr

# 检查API是否可访问
curl http://localhost:8191/

# 重启容器
docker restart flaresolverr
```

## 成本估算

### Capsolver定价（参考）
- Turnstile: $0.002/次
- Challenge: $0.003/次
- 假设每天renew 100次，月成本约 $6-9

### FlareSolverr定价
- 完全免费
- 需要自己维护Docker环境

## 最佳实践

### 1. 混合使用
```json
{
  "cf_solver_type": "capsolver",
  "capsolver_api_key": "YOUR_KEY",
  "manual_mode": true
}
```
- 首先尝试Capsolver自动解决
- 失败后回退到手动模式（VNC）

### 2. 日志监控
```bash
# 查看解决成功率
tail -f tasks/default/task.log | grep "Cloudflare"
```

### 3. 定期检查
- Capsolver余额
- FlareSolverr容器状态
- 验证成功率

## 参考链接

- [Capsolver官方文档](https://docs.capsolver.com/)
- [FlareSolverr GitHub](https://github.com/FlareSolverr/FlareSolverr)
- [Cloudflare Turnstile文档](https://developers.cloudflare.com/turnstile/)

## 注意事项

⚠️ **重要提醒：**
1. 自动化验证可能违反某些网站的服务条款
2. 仅用于个人项目和测试目的
3. 不建议用于商业爬虫或违规用途
4. Capsolver需要付费，请合理使用以控制成本
5. FlareSolverr效果可能随Cloudflare更新而下降
