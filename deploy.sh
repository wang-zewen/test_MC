#!/bin/bash

# MCHost Auto Renew - 一键部署脚本
# 适用于 Ubuntu/Debian VPS

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  MCHost 自动续期脚本 - 一键部署"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}[1/7]${NC} 检查系统环境..."

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   SUDO=""
else
   SUDO="sudo"
fi

# 更新包列表
echo -e "${GREEN}[2/7]${NC} 更新系统包列表..."
$SUDO apt-get update -qq

# 安装Python3和pip
echo -e "${GREEN}[3/7]${NC} 安装 Python3 和依赖..."
$SUDO apt-get install -y python3 python3-pip python3-venv

# 安装Playwright依赖的系统库
echo -e "${GREEN}[4/7]${NC} 安装 Playwright 系统依赖..."
$SUDO apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

# 创建Python虚拟环境
echo -e "${GREEN}[5/7]${NC} 创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo -e "${GREEN}[6/7]${NC} 安装 Python 依赖包..."
source venv/bin/activate
pip install --upgrade pip
pip install playwright

# 安装Playwright浏览器
echo "安装 Chromium 浏览器（可能需要几分钟）..."
playwright install chromium
playwright install-deps chromium

# 创建配置文件
echo -e "${GREEN}[7/7]${NC} 配置文件设置..."
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}创建配置文件...${NC}"
    cp config.json.example config.json
    echo -e "${RED}重要：请编辑 config.json 文件，填入您的 MCHost 账号信息！${NC}"
    echo -e "使用命令: ${YELLOW}nano $SCRIPT_DIR/config.json${NC}"
else
    echo -e "${GREEN}配置文件已存在${NC}"
fi

# 创建日志目录
$SUDO mkdir -p /var/log
$SUDO touch /var/log/mchost_renew.log
$SUDO chmod 666 /var/log/mchost_renew.log

# 设置脚本可执行权限
chmod +x mchost_renew.py

echo ""
echo -e "${GREEN}=========================================="
echo "  部署完成！"
echo "==========================================${NC}"
echo ""
echo "下一步操作："
echo ""
echo -e "1. 编辑配置文件（${YELLOW}必须${NC}）："
echo -e "   ${YELLOW}nano $SCRIPT_DIR/config.json${NC}"
echo ""
echo "   需要填写："
echo "   - mchost_url: 你的MCHost登录页面URL"
echo "   - username: 你的用户名"
echo "   - password: 你的密码"
echo ""
echo "2. 测试运行脚本："
echo -e "   ${YELLOW}$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/mchost_renew.py${NC}"
echo ""
echo "3. 设置开机自启（可选）："
echo -e "   ${YELLOW}bash $SCRIPT_DIR/install_service.sh${NC}"
echo ""
echo "4. 查看日志："
echo -e "   ${YELLOW}tail -f /var/log/mchost_renew.log${NC}"
echo ""
echo -e "${GREEN}提示：${NC}首次运行建议先测试，确保登录成功后再设置为服务"
echo ""
