#!/usr/bin/env python3
"""
MCHost Auto Renew Script
自动登录MCHost并每15分钟点击Renew按钮
支持多任务模式
"""

import asyncio
import json
import logging
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


class MCHostRenewer:
    def __init__(self, task_id=None, config_path=None):
        """
        初始化配置

        Args:
            task_id: 任务ID（多任务模式）
            config_path: 配置文件路径（单任务模式，兼容旧版本）
        """
        self.base_dir = Path(__file__).parent
        self.task_id = task_id

        # 多任务模式
        if task_id:
            self.task_dir = self.base_dir / 'tasks' / task_id
            self.task_dir.mkdir(parents=True, exist_ok=True)
            self.screenshots_dir = self.task_dir / 'screenshots'
            self.screenshots_dir.mkdir(exist_ok=True)
            self.cookies_file = self.task_dir / 'cookies.json'
            self.log_file = self.task_dir / 'task.log'
            self.config = self._load_task_config(task_id)
        # 单任务模式（向后兼容）
        else:
            config_path = config_path or (self.base_dir / 'config.json')
            self.screenshots_dir = self.base_dir / 'screenshots'
            self.screenshots_dir.mkdir(exist_ok=True)
            self.cookies_file = self.base_dir / 'cookies.json'
            self.log_file = Path('/var/log/mchost_renew.log')
            self.config = self._load_config(config_path)

        # 配置日志
        self._setup_logging()

        self.browser = None
        self.context = None
        self.page = None

    def _setup_logging(self):
        """配置日志"""
        # 清除现有handlers
        logger = logging.getLogger()
        logger.handlers.clear()

        # 设置日志级别
        logger.setLevel(logging.INFO)

        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 文件handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 控制台handler（仅在非多任务模式下）
        if not self.task_id:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        self.logger = logger

    def _load_task_config(self, task_id):
        """从多任务配置文件加载任务配置"""
        try:
            tasks_config_path = self.base_dir / 'tasks_config.json'
            if not tasks_config_path.exists():
                self.logger.error(f"多任务配置文件不存在: {tasks_config_path}")
                sys.exit(1)

            with open(tasks_config_path, 'r', encoding='utf-8') as f:
                tasks_config = json.load(f)

            task_config = tasks_config.get('tasks', {}).get(task_id)
            if not task_config:
                self.logger.error(f"任务不存在: {task_id}")
                sys.exit(1)

            self.logger.info(f"✓ 加载任务配置: {task_id} ({task_config.get('name')})")
            return task_config

        except Exception as e:
            self.logger.error(f"加载任务配置失败: {e}")
            sys.exit(1)

    def _load_config(self, config_path):
        """加载配置文件（单任务模式）"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            required_fields = ['mchost_url']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"配置文件缺少必填字段: {field}")

            self.logger.info(f"成功加载配置文件: {config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"配置文件不存在: {config_path}")
            self.logger.error("请复制 config.json.example 为 config.json 并填写您的信息")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    async def init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()

        # 启动浏览器（多任务模式强制使用headless）
        headless = True if self.task_id else self.config.get('headless', True)

        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )

        # 创建上下文，添加反检测配置
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )

        # 添加stealth脚本
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            window.chrome = {
                runtime: {}
            };
        """)

        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)

        self.logger.info("✓ 浏览器初始化成功")

    async def save_cookies(self):
        """保存cookies到文件"""
        try:
            cookies = await self.context.cookies()
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            self.logger.info(f"✓ Cookies已保存到: {self.cookies_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存cookies失败: {e}")
            return False

    async def load_cookies(self):
        """从文件加载cookies"""
        try:
            if not self.cookies_file.exists():
                self.logger.info("未找到cookies文件，需要手动登录")
                return False

            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            # 修正 sameSite 值的格式（首字母大写）
            for cookie in cookies:
                if 'sameSite' in cookie:
                    same_site = cookie['sameSite']
                    if isinstance(same_site, str):
                        cookie['sameSite'] = same_site.capitalize()

            await self.context.add_cookies(cookies)
            self.logger.info("✓ Cookies已加载")
            return True
        except Exception as e:
            self.logger.error(f"加载cookies失败: {e}")
            return False

    async def check_login_status(self):
        """检查是否已登录（通过查找Renew按钮）"""
        try:
            await self.page.goto(self.config['mchost_url'], wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            # 查找Renew按钮
            try:
                await self.page.wait_for_selector('#renewSessionBtn', timeout=5000, state='visible')
                self.logger.info("✓ 已登录状态确认")
                return True
            except:
                self.logger.info("未检测到登录状态")
                return False
        except Exception as e:
            self.logger.error(f"检查登录状态失败: {e}")
            return False

    async def manual_login(self):
        """手动登录模式 - 等待用户手动完成登录"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("手动登录模式")
            self.logger.info("=" * 60)
            self.logger.info(f"正在打开登录页面: {self.config['mchost_url']}")
            self.logger.info("")
            self.logger.info("请在打开的浏览器窗口中手动完成以下操作：")
            self.logger.info("  1. 填写用户名和密码")
            self.logger.info("  2. 完成 Cloudflare 人机验证")
            self.logger.info("  3. 点击登录按钮")
            self.logger.info("  4. 等待登录成功（看到 Renew 按钮）")
            self.logger.info("")
            self.logger.info("脚本将自动检测登录状态...")
            self.logger.info("=" * 60)

            # 打开登录页面
            await self.page.goto(self.config['mchost_url'], wait_until='domcontentloaded', timeout=60000)

            # 等待用户手动登录，最多等待 5 分钟
            max_wait_time = 300  # 5分钟
            check_interval = 3   # 每3秒检查一次
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval

                # 检查是否出现了 Renew 按钮（表示登录成功）
                try:
                    await self.page.wait_for_selector('#renewSessionBtn', timeout=1000, state='visible')
                    self.logger.info("")
                    self.logger.info("=" * 60)
                    self.logger.info("✓ 检测到登录成功！")
                    self.logger.info("=" * 60)

                    # 保存登录成功截图
                    screenshot_path = self.screenshots_dir / 'login_success.png'
                    await self.page.screenshot(path=str(screenshot_path), full_page=True)
                    self.logger.info(f"✓ 已保存登录成功截图到: {screenshot_path}")

                    # 保存 cookies
                    if await self.save_cookies():
                        self.logger.info("✓ 登录会话已保存")
                        self.logger.info("✓ 下次运行将自动使用保存的会话，无需再次登录")

                    return True
                except:
                    # 还未登录，继续等待
                    if elapsed_time % 15 == 0:  # 每15秒提示一次
                        self.logger.info(f"等待中... ({elapsed_time}/{max_wait_time}秒)")
                    pass

            # 超时
            self.logger.error("")
            self.logger.error("=" * 60)
            self.logger.error("登录超时！")
            self.logger.error(f"已等待 {max_wait_time} 秒，但未检测到登录成功")
            self.logger.error("请重新运行脚本并在 5 分钟内完成登录")
            self.logger.error("=" * 60)
            screenshot_path = self.screenshots_dir / 'login_timeout.png'
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"已保存超时截图到: {screenshot_path}")
            return False

        except Exception as e:
            self.logger.error(f"手动登录过程出错: {e}")
            screenshot_path = self.screenshots_dir / 'error.png'
            await self.page.screenshot(path=str(screenshot_path))
            self.logger.info(f"已保存错误截图到: {screenshot_path}")
            return False

    async def click_renew(self):
        """点击Renew按钮"""
        try:
            self.logger.info("正在点击Renew按钮...")

            # 等待按钮可见
            await self.page.wait_for_selector('#renewSessionBtn', state='visible', timeout=10000)

            # 点击按钮
            await self.page.click('#renewSessionBtn')

            self.logger.info("✓ 成功点击Renew按钮！")

            # 等待一下看是否有反馈
            await asyncio.sleep(2)

            # 保存截图（用于Web查看）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = self.screenshots_dir / f'renew_{timestamp}.png'
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"✓ 已保存截图到: {screenshot_path}")

            # 清理旧截图（只保留最近50张）
            screenshots = sorted(self.screenshots_dir.glob('renew_*.png'), key=os.path.getmtime, reverse=True)
            for old_screenshot in screenshots[50:]:
                old_screenshot.unlink()
                self.logger.debug(f"清理旧截图: {old_screenshot.name}")

            return True
        except PlaywrightTimeoutError:
            self.logger.error("找不到Renew按钮，可能会话已过期")
            return False
        except Exception as e:
            self.logger.error(f"点击Renew按钮时出错: {e}")
            screenshot_path = self.screenshots_dir / 'renew_error.png'
            await self.page.screenshot(path=str(screenshot_path))
            return False

    async def run(self):
        """主运行循环"""
        try:
            # 多任务模式下，cookies必须已存在
            if self.task_id and not self.cookies_file.exists():
                self.logger.error("多任务模式下需要先上传 cookies.json 文件")
                self.logger.error(f"请将 cookies 文件放置在: {self.cookies_file}")
                return

            # 检查是否需要手动登录（没有cookies文件时使用非headless模式）
            need_manual_login = not self.cookies_file.exists()

            if need_manual_login:
                self.logger.info("首次运行，需要手动登录")
                self.logger.info("将打开浏览器窗口...")
                # 临时设置为非headless模式
                original_headless = self.config.get('headless', True)
                self.config['headless'] = False

            # 初始化浏览器
            await self.init_browser()

            # 尝试加载cookies
            logged_in = False
            if await self.load_cookies():
                # 检查cookies是否有效
                self.logger.info("检查保存的登录会话是否有效...")
                if await self.check_login_status():
                    logged_in = True
                    self.logger.info("✓ 使用保存的会话登录成功")
                else:
                    self.logger.warning("保存的会话已失效，需要重新登录")

            # 如果cookies无效或不存在，进行手动登录
            if not logged_in:
                self.logger.info("")
                if need_manual_login:
                    self.logger.info("需要手动登录（首次运行或会话失效）")
                else:
                    self.logger.info("会话失效，需要重新登录")
                    # 如果之前是headless模式，现在需要重新打开非headless浏览器
                    if self.config.get('headless', True):
                        self.logger.info("正在重启浏览器以显示窗口...")
                        await self.cleanup()
                        self.config['headless'] = False
                        await self.init_browser()

                if not await self.manual_login():
                    self.logger.error("手动登录失败，退出程序")
                    return

                # 恢复headless设置
                if need_manual_login:
                    self.config['headless'] = original_headless

            # 检查是否为测试模式
            test_mode = self.config.get('test_mode', False)
            if test_mode:
                self.logger.info("")
                self.logger.info("=" * 60)
                self.logger.info("测试模式：登录成功，即将退出")
                self.logger.info(f"请查看截图: {self.screenshots_dir}/login_success.png")
                self.logger.info("=" * 60)
                self.logger.info("")
                self.logger.info("确认登录成功后：")
                self.logger.info("1. 将 config.json 中的 test_mode 改为 false")
                self.logger.info("2. 再次运行脚本，将自动使用保存的会话")
                self.logger.info("3. 后续运行可以使用 headless: true（无窗口模式）")
                self.logger.info("=" * 60)
                await asyncio.sleep(5)
                return

            # 如果首次登录，提示用户可以关闭浏览器窗口
            if need_manual_login and not self.task_id:
                self.logger.info("")
                self.logger.info("=" * 60)
                self.logger.info("提示：登录会话已保存")
                self.logger.info("后续运行将自动使用保存的会话，无需再次登录")
                self.logger.info("您可以：")
                self.logger.info("  - 将 config.json 中的 headless 改为 true（无窗口模式）")
                self.logger.info("  - 或继续使用当前窗口（将保持打开状态）")
                self.logger.info("=" * 60)
                self.logger.info("")

            # 主循环：每N分钟点击一次Renew
            renew_interval = self.config.get('renew_interval_minutes', 15) * 60
            self.logger.info(f"开始自动续期循环，每 {renew_interval // 60} 分钟执行一次")
            self.logger.info("")

            while True:
                # 立即执行一次renew
                success = await self.click_renew()

                if not success:
                    self.logger.warning("Renew失败，会话可能已过期")
                    self.logger.info("尝试使用保存的cookies重新登录...")

                    # 重新加载页面和cookies
                    if await self.load_cookies() and await self.check_login_status():
                        self.logger.info("✓ 重新登录成功")
                    else:
                        self.logger.error("会话已完全失效")
                        if self.task_id:
                            self.logger.error("请通过Web界面更新cookies")
                        else:
                            self.logger.error("请手动重新运行脚本进行登录")
                        return

                # 等待指定时间
                self.logger.info(f"等待 {renew_interval // 60} 分钟后执行下一次续期...")
                await asyncio.sleep(renew_interval)

        except KeyboardInterrupt:
            self.logger.info("收到退出信号，正在关闭...")
        except Exception as e:
            self.logger.error(f"运行时错误: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
            self.logger.info("浏览器已关闭")
        except Exception as e:
            self.logger.warning(f"清理资源时出错: {e}")


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='MCHost 自动续期脚本')
    parser.add_argument('--task-id', type=str, help='任务ID（多任务模式）')
    parser.add_argument('--config', type=str, help='配置文件路径（单任务模式）')
    args = parser.parse_args()

    # 初始化logger（临时用于启动信息）
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    logger.info("=" * 50)
    logger.info("MCHost 自动续期脚本启动")
    if args.task_id:
        logger.info(f"运行模式: 多任务 (Task ID: {args.task_id})")
    else:
        logger.info("运行模式: 单任务")
    logger.info("=" * 50)

    # 单任务模式：检查配置文件
    if not args.task_id:
        base_dir = Path(__file__).parent
        config_path = Path(args.config) if args.config else (base_dir / 'config.json')
        if not config_path.exists():
            logger.error("配置文件不存在！")
            logger.error(f"请创建配置文件: {config_path}")
            logger.error("可以复制 config.json.example 并修改")
            sys.exit(1)

    # 创建并运行renewer
    renewer = MCHostRenewer(task_id=args.task_id, config_path=args.config)
    await renewer.run()


if __name__ == '__main__':
    asyncio.run(main())
