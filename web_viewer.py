#!/usr/bin/env python3
"""
MCHost Renew Web Viewer
Web界面查看Renew截图和日志
"""

from flask import Flask, render_template_string, send_file, jsonify, request, redirect
import os
from pathlib import Path
from datetime import datetime
import glob

app = Flask(__name__)

# 配置
SCREENSHOTS_DIR = Path(__file__).parent / 'screenshots'
LOG_FILE = '/var/log/mchost_renew.log'
SECRET_KEY = os.environ.get('VIEWER_PASSWORD', 'mchost123')  # 默认密码，可通过环境变量修改

# 确保截图目录存在
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# 简单的密码保护
def check_auth():
    """检查是否已认证"""
    password = request.cookies.get('auth_token')
    return password == SECRET_KEY

def login_required(f):
    """登录装饰器"""
    def decorated_function(*args, **kwargs):
        if not check_auth():
            return redirect('/login')
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# HTML 模板
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - MCHost Renew Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 90%;
            max-width: 400px;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #666;
        }
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #5568d3;
        }
        .error {
            color: #e74c3c;
            margin-bottom: 15px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 MCHost Viewer</h1>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>密码</label>
                <input type="password" name="password" placeholder="输入访问密码" required autofocus>
            </div>
            <button type="submit">登录</button>
        </form>
    </div>
</body>
</html>
"""

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCHost Renew Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            font-size: 28px;
            margin-bottom: 5px;
        }
        .subtitle {
            opacity: 0.9;
            font-size: 14px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .stat-label {
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .section-title {
            font-size: 20px;
            margin-bottom: 15px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .screenshots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .screenshot-item {
            border: 2px solid #eee;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .screenshot-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .screenshot-item img {
            width: 100%;
            display: block;
            cursor: pointer;
        }
        .screenshot-info {
            padding: 10px;
            background: #f9f9f9;
            font-size: 12px;
            color: #666;
        }
        .log-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.6;
            max-height: 500px;
            overflow-y: auto;
        }
        .log-line {
            margin-bottom: 2px;
        }
        .log-line.error { color: #f48771; }
        .log-line.warning { color: #dcdcaa; }
        .log-line.success { color: #4ec9b0; }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 15px;
            transition: background 0.3s;
        }
        .refresh-btn:hover {
            background: #5568d3;
        }
        .logout-btn {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            float: right;
        }
        .logout-btn:hover {
            background: #c0392b;
        }
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        /* Lightbox */
        .lightbox {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .lightbox.active {
            display: flex;
        }
        .lightbox img {
            max-width: 90%;
            max-height: 90%;
            border-radius: 5px;
        }
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 30px;
            color: white;
            font-size: 40px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🖥️ MCHost Auto Renew Viewer</h1>
            <p class="subtitle">实时监控自动续期状态</p>
            <a href="/logout" class="logout-btn">登出</a>
        </div>
    </div>

    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">截图总数</div>
                <div class="stat-value">{{ screenshot_count }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">最后更新</div>
                <div class="stat-value" style="font-size: 16px;">{{ last_update }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">运行状态</div>
                <div class="stat-value" style="font-size: 18px; color: #27ae60;">● 运行中</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">
                📸 最近的Renew截图
                <button class="refresh-btn" onclick="location.reload()">🔄 刷新</button>
            </div>
            {% if screenshots %}
            <div class="screenshots-grid">
                {% for screenshot in screenshots %}
                <div class="screenshot-item">
                    <img src="/screenshot/{{ screenshot.filename }}" alt="Screenshot" onclick="openLightbox(this.src)">
                    <div class="screenshot-info">
                        📅 {{ screenshot.time }}<br>
                        📦 {{ screenshot.size }}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="no-data">
                <p>暂无截图数据</p>
            </div>
            {% endif %}
        </div>

        <div class="section">
            <div class="section-title">
                📋 最近日志 (最后100行)
            </div>
            <div class="log-container" id="logContainer">
                {% for line in log_lines %}
                <div class="log-line {{ line.type }}">{{ line.text }}</div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <span class="lightbox-close">&times;</span>
        <img id="lightbox-img" src="" alt="">
    </div>

    <script>
        function openLightbox(src) {
            document.getElementById('lightbox').classList.add('active');
            document.getElementById('lightbox-img').src = src;
        }
        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('active');
        }
        // 自动滚动日志到底部
        const logContainer = document.getElementById('logContainer');
        logContainer.scrollTop = logContainer.scrollHeight;

        // 每30秒自动刷新
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == SECRET_KEY:
            resp = redirect('/')
            resp.set_cookie('auth_token', SECRET_KEY, max_age=86400*7)  # 7天
            return resp
        else:
            return render_template_string(LOGIN_TEMPLATE, error='密码错误')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """登出"""
    resp = redirect('/login')
    resp.set_cookie('auth_token', '', max_age=0)
    return resp

@app.route('/')
@login_required
def index():
    """主页"""
    # 获取截图列表
    screenshots = []
    screenshot_files = sorted(SCREENSHOTS_DIR.glob('renew_*.png'), key=os.path.getmtime, reverse=True)

    for screenshot_file in screenshot_files[:20]:  # 只显示最近20张
        stat = screenshot_file.stat()
        screenshots.append({
            'filename': screenshot_file.name,
            'time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'size': f'{stat.st_size / 1024:.1f} KB'
        })

    # 读取日志
    log_lines = []
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-100:]  # 最后100行
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 根据内容判断类型
                line_type = ''
                if 'ERROR' in line or '错误' in line or '失败' in line:
                    line_type = 'error'
                elif 'WARNING' in line or '警告' in line:
                    line_type = 'warning'
                elif '成功' in line or 'SUCCESS' in line or '✓' in line:
                    line_type = 'success'

                log_lines.append({
                    'text': line,
                    'type': line_type
                })
    except FileNotFoundError:
        log_lines.append({
            'text': '日志文件不存在',
            'type': 'warning'
        })

    # 最后更新时间
    last_update = datetime.now().strftime('%H:%M:%S')

    return render_template_string(
        MAIN_TEMPLATE,
        screenshots=screenshots,
        screenshot_count=len(screenshot_files),
        log_lines=log_lines,
        last_update=last_update
    )

@app.route('/screenshot/<filename>')
@login_required
def get_screenshot(filename):
    """获取截图文件"""
    screenshot_path = SCREENSHOTS_DIR / filename
    if screenshot_path.exists():
        return send_file(screenshot_path, mimetype='image/png')
    return '文件不存在', 404

@app.route('/api/stats')
@login_required
def api_stats():
    """API: 获取统计信息"""
    screenshot_files = list(SCREENSHOTS_DIR.glob('renew_*.png'))
    return jsonify({
        'screenshot_count': len(screenshot_files),
        'last_update': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("MCHost Renew Web Viewer 启动")
    print("=" * 60)
    print(f"访问地址: http://0.0.0.0:5000")
    print(f"默认密码: {SECRET_KEY}")
    print("提示: 可通过环境变量 VIEWER_PASSWORD 修改密码")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
