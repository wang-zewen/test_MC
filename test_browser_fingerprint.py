#!/usr/bin/env python3
"""
浏览器指纹测试脚本
测试浏览器是否能通过Cloudflare等反爬虫检测
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

async def test_fingerprint():
    """测试浏览器指纹"""
    print("=" * 60)
    print("浏览器指纹测试")
    print("=" * 60)
    print()

    base_dir = Path(__file__).parent

    # 读取stealth脚本
    stealth_js_path = base_dir / 'stealth.js'
    if not stealth_js_path.exists():
        print("❌ 未找到stealth.js文件")
        return

    with open(stealth_js_path, 'r', encoding='utf-8') as f:
        stealth_js = f.read()

    async with async_playwright() as p:
        # 启动浏览器（带反检测参数）
        print("1️⃣ 启动浏览器...")

        launch_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--exclude-switches=enable-automation',
            '--disable-automation',
            '--disable-infobars'
        ]

        try:
            browser = await p.chromium.launch(
                headless=False,
                channel="chrome",
                args=launch_args
            )
        except Exception as e:
            print(f"Chrome不可用，使用Chromium: {e}")
            browser = await p.chromium.launch(
                headless=False,
                args=launch_args
            )

        # 创建上下文
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )

        # 加载反检测脚本
        await context.add_init_script(stealth_js)
        print("✓ 反检测脚本已加载")
        print()

        page = await context.new_page()

        # 测试1: 检查基本指纹
        print("2️⃣ 测试基本浏览器指纹...")
        await page.goto('about:blank')

        fingerprint = await page.evaluate("""
            () => {
                return {
                    webdriver: navigator.webdriver,
                    languages: navigator.languages,
                    plugins: navigator.plugins.length,
                    platform: navigator.platform,
                    vendor: navigator.vendor,
                    hasChrome: !!window.chrome,
                    hardwareConcurrency: navigator.hardwareConcurrency,
                    deviceMemory: navigator.deviceMemory,
                    userAgent: navigator.userAgent
                };
            }
        """)

        print("   基本指纹信息:")
        for key, value in fingerprint.items():
            status = "✓" if value not in [True, None, 0] or key == 'webdriver' and value is None else "⚠️"
            print(f"   {status} {key}: {value}")
        print()

        # 测试2: 访问Cloudflare测试页面
        print("3️⃣ 测试Cloudflare检测...")
        print("   访问: https://nowsecure.nl")

        try:
            await page.goto('https://nowsecure.nl', wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)

            # 检查是否被阻止
            title = await page.title()
            url = page.url

            print(f"   页面标题: {title}")
            print(f"   当前URL: {url}")

            # 检查页面内容
            content = await page.content()

            if 'challenge' in content.lower() or 'cloudflare' in content.lower():
                print("   ⚠️ 检测到Cloudflare验证页面")
            else:
                print("   ✓ 成功访问，未被Cloudflare阻止")
        except Exception as e:
            print(f"   ❌ 访问失败: {e}")

        print()

        # 测试3: 访问BrowserLeaks
        print("4️⃣ 测试浏览器泄露检测...")
        print("   访问: https://browserleaks.com/javascript")

        try:
            await page.goto('https://browserleaks.com/javascript', wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            print("   ✓ 页面已加载")
            print("   ℹ️ 请在浏览器中查看检测结果")
        except Exception as e:
            print(f"   ❌ 访问失败: {e}")

        print()

        # 测试4: Canvas指纹
        print("5️⃣ 测试Canvas指纹...")
        canvas_fp = await page.evaluate("""
            () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                ctx.fillText('test', 10, 10);
                return canvas.toDataURL();
            }
        """)
        print(f"   Canvas指纹: {canvas_fp[:50]}...")
        print()

        # 测试5: WebGL指纹
        print("6️⃣ 测试WebGL指纹...")
        webgl_fp = await page.evaluate("""
            () => {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl');
                if (!gl) return 'WebGL不可用';

                return {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    unmaskedVendor: gl.getParameter(0x9245),
                    unmaskedRenderer: gl.getParameter(0x9246)
                };
            }
        """)

        for key, value in webgl_fp.items() if isinstance(webgl_fp, dict) else {}:
            print(f"   {key}: {value}")
        print()

        # 等待用户检查
        print("=" * 60)
        print("测试完成！")
        print()
        print("浏览器窗口将保持打开30秒，请检查:")
        print("1. navigator.webdriver 是否为 undefined")
        print("2. 是否能正常访问网站")
        print("3. Cloudflare是否阻止访问")
        print("=" * 60)

        await asyncio.sleep(30)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_fingerprint())
