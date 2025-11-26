#!/usr/bin/env python3
"""
MCHost Auto Renew Script
自动登录MCHost并每15分钟点击Renew按钮
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/mchost_renew.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MCHostRenewer:
    def __init__(self, config_path='config.json'):
        """初始化配置"""
        self.config = self._load_config(config_path)
        self.browser = None
        self.context = None
        self.page = None

    def _load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            required_fields = ['mchost_url', 'username', 'password']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"配置文件缺少必填字段: {field}")

            logger.info(f"成功加载配置文件: {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {config_path}")
            logger.error("请复制 config.json.example 为 config.json 并填写您的信息")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    async def init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()

        # 启动浏览器（使用chromium，headless模式）
        self.browser = await playwright.chromium.launch(
            headless=self.config.get('headless', True),
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # 创建上下文，添加反检测配置
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 添加stealth脚本
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        self.page = await self.context.new_page()
        logger.info("浏览器初始化成功")

    async def login(self):
        """登录MCHost"""
        try:
            logger.info(f"正在访问登录页面: {self.config['mchost_url']}")
            await self.page.goto(self.config['mchost_url'], wait_until='networkidle')

            # 等待Cloudflare验证完成（如果有）
            logger.info("等待页面加载完成（可能需要通过Cloudflare验证）...")
            await asyncio.sleep(5)

            # 查找并填写用户名
            logger.info("正在填写登录信息...")
            username_selectors = [
                'input[name="username"]',
                'input[type="text"]',
                'input[placeholder*="用户名"]',
                'input[placeholder*="username"]',
                '#username'
            ]

            username_filled = False
            for selector in username_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.fill(selector, self.config['username'])
                    username_filled = True
                    logger.info(f"使用选择器填写用户名: {selector}")
                    break
                except:
                    continue

            if not username_filled:
                raise Exception("无法找到用户名输入框")

            # 查找并填写密码
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password'
            ]

            password_filled = False
            for selector in password_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.fill(selector, self.config['password'])
                    password_filled = True
                    logger.info(f"使用选择器填写密码: {selector}")
                    break
                except:
                    continue

            if not password_filled:
                raise Exception("无法找到密码输入框")

            # 等待Cloudflare验证（如果登录表单中有）
            await asyncio.sleep(3)

            # 查找并点击登录按钮
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("登录")',
                'button:has-text("Login")',
                'button:has-text("Sign In")'
            ]

            login_clicked = False
            for selector in login_button_selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    login_clicked = True
                    logger.info(f"点击登录按钮: {selector}")
                    break
                except:
                    continue

            if not login_clicked:
                raise Exception("无法找到登录按钮")

            # 等待登录完成
            logger.info("等待登录完成...")
            await asyncio.sleep(5)

            # 检查是否成功登录（通过查找Renew按钮）
            try:
                await self.page.wait_for_selector('#renewSessionBtn', timeout=10000)
                logger.info("✓ 登录成功！")
                return True
            except PlaywrightTimeoutError:
                logger.warning("未找到Renew按钮，可能登录失败")
                # 保存截图用于调试
                await self.page.screenshot(path='/tmp/mchost_login_failed.png')
                logger.info("已保存截图到: /tmp/mchost_login_failed.png")
                return False

        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            await self.page.screenshot(path='/tmp/mchost_error.png')
            logger.info("已保存错误截图到: /tmp/mchost_error.png")
            return False

    async def click_renew(self):
        """点击Renew按钮"""
        try:
            logger.info("正在点击Renew按钮...")

            # 等待按钮可见
            await self.page.wait_for_selector('#renewSessionBtn', state='visible', timeout=10000)

            # 点击按钮
            await self.page.click('#renewSessionBtn')

            logger.info("✓ 成功点击Renew按钮！")

            # 等待一下看是否有反馈
            await asyncio.sleep(2)

            return True
        except PlaywrightTimeoutError:
            logger.error("找不到Renew按钮，可能会话已过期")
            return False
        except Exception as e:
            logger.error(f"点击Renew按钮时出错: {e}")
            await self.page.screenshot(path='/tmp/mchost_renew_error.png')
            return False

    async def run(self):
        """主运行循环"""
        try:
            # 初始化浏览器
            await self.init_browser()

            # 登录
            if not await self.login():
                logger.error("登录失败，退出程序")
                return

            # 主循环：每15分钟点击一次Renew
            renew_interval = self.config.get('renew_interval_minutes', 15) * 60
            logger.info(f"开始自动续期循环，每 {renew_interval // 60} 分钟执行一次")

            while True:
                # 立即执行一次renew
                success = await self.click_renew()

                if not success:
                    logger.warning("Renew失败，尝试重新登录...")
                    if not await self.login():
                        logger.error("重新登录失败，等待下一个周期再试")

                # 等待指定时间
                logger.info(f"等待 {renew_interval // 60} 分钟后执行下一次续期...")
                await asyncio.sleep(renew_interval)

        except KeyboardInterrupt:
            logger.info("收到退出信号，正在关闭...")
        except Exception as e:
            logger.error(f"运行时错误: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
            logger.info("浏览器已关闭")


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("MCHost 自动续期脚本启动")
    logger.info("=" * 50)

    # 检查配置文件
    config_path = Path(__file__).parent / 'config.json'
    if not config_path.exists():
        logger.error("配置文件不存在！")
        logger.error(f"请创建配置文件: {config_path}")
        logger.error("可以复制 config.json.example 并修改")
        sys.exit(1)

    # 创建并运行renewer
    renewer = MCHostRenewer(str(config_path))
    await renewer.run()


if __name__ == '__main__':
    asyncio.run(main())
