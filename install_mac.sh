#!/bin/bash

# MCHost Auto-Renew - Mac 一键安装脚本

set -e

echo "🍎 MCHost 自动续期脚本 - Mac 一键安装"
echo "================================================"

# 检测是否在Mac上
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本仅支持 macOS 系统"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "📦 步骤 1/5: 检查 Python3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装："
    echo "   brew install python3"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✅ 找到 $PYTHON_VERSION"

echo ""
echo "📦 步骤 2/5: 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

echo ""
echo "📦 步骤 3/5: 安装依赖..."
source venv/bin/activate
pip install --upgrade pip > /dev/null
pip install playwright flask
echo "✅ Python 依赖安装完成"

echo ""
echo "📦 步骤 4/5: 安装浏览器..."
playwright install chromium
playwright install chrome
echo "✅ 浏览器安装完成"

echo ""
echo "📦 步骤 5/5: 创建配置文件..."

# 创建配置文件
if [ ! -f "tasks_config.json" ]; then
    cat > tasks_config.json << 'EOF'
{
  "tasks": {
    "default": {
      "name": "我的MCHost服务器",
      "mchost_url": "https://freemchost.com/server?id=你的服务器ID",
      "renew_interval_minutes": 15,
      "enabled": true,
      "manual_mode": false,
      "created_at": "2025-12-13T00:00:00Z"
    }
  }
}
EOF
    echo "✅ 配置文件已创建: tasks_config.json"
    echo "   ⚠️  请编辑此文件，修改服务器ID"
else
    echo "✅ 配置文件已存在: tasks_config.json"
fi

# 创建任务目录
mkdir -p tasks/default
echo "✅ 任务目录已创建: tasks/default"

# 创建快速启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 mchost_renew.py --task-id default
EOF
chmod +x start.sh
echo "✅ 启动脚本已创建: start.sh"

# 创建后台运行脚本
cat > start_background.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
nohup python3 mchost_renew.py --task-id default > mchost.log 2>&1 &
echo "✅ 已在后台启动"
echo "查看日志: tail -f mchost.log"
echo "停止任务: pkill -f mchost_renew.py"
EOF
chmod +x start_background.sh
echo "✅ 后台运行脚本已创建: start_background.sh"

echo ""
echo "================================================"
echo "✅ 安装完成！"
echo ""
echo "📋 后续步骤："
echo ""
echo "1. 导出 cookies："
echo "   - 在浏览器中登录 https://freemchost.com"
echo "   - 使用浏览器插件导出 cookies (Cookie-Editor 等)"
echo "   - 保存为 JSON 格式到: tasks/default/cookies.json"
echo ""
echo "2. 编辑配置文件："
echo "   nano tasks_config.json"
echo "   修改 mchost_url 中的服务器ID"
echo ""
echo "3. 启动方式："
echo "   前台运行(测试): ./start.sh"
echo "   后台运行:       ./start_background.sh"
echo ""
echo "4. Web 管理界面(可选)："
echo "   python3 web_viewer.py"
echo "   访问: http://localhost:5001"
echo ""
echo "================================================"
