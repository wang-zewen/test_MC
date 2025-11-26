#!/usr/bin/env python3
"""
本地登录脚本 - 用于在有图形界面的电脑上生成 cookies
生成的 cookies.json 可以上传到服务器使用
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

print("=" * 70)
print("MCHost 本地登录工具")
print("=" * 70)
print()
print("此脚本将：")
print("1. 打开浏览器窗口")
print("2. 等待你手动登录 MCHost")
print("3. 自动保存 cookies 到 cookies.json")
print("4. 你可以将 cookies.json 上传到服务器使用")
print()
print("=" * 70)
print()

MCHOST_URL = input("请输入 MCHost 登录页面 URL（直接回车使用默认）: ").strip()
if not MCHOST_URL:
    MCHOST_URL = "https://freemchost.com/auth"

print(f"\n使用 URL: {MCHOST_URL}")
print()


async def main():
    async with async_playwright() as p:
        # 启动浏览器（非 headless 模式）
        print("正在启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"正在打开登录页面: {MCHOST_URL}")
        await page.goto(MCHOST_URL)

        print()
        print("=" * 70)
        print("请在浏览器中完成以下操作：")
        print("  1. 填写用户名和密码")
        print("  2. 完成 Cloudflare 人机验证")
        print("  3. 点击登录按钮")
        print("  4. 看到 Renew 按钮即表示登录成功")
        print()
        print("脚本正在检测登录状态...")
        print("=" * 70)
        print()

        # 等待用户手动登录
        max_wait = 300  # 5 分钟
        check_interval = 3
        elapsed = 0

        while elapsed < max_wait:
            await asyncio.sleep(check_interval)
            elapsed += check_interval

            # 检查是否有 Renew 按钮
            try:
                await page.wait_for_selector('#renewSessionBtn', timeout=1000, state='visible')
                print()
                print("=" * 70)
                print("✓ 检测到登录成功！")
                print("=" * 70)
                print()

                # 保存 cookies
                cookies = await context.cookies()
                cookies_file = Path(__file__).parent / 'cookies.json'

                with open(cookies_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)

                print(f"✓ Cookies 已保存到: {cookies_file}")
                print()
                print("接下来：")
                print(f"1. 将 cookies.json 上传到服务器:")
                print(f"   scp {cookies_file} root@your-server-ip:/root/test_MC/")
                print()
                print("2. 在服务器上运行脚本，将自动使用这个 cookies 登录")
                print()
                print("=" * 70)

                await asyncio.sleep(3)
                await browser.close()
                return

            except:
                if elapsed % 15 == 0:
                    print(f"等待中... ({elapsed}/{max_wait} 秒)")

        # 超时
        print()
        print("=" * 70)
        print("❌ 登录超时！")
        print(f"已等待 {max_wait} 秒，未检测到登录成功")
        print("请重新运行此脚本")
        print("=" * 70)
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
