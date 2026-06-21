import asyncio
from playwright.async_api import async_playwright

VIDEO_URL = "https://www.douyin.com/video/7634849134133906715"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        print("Opening Douyin video...")
        await page.goto(VIDEO_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(8000)  # wait for video player to load

        # Try to extract title
        title = await page.title()
        print(f"Page title: {title}")

        # Look for video description / caption elements
        selectors = [
            '[data-e2e="video-desc"]',
            '[data-e2e="video-title"]',
            ".video-info-detail",
            ".xgplayer-text-track",
            "[class*='desc']",
            "[class*='title']",
            "[class*='caption']",
            "[class*='subtitle']",
            "video",
            ".swiper-slide",
        ]

        for sel in selectors:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    text = await el.inner_text()
                    if text and text.strip():
                        print(f"[{sel}]: {text.strip()[:200]}")
            except Exception:
                pass

        # Try to get video element info
        try:
            video = await page.query_selector("video")
            if video:
                src = await video.get_attribute("src")
                print(f"Video src: {src}")
                subtitles = await video.get_attribute("textTracks")
                print(f"Subtitles: {subtitles}")
        except Exception:
            pass

        # Grab all visible text
        try:
            body_text = await page.inner_text("body")
            print("\n--- Page text content (first 2000 chars) ---")
            print(body_text[:2000])
        except Exception:
            pass

        # Take a screenshot for visual inspection
        await page.screenshot(path="d:/ceshi/douyin_screenshot.png", full_page=False)
        print("\nScreenshot saved: d:/ceshi/douyin_screenshot.png")

        print("\nKeeping browser open for 10 seconds... close manually if needed.")
        await page.wait_for_timeout(10000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
