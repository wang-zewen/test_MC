#!/bin/bash

# 在VNC桌面上启动Chromium浏览器（用于测试）

export DISPLAY=:99

echo "在VNC桌面上启动Chromium浏览器..."

# 尝试启动Chromium
if command -v chromium &> /dev/null; then
    chromium --no-sandbox --disable-setuid-sandbox &
elif command -v chromium-browser &> /dev/null; then
    chromium-browser --no-sandbox --disable-setuid-sandbox &
elif command -v google-chrome &> /dev/null; then
    google-chrome --no-sandbox --disable-setuid-sandbox &
else
    echo "错误：未找到Chromium或Chrome浏览器"
    echo "请先安装Playwright（它会自动下载Chromium）："
    echo "  pip install playwright"
    echo "  playwright install chromium"
    exit 1
fi

echo "✓ 浏览器已启动，请在VNC界面中查看"
echo "  访问: http://服务器IP:6080/vnc.html"
