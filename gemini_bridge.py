"""
Gemini 桥接 — 全自动图片上传 + 提问
用法: python gemini_bridge.py "你的问题" [图片路径]
"""
import asyncio
import sys
import os
import json
import base64
import time

PROFILE = os.path.join(os.path.dirname(__file__), ".gemini_profile")


async def upload_image(page, image_path):
    """Upload via base64 DataTransfer paste event."""
    with open(image_path, "rb") as f:
        img_data = f.read()
    b64_data = base64.b64encode(img_data).decode()
    mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
    filename = os.path.basename(image_path)

    result = await page.evaluate("""
        async (args) => {
            const [b64, mime, name] = args;
            const byteChars = atob(b64);
            const bytes = new Uint8Array(byteChars.length);
            for (let i = 0; i < byteChars.length; i++) bytes[i] = byteChars.charCodeAt(i);
            const blob = new Blob([bytes], {type: mime});
            const file = new File([blob], name, {type: mime});
            const dt = new DataTransfer();
            dt.items.add(file);
            const target = document.querySelector('rich-textarea')
                        || document.querySelector('div[contenteditable="true"]')
                        || document.body;
            target.dispatchEvent(new ClipboardEvent('paste', {
                clipboardData: dt, bubbles: true, cancelable: true
            }));
            return 'paste -> ' + target.tagName;
        }
    """, [b64_data, mime, filename])
    print(f"  {result}")
    return True


async def main():
    if len(sys.argv) < 2:
        print("用法: python gemini_bridge.py \"问题\" [图片路径]")
        sys.exit(1)

    question = sys.argv[1]
    image_path = sys.argv[2] if len(sys.argv) > 2 else None
    os.makedirs(PROFILE, exist_ok=True)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            PROFILE,
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        page = await browser.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1000)

        # ── upload ──
        if image_path and os.path.isfile(image_path):
            print(f"上传: {os.path.basename(image_path)}")
            textarea = page.locator('div[contenteditable="true"]').first
            await textarea.click(force=True, timeout=5000)
            await page.wait_for_timeout(500)
            await upload_image(page, image_path)
            await page.wait_for_timeout(5000)

        # ── type ──
        print(f"发送: {question[:60]}...")
        textarea = page.locator('div[contenteditable="true"]').first
        await textarea.click(force=True, timeout=5000)
        await page.wait_for_timeout(300)
        await textarea.fill("")
        await page.wait_for_timeout(200)
        await textarea.type(question, delay=10)
        await page.wait_for_timeout(500)

        # ── send ──
        for sel in ['button[aria-label="プロンプトを送信"]', 'button[aria-label="发送消息"]', 'button[aria-label*="send" i]']:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click(force=True)
                break
        else:
            await page.keyboard.press("Enter")

        print("等待回复...")
        await page.wait_for_timeout(20000)
        for _ in range(120):
            if await page.locator('button[aria-label*="停止"]').count() == 0:
                break
            await page.wait_for_timeout(1500)

        text = await page.inner_text("body")
        noise = ["Gemini", "PRO", "ノートブック", "ツール", "高速モード",
                 "一時的なチャット", "設定とヘルプ", "Gemini との会話",
                 "作成したもの", "新しいウィンドウで開く",
                 "は 最近のチャット", "Gemini アプリ アクティビティ",
                 "ファイルを追加", "Personalization in progress",
                 "クエリが正常に完了しました", "は AI であり",
                 "Google Terms", "Google プライバシーポリシー"]
        for n in noise:
            text = text.replace(n, "")

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        q_pos = "\n".join(lines).find(question[:15])
        if q_pos >= 0:
            text = "\n".join(lines)[q_pos:]

        print("=" * 50)
        print(text[:8000])
        print("=" * 50)
        print("=== Gemini 回复结束 ===")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
