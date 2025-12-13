#!/bin/bash

echo "🌐 启动Chrome（调试模式）"

# 检查Chrome是否已运行
if pgrep -x "Google Chrome" > /dev/null; then
    echo "⚠️  Chrome正在运行，需要先关闭"
    echo -n "是否关闭Chrome并重新启动？ [y/N] "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "正在关闭Chrome..."
        killall "Google Chrome" 2>/dev/null || true
        sleep 2
    else
        echo "❌ 已取消"
        exit 1
    fi
fi

echo "正在启动Chrome（调试模式）..."

# 启动Chrome with debugging port
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  > /dev/null 2>&1 &

sleep 3

# 检查是否成功
if nc -z localhost 9222 2>/dev/null; then
    echo "✅ Chrome已成功启动（调试模式）"
    echo "   端口: 9222"
    echo "   现在可以运行脚本了: ./start.sh"
else
    echo "❌ Chrome启动失败"
    exit 1
fi
