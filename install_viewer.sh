#!/bin/bash

# 安装 Web Viewer systemd 服务脚本

set -e

echo "=========================================="
echo "  安装 MCHost Web Viewer 服务"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_NAME=$(whoami)

# 检查web_viewer.py是否存在
if [ ! -f "$SCRIPT_DIR/web_viewer.py" ]; then
    echo "错误：找不到 web_viewer.py 文件！"
    exit 1
fi

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   SUDO=""
else
   SUDO="sudo"
fi

# 询问密码（可选）
echo -e "${YELLOW}设置 Web Viewer 访问密码（直接回车使用默认密码 mchost123）:${NC}"
read -s -p "密码: " VIEWER_PASSWORD
echo ""

if [ -z "$VIEWER_PASSWORD" ]; then
    VIEWER_PASSWORD="mchost123"
    echo "使用默认密码: mchost123"
fi

# 创建服务文件
echo "创建 systemd 服务文件..."
SERVICE_FILE="/tmp/mchost-viewer.service"
cp "$SCRIPT_DIR/mchost-viewer.service" "$SERVICE_FILE"

# 替换占位符
sed -i "s|%USER%|$USER_NAME|g" "$SERVICE_FILE"
sed -i "s|%SCRIPT_DIR%|$SCRIPT_DIR|g" "$SERVICE_FILE"
sed -i "s|Environment=\"VIEWER_PASSWORD=mchost123\"|Environment=\"VIEWER_PASSWORD=$VIEWER_PASSWORD\"|g" "$SERVICE_FILE"

# 复制服务文件到系统目录
echo "安装服务文件..."
$SUDO cp "$SERVICE_FILE" /etc/systemd/system/mchost-viewer.service
$SUDO chmod 644 /etc/systemd/system/mchost-viewer.service

# 重新加载 systemd
echo "重新加载 systemd..."
$SUDO systemctl daemon-reload

# 启用服务
echo "启用服务（开机自启）..."
$SUDO systemctl enable mchost-viewer.service

# 启动服务
echo "启动服务..."
$SUDO systemctl start mchost-viewer.service

# 等待一下
sleep 2

# 获取服务器IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# 检查服务状态
echo ""
echo -e "${GREEN}=========================================="
echo "  Web Viewer 服务安装完成！"
echo "==========================================${NC}"
echo ""
echo "服务状态："
$SUDO systemctl status mchost-viewer.service --no-pager || true
echo ""
echo -e "${GREEN}访问地址: ${YELLOW}http://$SERVER_IP:5000${NC}"
echo -e "${GREEN}登录密码: ${YELLOW}$VIEWER_PASSWORD${NC}"
echo ""
echo "常用命令："
echo -e "  查看状态: ${YELLOW}sudo systemctl status mchost-viewer${NC}"
echo -e "  停止服务: ${YELLOW}sudo systemctl stop mchost-viewer${NC}"
echo -e "  启动服务: ${YELLOW}sudo systemctl start mchost-viewer${NC}"
echo -e "  重启服务: ${YELLOW}sudo systemctl restart mchost-viewer${NC}"
echo -e "  查看日志: ${YELLOW}sudo journalctl -u mchost-viewer -f${NC}"
echo ""
echo -e "${YELLOW}提示：${NC}如需修改密码，编辑 /etc/systemd/system/mchost-viewer.service"
echo "      修改 Environment=\"VIEWER_PASSWORD=...\" 这一行，然后执行："
echo "      sudo systemctl daemon-reload && sudo systemctl restart mchost-viewer"
echo ""
