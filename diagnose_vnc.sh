#!/bin/bash
#
# VNC浏览器诊断脚本
# 检查VNC环境和浏览器显示问题
#

echo "========================================="
echo "VNC浏览器诊断工具"
echo "========================================="
echo ""

# 1. 检查VNC服务
echo "1️⃣ 检查VNC服务..."
if pgrep -x "Xvfb" > /dev/null; then
    echo "   ✓ Xvfb运行中"
else
    echo "   ❌ Xvfb未运行"
    echo "   启动命令: Xvfb :99 -screen 0 1920x1080x24 &"
fi

if pgrep -x "x11vnc" > /dev/null; then
    echo "   ✓ x11vnc运行中"
else
    echo "   ❌ x11vnc未运行"
    echo "   启动命令: x11vnc -display :99 -forever -shared &"
fi

if pgrep -x "fluxbox" > /dev/null; then
    echo "   ✓ Fluxbox窗口管理器运行中"
else
    echo "   ❌ Fluxbox未运行"
    echo "   启动命令: DISPLAY=:99 fluxbox &"
fi

echo ""

# 2. 检查DISPLAY环境变量
echo "2️⃣ 检查DISPLAY环境变量..."
if [ -z "$DISPLAY" ]; then
    echo "   ⚠️  当前shell未设置DISPLAY"
    echo "   设置命令: export DISPLAY=:99"
else
    echo "   ✓ DISPLAY=$DISPLAY"
fi

echo ""

# 3. 测试X服务器
echo "3️⃣ 测试X服务器..."
DISPLAY=:99 xdpyinfo > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ X服务器响应正常"
    DISPLAY=:99 xdpyinfo | grep dimensions
else
    echo "   ❌ X服务器无响应"
fi

echo ""

# 4. 检查浏览器进程
echo "4️⃣ 检查浏览器进程..."
if pgrep -f "chromium.*--remote-debugging" > /dev/null; then
    echo "   ✓ Chromium浏览器运行中"
    pgrep -f "chromium" | head -1 | xargs ps -p
elif pgrep -f "chrome.*--remote-debugging" > /dev/null; then
    echo "   ✓ Chrome浏览器运行中"
    pgrep -f "chrome" | head -1 | xargs ps -p
else
    echo "   ⚠️  未检测到浏览器进程"
fi

echo ""

# 5. 测试在VNC上打开窗口
echo "5️⃣ 测试VNC窗口显示..."
echo "   正在VNC上打开测试窗口（xterm）..."
DISPLAY=:99 xterm -e "echo '测试窗口 - 5秒后自动关闭'; sleep 5" 2>/dev/null &
TEST_PID=$!
sleep 1

if ps -p $TEST_PID > /dev/null 2>&1; then
    echo "   ✓ 测试窗口已启动"
    echo "   ℹ️  请在VNC中查看是否能看到xterm窗口"
    echo "   ℹ️  窗口将在5秒后自动关闭"
else
    echo "   ⚠️  xterm可能未安装或启动失败"
fi

echo ""

# 6. 截图测试
echo "6️⃣ VNC截图测试..."
if command -v import > /dev/null 2>&1; then
    DISPLAY=:99 import -window root /tmp/vnc_screenshot.png 2>/dev/null
    if [ -f /tmp/vnc_screenshot.png ]; then
        SIZE=$(stat -c%s /tmp/vnc_screenshot.png 2>/dev/null || stat -f%z /tmp/vnc_screenshot.png)
        echo "   ✓ 截图成功: /tmp/vnc_screenshot.png ($SIZE bytes)"
        echo "   ℹ️  可以下载查看截图内容"
    else
        echo "   ❌ 截图失败"
    fi
else
    echo "   ⚠️  未安装ImageMagick (import命令)"
    echo "   安装: sudo apt-get install imagemagick"
fi

echo ""

# 7. 浏览器窗口检测
echo "7️⃣ 检查浏览器窗口..."
if command -v xdotool > /dev/null 2>&1; then
    DISPLAY=:99 xdotool search --class "chromium" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        WINDOW_COUNT=$(DISPLAY=:99 xdotool search --class "chromium" 2>/dev/null | wc -l)
        echo "   ✓ 检测到 $WINDOW_COUNT 个Chromium窗口"
    else
        DISPLAY=:99 xdotool search --class "Chrome" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            WINDOW_COUNT=$(DISPLAY=:99 xdotool search --class "Chrome" 2>/dev/null | wc -l)
            echo "   ✓ 检测到 $WINDOW_COUNT 个Chrome窗口"
        else
            echo "   ⚠️  未检测到浏览器窗口"
        fi
    fi
else
    echo "   ⚠️  未安装xdotool"
    echo "   安装: sudo apt-get install xdotool"
fi

echo ""
echo "========================================="
echo "诊断完成"
echo "========================================="
echo ""
echo "建议操作："
echo "1. 如果VNC能看到桌面但没有浏览器："
echo "   - 检查浏览器是否真的启动了"
echo "   - 手动测试: DISPLAY=:99 chromium --no-sandbox &"
echo ""
echo "2. 如果浏览器窗口是空白的："
echo "   - 可能是GPU渲染问题"
echo "   - 添加启动参数: --disable-gpu --disable-software-rasterizer"
echo ""
echo "3. 如果网页不加载："
echo "   - 检查网络连接"
echo "   - 查看浏览器控制台错误"
echo ""
