#!/usr/bin/env python3
"""
Cloudflare验证解决方案
支持 Capsolver 和 FlareSolverr
"""

import asyncio
import logging
import aiohttp
import time
from typing import Optional, Dict, Any


class CloudflareSolver:
    """Cloudflare验证解决器"""

    def __init__(self, solver_type: str, config: Dict[str, Any], logger: logging.Logger):
        """
        初始化

        Args:
            solver_type: 解决方案类型 ("capsolver" 或 "flaresolverr")
            config: 配置信息
            logger: 日志记录器
        """
        self.solver_type = solver_type.lower()
        self.config = config
        self.logger = logger

    async def solve_turnstile(self, page_url: str, site_key: str) -> Optional[str]:
        """
        解决Cloudflare Turnstile验证

        Args:
            page_url: 页面URL
            site_key: Turnstile site key

        Returns:
            验证token，失败返回None
        """
        if self.solver_type == "capsolver":
            return await self._solve_with_capsolver(page_url, site_key)
        elif self.solver_type == "flaresolverr":
            return await self._solve_with_flaresolverr(page_url)
        else:
            self.logger.error(f"未知的解决方案类型: {self.solver_type}")
            return None

    async def _solve_with_capsolver(self, page_url: str, site_key: str) -> Optional[str]:
        """使用Capsolver解决Turnstile"""
        try:
            api_key = self.config.get('capsolver_api_key')
            if not api_key:
                self.logger.error("未配置 capsolver_api_key")
                return None

            self.logger.info("🔐 使用Capsolver解决Cloudflare验证...")

            # 创建任务
            task_data = {
                "clientKey": api_key,
                "task": {
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteURL": page_url,
                    "websiteKey": site_key
                }
            }

            async with aiohttp.ClientSession() as session:
                # 提交任务
                async with session.post(
                    'https://api.capsolver.com/createTask',
                    json=task_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    result = await resp.json()

                    if result.get('errorId') != 0:
                        self.logger.error(f"Capsolver创建任务失败: {result.get('errorDescription')}")
                        return None

                    task_id = result.get('taskId')
                    self.logger.info(f"✓ 任务已创建: {task_id}")

                # 轮询结果（最多等待60秒）
                max_wait = 60
                start_time = time.time()

                while time.time() - start_time < max_wait:
                    await asyncio.sleep(3)

                    async with session.post(
                        'https://api.capsolver.com/getTaskResult',
                        json={
                            "clientKey": api_key,
                            "taskId": task_id
                        },
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        result = await resp.json()

                        status = result.get('status')
                        if status == 'ready':
                            token = result.get('solution', {}).get('token')
                            self.logger.info("✓ Cloudflare验证成功！")
                            return token
                        elif status == 'failed':
                            self.logger.error(f"验证失败: {result.get('errorDescription')}")
                            return None
                        else:
                            elapsed = int(time.time() - start_time)
                            self.logger.info(f"等待验证... ({elapsed}秒)")

                self.logger.error("验证超时")
                return None

        except Exception as e:
            self.logger.error(f"Capsolver解决失败: {e}")
            return None

    async def _solve_with_flaresolverr(self, page_url: str) -> Optional[Dict[str, Any]]:
        """使用FlareSolverr解决Cloudflare"""
        try:
            endpoint = self.config.get('flaresolverr_endpoint', 'http://localhost:8191/v1')

            self.logger.info("🔐 使用FlareSolverr解决Cloudflare验证...")

            request_data = {
                "cmd": "request.get",
                "url": page_url,
                "maxTimeout": 60000
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as resp:
                    result = await resp.json()

                    if result.get('status') == 'ok':
                        self.logger.info("✓ FlareSolverr验证成功！")
                        return {
                            'cookies': result.get('solution', {}).get('cookies', []),
                            'user_agent': result.get('solution', {}).get('userAgent')
                        }
                    else:
                        self.logger.error(f"FlareSolverr失败: {result.get('message')}")
                        return None

        except Exception as e:
            self.logger.error(f"FlareSolverr解决失败: {e}")
            return None

    async def get_cookies_from_flaresolverr(self, page_url: str) -> Optional[list]:
        """
        使用FlareSolverr获取可用的cookies

        Args:
            page_url: 目标URL

        Returns:
            cookies列表，失败返回None
        """
        result = await self._solve_with_flaresolverr(page_url)
        if result:
            return result.get('cookies')
        return None
