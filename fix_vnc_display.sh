#!/bin/bash
#
# 修复VNC浏览器显示问题
#

echo "========================================="
echo "VNC浏览器显示修复工具"
echo "========================================="
echo ""

# 1. 安装必要工具
echo "1️⃣ 安装诊断工具..."
if ! command -v xdotool > /dev/null; then
    echo "   安装xdotool..."
    sudo apt-get update > /dev/null 2>&1
    sudo apt-get install -y xdotool > /dev/null 2>&1
    echo "   ✓ xdotool已安装"
else
    echo "   ✓ xdotool已存在"
fi

if ! command -v import > /dev/null; then
    echo "   安装ImageMagick..."
    sudo apt-get install -y imagemagick > /dev/null 2>&1
    echo "   ✓ ImageMagick已安装"
else
    echo "   ✓ ImageMagick已存在"
fi

echo ""

# 2. 确保VNC服务运行
echo "2️⃣ 检查VNC服务..."
export DISPLAY=:99

if ! pgrep -x "Xvfb" > /dev/null; then
    echo "   启动Xvfb..."
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    sleep 2
fi

if ! pgrep -x "x11vnc" > /dev/null; then
    echo "   启动x11vnc..."
    x11vnc -display :99 -forever -shared -rfbport 5900 > /dev/null 2>&1 &
    sleep 1
fi

if ! pgrep -x "fluxbox" > /dev/null; then
    echo "   启动Fluxbox..."
    DISPLAY=:99 fluxbox > /dev/null 2>&1 &
    sleep 1
fi

echo "   ✓ VNC服务已就绪"
echo ""

# 3. 检查现有浏览器窗口
echo "3️⃣ 检查现有浏览器窗口..."
WINDOWS=$(DISPLAY=:99 xdotool search --class "chromium|Chrome" 2>/dev/null)
if [ -n "$WINDOWS" ]; then
    echo "   发现 $(echo "$WINDOWS" | wc -l) 个浏览器窗口"
    echo "   窗口ID: $WINDOWS"
    echo ""
    echo "   这些窗口可能隐藏或最小化了"
    echo "   尝试显示所有窗口..."
    
    for win in $WINDOWS; do
        DISPLAY=:99 xdotool windowactivate $win 2>/dev/null
        DISPLAY=:99 xdotool windowraise $win 2>/dev/null
    done
    
    echo "   ✓ 已尝试激活所有窗口"
else
    echo "   未发现浏览器窗口"
    echo "   可能浏览器未启动或启动失败"
fi

echo ""

# 4. 截图验证
echo "4️⃣ 生成VNC截图..."
DISPLAY=:99 import -window root /tmp/vnc_current.png 2>/dev/null
if [ -f /tmp/vnc_current.png ]; then
    SIZE=$(stat -c%s /tmp/vnc_current.png)
    echo "   ✓ 截图已保存: /tmp/vnc_current.png ($SIZE bytes)"
    echo "   请下载查看当前VNC显示内容"
else
    echo "   ❌ 截图失败"
fi

echo ""

# 5. 列出所有窗口
echo "5️⃣ VNC上的所有窗口:"
DISPLAY=:99 xdotool search --name "." 2>/dev/null | while read win; do
    title=$(DISPLAY=:99 xdotool getwindowname $win 2>/dev/null)
    echo "   窗口ID: $win - 标题: $title"
done

echo ""
echo "========================================="
echo "修复完成"
echo "========================================="
echo ""
echo "下一步操作："
echo "1. 下载截图查看: scp user@server:/tmp/vnc_current.png ."
echo "2. 如果截图中没有浏览器，运行测试脚本:"
echo "   ./test_vnc_browser.sh"
echo "3. 在VNC中观察测试结果"
echo ""
