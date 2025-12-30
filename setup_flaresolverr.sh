#!/bin/bash
#
# FlareSolverr Docker 部署脚本
# 用于自动解决Cloudflare验证
#

set -e

echo "========================================="
echo "FlareSolverr Docker 部署"
echo "========================================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    echo ""
    echo "请先安装Docker："
    echo "  Ubuntu/Debian: sudo apt-get install docker.io"
    echo "  CentOS/RHEL:   sudo yum install docker"
    echo "  Mac:           brew install --cask docker"
    echo ""
    exit 1
fi

echo "✓ Docker已安装"

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker服务未运行"
    echo ""
    echo "请启动Docker："
    echo "  Linux: sudo systemctl start docker"
    echo "  Mac:   打开Docker Desktop应用"
    echo ""
    exit 1
fi

echo "✓ Docker服务运行中"
echo ""

# 停止并删除旧容器（如果存在）
if docker ps -a | grep -q flaresolverr; then
    echo "🗑️  停止并删除旧的FlareSolverr容器..."
    docker stop flaresolverr 2>/dev/null || true
    docker rm flaresolverr 2>/dev/null || true
fi

# 拉取最新镜像
echo "📥 拉取FlareSolverr镜像..."
docker pull ghcr.io/flaresolverr/flaresolverr:latest

# 启动容器
echo "🚀 启动FlareSolverr容器..."
docker run -d \
  --name flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest

# 等待服务启动
echo ""
echo "⏳ 等待FlareSolverr启动..."
sleep 5

# 检查服务是否运行
if curl -s http://localhost:8191/ > /dev/null 2>&1; then
    echo ""
    echo "========================================="
    echo "✅ FlareSolverr部署成功！"
    echo "========================================="
    echo ""
    echo "服务信息："
    echo "  - 端口: 8191"
    echo "  - API地址: http://localhost:8191/v1"
    echo "  - 容器名: flaresolverr"
    echo ""
    echo "管理命令："
    echo "  查看日志: docker logs -f flaresolverr"
    echo "  停止服务: docker stop flaresolverr"
    echo "  启动服务: docker start flaresolverr"
    echo "  重启服务: docker restart flaresolverr"
    echo "  删除服务: docker stop flaresolverr && docker rm flaresolverr"
    echo ""
    echo "配置脚本："
    echo "  在 config.json 中添加:"
    echo '  "cf_solver_type": "flaresolverr",'
    echo '  "flaresolverr_endpoint": "http://localhost:8191/v1"'
    echo ""
else
    echo ""
    echo "❌ FlareSolverr启动失败"
    echo ""
    echo "请检查日志："
    echo "  docker logs flaresolverr"
    echo ""
    exit 1
fi
