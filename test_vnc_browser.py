#!/usr/bin/env python3
"""
测试浏览器是否能显示在VNC桌面上
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_browser_on_vnc():
    print("测试浏览器在VNC上显示...")

    # 设置DISPLAY环境变量
    os.environ['DISPLAY'] = ':99'
    print(f"设置 DISPLAY={os.environ.get('DISPLAY')}")

    # 准备环境变量
    browser_env = os.environ.copy()
    browser_env['DISPLAY'] = ':99'

    playwright = await async_playwright().start()

    # 启动headed模式浏览器
    browser = await playwright.chromium.launch(
        headless=False,
        env=browser_env,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
        ]
    )

    print("✓ 浏览器已启动（headed模式）")
    print("请检查VNC界面 (http://服务器IP:6080/vnc.html)")
    print("应该能看到浏览器窗口")
    print()
    print("按Ctrl+C停止测试...")

    # 打开一个测试页面
    page = await browser.new_page()
    await page.goto('https://example.com')
    print("✓ 已打开测试页面: https://example.com")

    # 保持运行
    try:
        await asyncio.sleep(3600)  # 运行1小时
    except KeyboardInterrupt:
        print("\n停止测试...")

    await browser.close()
    await playwright.stop()

if __name__ == '__main__':
    asyncio.run(test_browser_on_vnc())
