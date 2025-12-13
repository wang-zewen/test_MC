#!/bin/bash

# MCHost Auto-Renew - VNC Remote Desktop Setup
# 用于在Web界面中手动处理Cloudflare验证

set -e

echo "🖥️ 安装VNC远程桌面环境..."

# 检测包管理器
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    UPDATE_CMD="apt-get update"
    INSTALL_CMD="apt-get install -y"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    UPDATE_CMD="yum check-update || true"
    INSTALL_CMD="yum install -y"
else
    echo "❌ 不支持的系统，只支持 apt 或 yum"
    exit 1
fi

echo "📦 更新软件包列表..."
sudo $UPDATE_CMD

echo "📦 安装必要的软件包..."
if [ "$PKG_MANAGER" = "apt-get" ]; then
    sudo $INSTALL_CMD xvfb x11vnc websockify python3-numpy
    # 安装noVNC
    if [ ! -d "/opt/noVNC" ]; then
        echo "📦 安装noVNC..."
        sudo git clone https://github.com/novnc/noVNC.git /opt/noVNC
        sudo git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify
    fi
else
    sudo $INSTALL_CMD xorg-x11-server-Xvfb x11vnc python3-websockify python3-numpy
    if [ ! -d "/opt/noVNC" ]; then
        echo "📦 安装noVNC..."
        sudo git clone https://github.com/novnc/noVNC.git /opt/noVNC
        sudo git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify
    fi
fi

# 创建VNC配置目录
mkdir -p ~/.vnc

# 创建VNC启动脚本
cat > ~/start_vnc.sh << 'EOFVNC'
#!/bin/bash

# 设置显示变量
export DISPLAY=:99

# 检查Xvfb是否已运行
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "启动虚拟显示服务器 Xvfb..."
    Xvfb :99 -screen 0 1920x1080x24 &
    sleep 2
fi

# 检查x11vnc是否已运行
if ! pgrep -x "x11vnc" > /dev/null; then
    echo "启动VNC服务器..."
    x11vnc -display :99 -forever -shared -rfbport 5900 -nopw &
    sleep 2
fi

# 检查noVNC是否已运行
if ! pgrep -f "websockify.*6080" > /dev/null; then
    echo "启动noVNC Web服务..."
    /opt/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080 &
    sleep 2
fi

echo "✅ VNC环境已启动！"
echo "   - VNC端口: 5900"
echo "   - Web访问: http://localhost:6080/vnc.html"
EOFVNC

chmod +x ~/start_vnc.sh

# 创建VNC停止脚本
cat > ~/stop_vnc.sh << 'EOFSTOP'
#!/bin/bash

echo "停止VNC环境..."
pkill -f "websockify.*6080" || true
pkill x11vnc || true
pkill Xvfb || true
echo "✅ VNC环境已停止"
EOFSTOP

chmod +x ~/stop_vnc.sh

# 创建systemd服务文件
sudo tee /etc/systemd/system/mchost-vnc.service > /dev/null << EOFSERVICE
[Unit]
Description=MCHost VNC Remote Desktop Service
After=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=$HOME
ExecStart=$HOME/start_vnc.sh
ExecStop=$HOME/stop_vnc.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSERVICE

echo "🔄 重新加载systemd配置..."
sudo systemctl daemon-reload

echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  启动VNC服务: sudo systemctl start mchost-vnc"
echo "  停止VNC服务: sudo systemctl stop mchost-vnc"
echo "  开机自启:     sudo systemctl enable mchost-vnc"
echo "  查看状态:     sudo systemctl status mchost-vnc"
echo ""
echo "访问方法："
echo "  在浏览器中打开: http://服务器IP:6080/vnc.html"
echo "  或在Web Viewer中点击'远程桌面'按钮"
