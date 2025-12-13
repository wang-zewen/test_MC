#!/bin/bash

echo "=== VNC诊断工具 ==="
echo ""

echo "1. 检查VNC相关进程："
echo "   Xvfb (虚拟显示):"
pgrep -a Xvfb || echo "     ❌ 未运行"

echo "   Fluxbox (窗口管理器):"
pgrep -a fluxbox || echo "     ❌ 未运行"

echo "   x11vnc (VNC服务器):"
pgrep -a x11vnc || echo "     ❌ 未运行"

echo "   noVNC (Web界面):"
pgrep -a -f "websockify.*6080" || echo "     ❌ 未运行"

echo ""
echo "2. 检查端口监听："
echo "   5900 (VNC):"
netstat -tlnp 2>/dev/null | grep 5900 || echo "     ❌ 未监听"

echo "   6080 (noVNC Web):"
netstat -tlnp 2>/dev/null | grep 6080 || echo "     ❌ 未监听"

echo ""
echo "3. 检查DISPLAY :99 是否可用："
export DISPLAY=:99
if xdpyinfo -display :99 >/dev/null 2>&1; then
    echo "   ✅ DISPLAY :99 可用"
    xdpyinfo -display :99 | grep dimensions
else
    echo "   ❌ DISPLAY :99 不可用"
fi

echo ""
echo "4. 检查浏览器进程："
pgrep -a chromium || pgrep -a chrome || echo "   ❌ 未找到浏览器进程"

echo ""
echo "5. 检查MCHost任务进程："
pgrep -a -f "mchost_renew.py" || echo "   ❌ 未找到任务进程"

echo ""
echo "6. systemd服务状态："
systemctl is-active mchost-vnc 2>/dev/null || echo "   服务未运行"

echo ""
echo "=== 建议 ==="

if ! pgrep Xvfb > /dev/null; then
    echo "❌ VNC环境未运行！"
    echo "   运行: sudo systemctl start mchost-vnc"
    echo "   或者: bash ~/start_vnc.sh"
fi

if ! pgrep chromium > /dev/null && ! pgrep chrome > /dev/null; then
    echo "❌ 浏览器未运行！"
    echo "   确保任务已启用manual_mode并重启"
    echo "   或手动测试: bash open_browser_vnc.sh"
fi

echo ""
echo "=== 快速修复 ==="
echo "如果VNC环境有问题，运行："
echo "  sudo systemctl restart mchost-vnc"
echo "  # 或"
echo "  bash ~/start_vnc.sh"
