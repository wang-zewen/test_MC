#!/bin/bash

# 安装 systemd 服务脚本

set -e

echo "=========================================="
echo "  安装 MCHost 自动续期服务"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_NAME=$(whoami)

# 检查配置文件
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    echo "错误：找不到 config.json 配置文件！"
    echo "请先运行 deploy.sh 并配置 config.json"
    exit 1
fi

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   SUDO=""
else
   SUDO="sudo"
fi

# 创建服务文件
echo "创建 systemd 服务文件..."
SERVICE_FILE="/tmp/mchost-renew.service"
cp "$SCRIPT_DIR/mchost-renew.service" "$SERVICE_FILE"

# 替换占位符
sed -i "s|%USER%|$USER_NAME|g" "$SERVICE_FILE"
sed -i "s|%SCRIPT_DIR%|$SCRIPT_DIR|g" "$SERVICE_FILE"

# 复制服务文件到系统目录
echo "安装服务文件..."
$SUDO cp "$SERVICE_FILE" /etc/systemd/system/mchost-renew.service
$SUDO chmod 644 /etc/systemd/system/mchost-renew.service

# 重新加载 systemd
echo "重新加载 systemd..."
$SUDO systemctl daemon-reload

# 启用服务
echo "启用服务（开机自启）..."
$SUDO systemctl enable mchost-renew.service

# 启动服务
echo "启动服务..."
$SUDO systemctl start mchost-renew.service

# 等待一下
sleep 2

# 检查服务状态
echo ""
echo -e "${GREEN}=========================================="
echo "  服务安装完成！"
echo "==========================================${NC}"
echo ""
echo "服务状态："
$SUDO systemctl status mchost-renew.service --no-pager || true
echo ""
echo "常用命令："
echo -e "  查看状态: ${YELLOW}sudo systemctl status mchost-renew${NC}"
echo -e "  停止服务: ${YELLOW}sudo systemctl stop mchost-renew${NC}"
echo -e "  启动服务: ${YELLOW}sudo systemctl start mchost-renew${NC}"
echo -e "  重启服务: ${YELLOW}sudo systemctl restart mchost-renew${NC}"
echo -e "  查看日志: ${YELLOW}tail -f /var/log/mchost_renew.log${NC}"
echo -e "  实时日志: ${YELLOW}sudo journalctl -u mchost-renew -f${NC}"
echo ""
