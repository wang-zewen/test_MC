#!/usr/bin/env python3
"""
MCHost 多任务管理器
管理多个 MCHost 自动续期任务
"""

import json
import os
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/mchost_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器"""

    def __init__(self, config_path: str = None):
        """
        初始化任务管理器

        Args:
            config_path: 配置文件路径
        """
        self.base_dir = Path(__file__).parent
        self.config_path = Path(config_path) if config_path else self.base_dir / 'tasks_config.json'
        self.tasks_dir = self.base_dir / 'tasks'
        self.tasks_dir.mkdir(exist_ok=True)

        # 任务进程字典 {task_id: subprocess.Popen}
        self.processes: Dict[str, subprocess.Popen] = {}

        # 加载配置
        self.config = self.load_config()

    def load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path}")
            return {"tasks": {}}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✓ 加载配置文件成功，共 {len(config.get('tasks', {}))} 个任务")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {"tasks": {}}

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("✓ 配置文件已保存")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def get_task_dir(self, task_id: str) -> Path:
        """获取任务目录"""
        task_dir = self.tasks_dir / task_id
        task_dir.mkdir(exist_ok=True)
        return task_dir

    def get_task_config(self, task_id: str) -> Optional[dict]:
        """获取任务配置"""
        return self.config.get('tasks', {}).get(task_id)

    def add_task(self, task_id: str, name: str, mchost_url: str,
                 renew_interval_minutes: int = 15) -> bool:
        """
        添加新任务

        Args:
            task_id: 任务ID
            name: 任务名称
            mchost_url: MCHost URL
            renew_interval_minutes: 续期间隔（分钟）

        Returns:
            是否添加成功
        """
        if task_id in self.config.get('tasks', {}):
            logger.error(f"任务ID已存在: {task_id}")
            return False

        if 'tasks' not in self.config:
            self.config['tasks'] = {}

        self.config['tasks'][task_id] = {
            'name': name,
            'mchost_url': mchost_url,
            'renew_interval_minutes': renew_interval_minutes,
            'enabled': True,
            'created_at': datetime.now().isoformat(),
            'last_run': None
        }

        # 创建任务目录
        task_dir = self.get_task_dir(task_id)
        (task_dir / 'screenshots').mkdir(exist_ok=True)

        self.save_config()
        logger.info(f"✓ 添加任务成功: {task_id} ({name})")
        return True

    def update_task(self, task_id: str, **kwargs) -> bool:
        """
        更新任务配置

        Args:
            task_id: 任务ID
            **kwargs: 要更新的配置项

        Returns:
            是否更新成功
        """
        if task_id not in self.config.get('tasks', {}):
            logger.error(f"任务不存在: {task_id}")
            return False

        for key, value in kwargs.items():
            if key in ['name', 'mchost_url', 'renew_interval_minutes', 'enabled']:
                self.config['tasks'][task_id][key] = value

        self.save_config()
        logger.info(f"✓ 更新任务配置成功: {task_id}")
        return True

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        if task_id not in self.config.get('tasks', {}):
            logger.error(f"任务不存在: {task_id}")
            return False

        # 停止任务
        self.stop_task(task_id)

        # 删除配置
        del self.config['tasks'][task_id]
        self.save_config()

        logger.info(f"✓ 删除任务成功: {task_id}")
        return True

    def start_task(self, task_id: str) -> bool:
        """
        启动任务

        Args:
            task_id: 任务ID

        Returns:
            是否启动成功
        """
        task_config = self.get_task_config(task_id)
        if not task_config:
            logger.error(f"任务不存在: {task_id}")
            return False

        if not task_config.get('enabled', True):
            logger.warning(f"任务已禁用: {task_id}")
            return False

        # 检查是否已经在运行
        if task_id in self.processes:
            if self.processes[task_id].poll() is None:
                logger.warning(f"任务已在运行: {task_id}")
                return False

        # 启动任务进程
        try:
            python_path = self.base_dir / 'venv' / 'bin' / 'python'
            script_path = self.base_dir / 'mchost_renew.py'
            task_dir = self.get_task_dir(task_id)
            log_file = task_dir / 'task.log'

            # 打开日志文件
            log_fd = open(log_file, 'a', encoding='utf-8')

            # 启动进程
            process = subprocess.Popen(
                [str(python_path), str(script_path), '--task-id', task_id],
                stdout=log_fd,
                stderr=subprocess.STDOUT,
                cwd=str(self.base_dir)
            )

            self.processes[task_id] = process

            # 更新最后运行时间
            self.config['tasks'][task_id]['last_run'] = datetime.now().isoformat()
            self.save_config()

            logger.info(f"✓ 启动任务成功: {task_id} (PID: {process.pid})")
            return True

        except Exception as e:
            logger.error(f"启动任务失败: {task_id} - {e}")
            return False

    def stop_task(self, task_id: str) -> bool:
        """
        停止任务

        Args:
            task_id: 任务ID

        Returns:
            是否停止成功
        """
        if task_id not in self.processes:
            logger.warning(f"任务未运行: {task_id}")
            return False

        process = self.processes[task_id]

        try:
            # 发送终止信号
            process.terminate()

            # 等待进程结束（最多5秒）
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 强制杀死
                process.kill()
                process.wait()

            del self.processes[task_id]
            logger.info(f"✓ 停止任务成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"停止任务失败: {task_id} - {e}")
            return False

    def restart_task(self, task_id: str) -> bool:
        """
        重启任务

        Args:
            task_id: 任务ID

        Returns:
            是否重启成功
        """
        logger.info(f"重启任务: {task_id}")
        self.stop_task(task_id)
        time.sleep(1)
        return self.start_task(task_id)

    def get_task_status(self, task_id: str) -> dict:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        task_config = self.get_task_config(task_id)
        if not task_config:
            return {'error': '任务不存在'}

        is_running = False
        pid = None

        if task_id in self.processes:
            process = self.processes[task_id]
            if process.poll() is None:
                is_running = True
                pid = process.pid
            else:
                # 进程已结束，清理
                del self.processes[task_id]

        return {
            'task_id': task_id,
            'name': task_config.get('name'),
            'enabled': task_config.get('enabled', True),
            'running': is_running,
            'pid': pid,
            'mchost_url': task_config.get('mchost_url'),
            'renew_interval_minutes': task_config.get('renew_interval_minutes'),
            'created_at': task_config.get('created_at'),
            'last_run': task_config.get('last_run')
        }

    def get_all_tasks_status(self) -> list:
        """获取所有任务状态"""
        return [
            self.get_task_status(task_id)
            for task_id in self.config.get('tasks', {}).keys()
        ]

    def start_all_enabled_tasks(self):
        """启动所有已启用的任务"""
        for task_id, task_config in self.config.get('tasks', {}).items():
            if task_config.get('enabled', True):
                self.start_task(task_id)

    def stop_all_tasks(self):
        """停止所有任务"""
        for task_id in list(self.processes.keys()):
            self.stop_task(task_id)

    def run_forever(self):
        """持续运行，监控任务状态"""
        logger.info("任务管理器启动")

        # 启动所有已启用的任务
        self.start_all_enabled_tasks()

        # 注册信号处理
        def signal_handler(sig, frame):
            logger.info("收到停止信号，正在停止所有任务...")
            self.stop_all_tasks()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 监控循环
        try:
            while True:
                time.sleep(30)  # 每30秒检查一次

                # 检查已启用但未运行的任务
                for task_id, task_config in self.config.get('tasks', {}).items():
                    if not task_config.get('enabled', True):
                        continue

                    # 检查进程是否还在运行
                    if task_id in self.processes:
                        if self.processes[task_id].poll() is not None:
                            # 进程已结束，重新启动
                            logger.warning(f"任务已停止，正在重启: {task_id}")
                            del self.processes[task_id]
                            self.start_task(task_id)
                    else:
                        # 任务未运行，启动它
                        logger.info(f"启动任务: {task_id}")
                        self.start_task(task_id)

        except Exception as e:
            logger.error(f"监控循环异常: {e}")
            self.stop_all_tasks()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='MCHost 多任务管理器')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')

    args = parser.parse_args()

    manager = TaskManager(config_path=args.config)

    if args.daemon:
        manager.run_forever()
    else:
        # 交互模式
        print("MCHost 任务管理器")
        print("=" * 50)
        manager.start_all_enabled_tasks()
        print("\n按 Ctrl+C 停止所有任务并退出")

        try:
            signal.pause()
        except KeyboardInterrupt:
            print("\n正在停止所有任务...")
            manager.stop_all_tasks()


if __name__ == '__main__':
    main()
