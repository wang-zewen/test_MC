#!/bin/bash

# 安装 Google Chrome 浏览器（用于绕过Cloudflare检测）

echo "🌐 安装 Google Chrome 浏览器..."

# 检测包管理器
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    echo "检测到 apt 包管理器"

    # 下载Chrome的GPG密钥
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

    # 添加Chrome仓库
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

    # 更新并安装
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable

elif command -v yum &> /dev/null; then
    # RedHat/CentOS
    echo "检测到 yum 包管理器"

    # 添加Chrome仓库
    sudo tee /etc/yum.repos.d/google-chrome.repo > /dev/null << 'EOF'
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/$basearch
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF

    # 安装
    sudo yum install -y google-chrome-stable

else
    echo "❌ 不支持的系统，只支持 apt 或 yum"
    exit 1
fi

# 验证安装
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome 安装成功！"
    google-chrome --version
else
    echo "❌ Chrome 安装失败"
    exit 1
fi

echo ""
echo "现在Playwright可以使用真正的Chrome浏览器来绕过Cloudflare检测"
echo "重启任务以使用Chrome浏览器"
