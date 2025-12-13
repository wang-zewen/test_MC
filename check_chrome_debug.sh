#!/bin/bash

echo "🔍 检查Chrome调试端口..."

# 检查9222端口是否开放
if nc -z localhost 9222 2>/dev/null; then
    echo "✅ 端口9222已开放"

    # 尝试访问Chrome的调试接口
    if curl -s http://localhost:9222/json > /tmp/chrome_debug.json; then
        echo "✅ Chrome调试接口可访问"
        echo ""
        echo "当前Chrome标签页："
        cat /tmp/chrome_debug.json | python3 -m json.tool | grep -E "title|url" | head -10
        echo ""
        echo "✅ Chrome调试模式正常，脚本应该能连接"
    else
        echo "❌ 无法访问Chrome调试接口"
    fi
else
    echo "❌ 端口9222未开放"
    echo ""
    echo "请先关闭Chrome，然后用以下命令启动："
    echo "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 &"
fi
