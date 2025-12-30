#!/bin/bash
#
# 测试VNC浏览器显示
#

echo "========================================="
echo "VNC浏览器显示测试"
echo "========================================="
echo ""

# 1. 检查VNC是否运行
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "❌ Xvfb未运行，请先启动VNC"
    exit 1
fi

echo "✓ VNC服务运行中"
echo ""

# 2. 设置DISPLAY
export DISPLAY=:99
echo "设置 DISPLAY=$DISPLAY"
echo ""

# 3. 测试简单窗口
echo "测试1: 启动xterm窗口（10秒后自动关闭）"
echo "       请在VNC中观察是否能看到窗口"
xterm -e "echo '如果你能看到这个窗口，说明VNC显示正常'; echo ''; echo '10秒后自动关闭...'; sleep 10" &
XTERM_PID=$!
echo "       xterm PID: $XTERM_PID"
echo ""
sleep 2

# 4. 测试浏览器启动
echo "测试2: 启动Chromium浏览器（访问example.com）"
echo "       请在VNC中观察浏览器窗口"
echo ""

# 使用VNC优化的参数启动浏览器
chromium --no-sandbox \
         --disable-gpu \
         --disable-software-rasterizer \
         --disable-gl-drawing-for-tests \
         --disable-accelerated-2d-canvas \
         --window-size=1280,720 \
         --start-maximized \
         --app=http://example.com \
         > /tmp/chromium_test.log 2>&1 &

BROWSER_PID=$!
echo "       Chromium PID: $BROWSER_PID"
echo "       日志文件: /tmp/chromium_test.log"
echo ""

# 5. 等待并检查浏览器
sleep 3
if ps -p $BROWSER_PID > /dev/null; then
    echo "✓ 浏览器进程运行中"
    echo ""
    echo "请在VNC中检查:"
    echo "1. 是否能看到浏览器窗口？"
    echo "2. 窗口是否显示内容？"
    echo "3. 能否看到example.com网页？"
    echo ""
    echo "浏览器将保持运行，按Ctrl+C停止测试"
    echo ""
    
    # 保持运行30秒
    for i in {1..30}; do
        if ! ps -p $BROWSER_PID > /dev/null; then
            echo "⚠️  浏览器进程已停止"
            echo "查看日志: cat /tmp/chromium_test.log"
            exit 1
        fi
        sleep 1
    done
    
    echo ""
    echo "测试完成，正在关闭浏览器..."
    kill $BROWSER_PID 2>/dev/null
    
else
    echo "❌ 浏览器启动失败"
    echo ""
    echo "查看错误日志:"
    cat /tmp/chromium_test.log
    exit 1
fi

echo ""
echo "========================================="
echo "测试结束"
echo "========================================="
