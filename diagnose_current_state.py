#!/usr/bin/env python3
"""
诊断当前登录和验证状态
检查CF是否真的通过，还是被静默阻止
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

async def diagnose_mchost():
    """诊断MCHost登录状态"""
    print("=" * 60)
    print("MCHost 状态诊断")
    print("=" * 60)
    print()

    base_dir = Path(__file__).parent

    # 读取stealth脚本
    stealth_js_path = base_dir / 'stealth.js'
    if stealth_js_path.exists():
        with open(stealth_js_path, 'r', encoding='utf-8') as f:
            stealth_js = f.read()
        print("✓ 已加载 stealth.js")
    else:
        print("❌ 未找到 stealth.js")
        stealth_js = None

    async with async_playwright() as p:
        print("\n1️⃣ 启动浏览器...")

        launch_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--exclude-switches=enable-automation',
            '--disable-automation',
            '--disable-infobars',
            '--enable-features=NetworkService,NetworkServiceInProcess'
        ]

        try:
            browser = await p.chromium.launch(
                headless=False,
                channel="chrome",
                args=launch_args
            )
            print("✓ 使用 Chrome")
        except Exception as e:
            print(f"⚠️ Chrome不可用，使用Chromium: {e}")
            browser = await p.chromium.launch(
                headless=False,
                args=launch_args
            )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )

        if stealth_js:
            await context.add_init_script(stealth_js)
            print("✓ 已加载反检测脚本")

        page = await context.new_page()

        # 测试访问MCHost
        print("\n2️⃣ 访问 MCHost...")
        mchost_url = "https://freemchost.com/auth"

        try:
            response = await page.goto(mchost_url, wait_until='domcontentloaded', timeout=30000)
            print(f"✓ 页面已加载")
            print(f"   状态码: {response.status}")
            print(f"   URL: {page.url}")

            await asyncio.sleep(5)

            # 获取页面信息
            title = await page.title()
            print(f"   标题: {title}")

            # 检查是否有CF验证
            print("\n3️⃣ 检查 Cloudflare 验证...")

            cf_selectors = {
                'CF Challenge iframe': 'iframe[src*="challenges.cloudflare.com"]',
                'CF iframe': 'iframe[src*="cloudflare"]',
                'Turnstile': '[data-sitekey]',
                'CF wrapper': '#cf-wrapper',
                'CF verification': '.cf-browser-verification'
            }

            cf_found = False
            for name, selector in cf_selectors.items():
                element = await page.query_selector(selector)
                if element:
                    try:
                        is_visible = await element.is_visible()
                        if is_visible:
                            print(f"   ⚠️ {name}: 存在且可见")
                            cf_found = True
                        else:
                            print(f"   ℹ️ {name}: 存在但不可见")
                    except:
                        print(f"   ℹ️ {name}: 存在 (可见性未知)")

            if not cf_found:
                print("   ✓ 未检测到 Cloudflare 验证框")

            # 检查页面内容
            print("\n4️⃣ 检查页面内容...")

            # 检查是否被阻止
            content = await page.content()

            if 'just a moment' in content.lower():
                print("   ⚠️ 页面显示 'Just a moment' (正在验证)")
            elif 'challenge' in content.lower():
                print("   ⚠️ 页面包含 'challenge' (可能被挑战)")
            elif 'access denied' in content.lower() or 'blocked' in content.lower():
                print("   ❌ 页面显示被阻止")
            else:
                print("   ✓ 页面内容正常")

            # 检查登录表单
            username_field = await page.query_selector('input[name="username"], input[type="text"]')
            password_field = await page.query_selector('input[name="password"], input[type="password"]')

            if username_field and password_field:
                print("   ✓ 检测到登录表单 (用户名和密码输入框)")
            else:
                print("   ⚠️ 未检测到标准登录表单")

            # 检查是否已经登录（有Renew按钮）
            renew_button = await page.query_selector('#renewSessionBtn')
            if renew_button:
                print("   ✓ 检测到 Renew 按钮 (已登录状态)")

            # 检查错误消息
            print("\n5️⃣ 检查错误消息...")
            error_selectors = ['.error', '.alert', '.alert-danger', '[role="alert"]']
            errors_found = False
            for selector in error_selectors:
                error_elem = await page.query_selector(selector)
                if error_elem:
                    try:
                        error_text = await error_elem.text_content()
                        if error_text.strip():
                            print(f"   ⚠️ 错误: {error_text.strip()[:100]}")
                            errors_found = True
                    except:
                        pass

            if not errors_found:
                print("   ✓ 未检测到错误消息")

            # JavaScript环境检查
            print("\n6️⃣ 检查 JavaScript 环境...")
            js_check = await page.evaluate("""
                () => {
                    return {
                        webdriver: navigator.webdriver,
                        chrome: !!window.chrome,
                        plugins: navigator.plugins.length,
                        languages: navigator.languages.length
                    };
                }
            """)

            print(f"   webdriver: {js_check['webdriver']} (应为 undefined/null/false)")
            print(f"   window.chrome: {js_check['chrome']} (应为 true)")
            print(f"   plugins: {js_check['plugins']} (应 > 0)")
            print(f"   languages: {js_check['languages']} (应 > 0)")

            # 截图
            screenshot_path = base_dir / 'diagnostic_screenshot.png'
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n✓ 截图已保存: {screenshot_path}")

            # 保存HTML
            html_path = base_dir / 'diagnostic_page.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ HTML已保存: {html_path}")

            print("\n" + "=" * 60)
            print("诊断完成！")
            print("=" * 60)
            print("\n浏览器窗口将保持打开30秒，请检查页面状态...")
            print("如果看到登录表单，说明可以正常访问")
            print("如果一直转圈或显示错误，说明被阻止")
            print("=" * 60)

            await asyncio.sleep(30)

        except Exception as e:
            print(f"❌ 访问失败: {e}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(diagnose_mchost())
