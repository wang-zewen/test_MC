#!/bin/bash

# 快速修复VNC黑屏问题 - 添加窗口管理器

echo "🔧 修复VNC黑屏问题..."

# 检测包管理器
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    echo "📦 安装Fluxbox窗口管理器和字体..."
    sudo apt-get install -y fluxbox xterm fonts-dejavu fonts-liberation
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    echo "📦 安装Fluxbox窗口管理器和字体..."
    sudo yum install -y fluxbox xterm dejavu-sans-fonts liberation-fonts
else
    echo "❌ 不支持的系统"
    exit 1
fi

# 停止现有VNC服务
echo "⏹️ 停止现有VNC服务..."
sudo systemctl stop mchost-vnc || true
sleep 2

# 清理现有进程
pkill -f "websockify.*6080" || true
pkill x11vnc || true
pkill fluxbox || true
pkill Xvfb || true
sleep 1

# 更新启动脚本
echo "📝 更新VNC启动脚本..."
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

# 检查窗口管理器是否已运行
if ! pgrep -x "fluxbox" > /dev/null; then
    echo "启动窗口管理器 Fluxbox..."
    fluxbox -display :99 &
    sleep 1
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
echo "   - 桌面环境: Fluxbox"
EOFVNC

chmod +x ~/start_vnc.sh

# 更新停止脚本
echo "📝 更新VNC停止脚本..."
cat > ~/stop_vnc.sh << 'EOFSTOP'
#!/bin/bash

echo "停止VNC环境..."
pkill -f "websockify.*6080" || true
pkill x11vnc || true
pkill fluxbox || true
pkill Xvfb || true
echo "✅ VNC环境已停止"
EOFSTOP

chmod +x ~/stop_vnc.sh

# 重新启动VNC服务
echo "🚀 重新启动VNC服务..."
sudo systemctl start mchost-vnc
sleep 3

# 检查状态
echo ""
echo "检查服务状态："
sudo systemctl status mchost-vnc --no-pager -l

echo ""
echo "✅ 修复完成！"
echo "现在可以访问 http://服务器IP:6080/vnc.html"
echo "你应该能看到Fluxbox灰色桌面而不是黑屏"
echo ""
echo "右键单击桌面可以打开Fluxbox菜单"
