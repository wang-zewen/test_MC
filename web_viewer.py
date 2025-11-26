#!/usr/bin/env python3
"""
MCHost Multi-Task Web Viewer
多任务管理 Web 界面
"""

import os
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_file
from werkzeug.utils import secure_filename
import sys

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from task_manager import TaskManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mchost-secret-key-change-me')

# 配置
BASE_DIR = Path(__file__).parent
PASSWORD = os.environ.get('VIEWER_PASSWORD', 'mchost123')

# 初始化任务管理器
task_manager = TaskManager()


def require_auth(f):
    """认证装饰器"""
    def wrapper(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


# ==================== HTML 模板 ====================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - MCHost 任务管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            width: 90%;
            max-width: 400px;
        }
        h1 { color: #333; margin-bottom: 30px; text-align: center; }
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { opacity: 0.9; }
        .error {
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 MCHost 任务管理</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="请输入密码" required autofocus>
            <button type="submit">登录</button>
        </form>
    </div>
</body>
</html>
'''

TASK_LIST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>任务列表 - MCHost 管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { font-size: 24px; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
        }
        .btn-primary {
            background: white;
            color: #667eea;
        }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-warning { background: #ffc107; color: #333; }
        .btn-info { background: #17a2b8; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn:hover { opacity: 0.9; }
        .btn-sm { padding: 5px 10px; font-size: 12px; margin: 0 2px; }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .task-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .task-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        .task-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .task-id {
            font-size: 12px;
            color: #999;
        }
        .status-badge {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        .status-stopped {
            background: #f8d7da;
            color: #721c24;
        }
        .task-info {
            margin: 10px 0;
            font-size: 14px;
            color: #666;
        }
        .task-info div {
            margin: 5px 0;
        }
        .task-actions {
            margin-top: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 10px;
        }
        .empty-state h2 {
            color: #999;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 MCHost 任务管理</h1>
            <div>
                <a href="{{ url_for('add_task') }}" class="btn btn-primary">➕ 新建任务</a>
                <a href="{{ url_for('logout') }}" class="btn btn-secondary">退出</a>
            </div>
        </div>

        {% if tasks|length == 0 %}
        <div class="empty-state">
            <h2>还没有任务</h2>
            <p style="color: #999; margin-bottom: 20px;">点击上方"新建任务"按钮开始</p>
            <a href="{{ url_for('add_task') }}" class="btn btn-primary">➕ 新建第一个任务</a>
        </div>
        {% else %}
        <div class="task-grid">
            {% for task in tasks %}
            <div class="task-card">
                <div class="task-header">
                    <div>
                        <div class="task-title">{{ task.name }}</div>
                        <div class="task-id">ID: {{ task.task_id }}</div>
                    </div>
                    <span class="status-badge status-{{ 'running' if task.running else 'stopped' }}">
                        {{ '🟢 运行中' if task.running else '🔴 已停止' }}
                    </span>
                </div>
                <div class="task-info">
                    <div>⏱️ 间隔: {{ task.renew_interval_minutes }} 分钟</div>
                    <div>🔗 URL: {{ task.mchost_url[:30] }}...</div>
                    {% if task.last_run %}
                    <div>🕐 最后运行: {{ task.last_run[:19] }}</div>
                    {% endif %}
                </div>
                <div class="task-actions">
                    <a href="{{ url_for('task_detail', task_id=task.task_id) }}" class="btn btn-info btn-sm">📊 详情</a>
                    <a href="{{ url_for('edit_task', task_id=task.task_id) }}" class="btn btn-warning btn-sm">✏️ 编辑</a>
                    {% if task.running %}
                    <a href="{{ url_for('stop_task', task_id=task.task_id) }}" class="btn btn-danger btn-sm" onclick="return confirm('确定停止任务？')">⏹️ 停止</a>
                    <a href="{{ url_for('restart_task', task_id=task.task_id) }}" class="btn btn-secondary btn-sm">🔄 重启</a>
                    {% else %}
                    <a href="{{ url_for('start_task', task_id=task.task_id) }}" class="btn btn-success btn-sm">▶️ 启动</a>
                    {% endif %}
                    <a href="{{ url_for('delete_task', task_id=task.task_id) }}" class="btn btn-danger btn-sm" onclick="return confirm('确定删除任务？此操作不可恢复！')">🗑️ 删除</a>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <script>
        // Auto refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''

TASK_DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>任务详情 - {{ task.name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { font-size: 24px; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
            margin: 0 5px;
        }
        .btn-primary { background: white; color: #667eea; }
        .btn:hover { opacity: 0.9; }
        .container { max-width: 1200px; margin: 0 auto; }
        .section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }
        .screenshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }
        .screenshot-item {
            cursor: pointer;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .screenshot-item img {
            width: 100%;
            height: 150px;
            object-fit: cover;
        }
        .screenshot-time {
            padding: 8px;
            background: #f8f9fa;
            font-size: 12px;
            text-align: center;
            color: #666;
        }
        .log-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 600px;
            overflow-y: auto;
            line-height: 1.6;
        }
        .log-container .log-error { color: #f48771; }
        .log-container .log-warning { color: #dcdcaa; }
        .log-container .log-info { color: #4fc1ff; }
        .log-container .log-success { color: #4ec9b0; }
        .empty-message {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .lightbox {
            display: none;
            position: fixed;
            z-index: 999;
            padding-top: 50px;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.9);
        }
        .lightbox-content {
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
        }
        .close {
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {{ task.name }}</h1>
            <a href="{{ url_for('index') }}" class="btn btn-primary">← 返回列表</a>
        </div>

        <div class="section">
            <div class="section-title">📸 最近截图</div>
            {% if screenshots|length > 0 %}
            <div class="screenshot-grid">
                {% for screenshot in screenshots %}
                <div class="screenshot-item" onclick="openLightbox('{{ url_for('serve_screenshot', task_id=task.task_id, filename=screenshot.name) }}')">
                    <img src="{{ url_for('serve_screenshot', task_id=task.task_id, filename=screenshot.name) }}" alt="{{ screenshot.name }}">
                    <div class="screenshot-time">{{ screenshot.time }}</div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty-message">还没有截图</div>
            {% endif %}
        </div>

        <div class="section">
            <div class="section-title">📋 运行日志（最近100行）</div>
            <div class="log-container">
                {% if log_lines %}
                    {% for line in log_lines %}
                    <div class="{% if 'ERROR' in line %}log-error{% elif 'WARNING' in line %}log-warning{% elif 'INFO' in line %}log-info{% elif '✓' in line %}log-success{% endif %}">{{ line }}</div>
                    {% endfor %}
                {% else %}
                <div class="empty-message">暂无日志</div>
                {% endif %}
            </div>
        </div>
    </div>

    <div id="lightbox" class="lightbox" onclick="closeLightbox()">
        <span class="close">&times;</span>
        <img class="lightbox-content" id="lightbox-img">
    </div>

    <script>
        function openLightbox(src) {
            document.getElementById('lightbox').style.display = 'block';
            document.getElementById('lightbox-img').src = src;
        }
        function closeLightbox() {
            document.getElementById('lightbox').style.display = 'none';
        }
        // Auto refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''

EDIT_TASK_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>编辑任务 - {{ task.name if task else '新建任务' }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { font-size: 24px; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: white; color: #667eea; }
        .btn:hover { opacity: 0.9; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-section {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }
        input[type="text"],
        input[type="number"],
        textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            font-family: inherit;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            min-height: 150px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .form-actions {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }
        .help-text {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .success {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ '✏️ 编辑任务' if task else '➕ 新建任务' }}</h1>
            <a href="{{ url_for('index') }}" class="btn btn-secondary">← 返回</a>
        </div>

        <div class="form-section">
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            {% if success %}
            <div class="success">{{ success }}</div>
            {% endif %}

            <form method="POST" enctype="multipart/form-data">
                {% if not task %}
                <div class="form-group">
                    <label for="task_id">任务 ID *</label>
                    <input type="text" id="task_id" name="task_id" required
                           pattern="[a-z0-9_-]+"
                           placeholder="例如: my_server_1">
                    <div class="help-text">只能使用小写字母、数字、下划线和连字符</div>
                </div>
                {% endif %}

                <div class="form-group">
                    <label for="name">任务名称 *</label>
                    <input type="text" id="name" name="name" required
                           value="{{ task.name if task else '' }}"
                           placeholder="例如: 我的服务器1">
                </div>

                <div class="form-group">
                    <label for="mchost_url">MCHost URL *</label>
                    <input type="text" id="mchost_url" name="mchost_url" required
                           value="{{ task.mchost_url if task else '' }}"
                           placeholder="https://freemchost.com/dashboard">
                    <div class="help-text">包含 Renew 按钮的页面URL</div>
                </div>

                <div class="form-group">
                    <label for="renew_interval_minutes">续期间隔（分钟）*</label>
                    <input type="number" id="renew_interval_minutes" name="renew_interval_minutes"
                           required min="1" max="1440"
                           value="{{ task.renew_interval_minutes if task else 15 }}">
                    <div class="help-text">推荐: 15 分钟</div>
                </div>

                <div class="form-group">
                    <label for="cookies">Cookies JSON {% if not task %}*{% endif %}</label>
                    <textarea id="cookies" name="cookies"
                              placeholder='粘贴从浏览器导出的 cookies JSON...&#10;&#10;格式示例:&#10;[&#10;  {&#10;    "name": "session",&#10;    "value": "...",&#10;    "domain": ".freemchost.com",&#10;    ...&#10;  }&#10;]'>{{ cookies_content if cookies_content else '' }}</textarea>
                    <div class="help-text">
                        {% if task %}
                        留空则不修改现有 cookies
                        {% else %}
                        新建任务必须提供 cookies
                        {% endif %}
                    </div>
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">💾 保存</button>
                    <a href="{{ url_for('index') }}" class="btn btn-secondary">取消</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''


# ==================== 路由 ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error='密码错误')
    return render_template_string(LOGIN_TEMPLATE)


@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@require_auth
def index():
    """任务列表页面"""
    tasks = task_manager.get_all_tasks_status()
    return render_template_string(TASK_LIST_TEMPLATE, tasks=tasks)


@app.route('/task/<task_id>')
@require_auth
def task_detail(task_id):
    """任务详情页面"""
    task = task_manager.get_task_status(task_id)
    if 'error' in task:
        return f"任务不存在: {task_id}", 404

    # 获取截图列表
    task_dir = task_manager.get_task_dir(task_id)
    screenshots_dir = task_dir / 'screenshots'
    screenshots = []
    if screenshots_dir.exists():
        screenshot_files = sorted(
            screenshots_dir.glob('renew_*.png'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:20]  # 最近20张
        for img in screenshot_files:
            screenshots.append({
                'name': img.name,
                'time': datetime.fromtimestamp(img.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

    # 读取日志
    log_file = task_dir / 'task.log'
    log_lines = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                log_lines = [line.rstrip() for line in lines[-100:]]  # 最后100行
        except:
            pass

    return render_template_string(
        TASK_DETAIL_TEMPLATE,
        task=task,
        screenshots=screenshots,
        log_lines=log_lines
    )


@app.route('/task/<task_id>/screenshot/<filename>')
@require_auth
def serve_screenshot(task_id, filename):
    """提供截图文件"""
    task_dir = task_manager.get_task_dir(task_id)
    screenshot_path = task_dir / 'screenshots' / secure_filename(filename)
    if screenshot_path.exists():
        return send_file(screenshot_path, mimetype='image/png')
    return "Screenshot not found", 404


@app.route('/task/add', methods=['GET', 'POST'])
@require_auth
def add_task():
    """添加新任务"""
    if request.method == 'POST':
        task_id = request.form.get('task_id', '').strip()
        name = request.form.get('name', '').strip()
        mchost_url = request.form.get('mchost_url', '').strip()
        renew_interval_minutes = int(request.form.get('renew_interval_minutes', 15))
        cookies_json = request.form.get('cookies', '').strip()

        # 验证
        if not task_id or not name or not mchost_url or not cookies_json:
            return render_template_string(
                EDIT_TASK_TEMPLATE,
                error='请填写所有必填字段',
                task=None,
                cookies_content=cookies_json
            )

        # 验证 task_id 格式
        import re
        if not re.match(r'^[a-z0-9_-]+$', task_id):
            return render_template_string(
                EDIT_TASK_TEMPLATE,
                error='任务ID只能包含小写字母、数字、下划线和连字符',
                task=None,
                cookies_content=cookies_json
            )

        # 验证 cookies JSON
        try:
            cookies = json.loads(cookies_json)
            if not isinstance(cookies, list):
                raise ValueError('Cookies must be a JSON array')
        except Exception as e:
            return render_template_string(
                EDIT_TASK_TEMPLATE,
                error=f'Cookies JSON 格式错误: {e}',
                task=None,
                cookies_content=cookies_json
            )

        # 添加任务
        if not task_manager.add_task(task_id, name, mchost_url, renew_interval_minutes):
            return render_template_string(
                EDIT_TASK_TEMPLATE,
                error='添加任务失败，任务ID可能已存在',
                task=None,
                cookies_content=cookies_json
            )

        # 保存 cookies
        task_dir = task_manager.get_task_dir(task_id)
        cookies_file = task_dir / 'cookies.json'
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2)

        return redirect(url_for('index'))

    return render_template_string(EDIT_TASK_TEMPLATE, task=None, cookies_content='')


@app.route('/task/<task_id>/edit', methods=['GET', 'POST'])
@require_auth
def edit_task(task_id):
    """编辑任务"""
    task = task_manager.get_task_status(task_id)
    if 'error' in task:
        return f"任务不存在: {task_id}", 404

    # 读取现有 cookies
    task_dir = task_manager.get_task_dir(task_id)
    cookies_file = task_dir / 'cookies.json'
    cookies_content = ''
    if cookies_file.exists():
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies_content = f.read()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        mchost_url = request.form.get('mchost_url', '').strip()
        renew_interval_minutes = int(request.form.get('renew_interval_minutes', 15))
        cookies_json = request.form.get('cookies', '').strip()

        # 更新配置
        if not task_manager.update_task(
            task_id,
            name=name,
            mchost_url=mchost_url,
            renew_interval_minutes=renew_interval_minutes
        ):
            return render_template_string(
                EDIT_TASK_TEMPLATE,
                error='更新任务配置失败',
                task=task,
                cookies_content=cookies_json if cookies_json else cookies_content
            )

        # 如果提供了新的 cookies，保存它
        if cookies_json:
            try:
                cookies = json.loads(cookies_json)
                if not isinstance(cookies, list):
                    raise ValueError('Cookies must be a JSON array')

                with open(cookies_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)
            except Exception as e:
                return render_template_string(
                    EDIT_TASK_TEMPLATE,
                    error=f'Cookies JSON 格式错误: {e}',
                    task=task,
                    cookies_content=cookies_json
                )

        return render_template_string(
            EDIT_TASK_TEMPLATE,
            task=task_manager.get_task_status(task_id),
            cookies_content=cookies_content,
            success='任务更新成功！'
        )

    return render_template_string(
        EDIT_TASK_TEMPLATE,
        task=task,
        cookies_content=cookies_content
    )


@app.route('/task/<task_id>/start')
@require_auth
def start_task(task_id):
    """启动任务"""
    task_manager.start_task(task_id)
    return redirect(url_for('index'))


@app.route('/task/<task_id>/stop')
@require_auth
def stop_task(task_id):
    """停止任务"""
    task_manager.stop_task(task_id)
    return redirect(url_for('index'))


@app.route('/task/<task_id>/restart')
@require_auth
def restart_task(task_id):
    """重启任务"""
    task_manager.restart_task(task_id)
    return redirect(url_for('index'))


@app.route('/task/<task_id>/delete')
@require_auth
def delete_task(task_id):
    """删除任务"""
    task_manager.delete_task(task_id)
    return redirect(url_for('index'))


if __name__ == '__main__':
    # 确保配置文件存在
    config_path = BASE_DIR / 'tasks_config.json'
    if not config_path.exists():
        print("创建默认配置文件...")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"tasks": {}}, f, indent=2)

    print("=" * 50)
    print("MCHost Multi-Task Web Viewer")
    print("=" * 50)
    print(f"访问地址: http://0.0.0.0:5000")
    print(f"默认密码: {PASSWORD}")
    print("=" * 50)
    print()

    app.run(host='0.0.0.0', port=5000, debug=False)
