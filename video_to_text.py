"""
视频 → 文字全自动流程
支持: 抖音链接(自动去水印) / 普通视频直链 / 本地文件
用法: python video_to_text.py <URL或路径>
"""
import sys
import os
import json
import time
import tempfile
import subprocess
import shutil
import asyncio


async def download_douyin(url, output_path):
    """通过 seekin.ai 解析抖音视频并下载"""
    from playwright.async_api import async_playwright
    import requests as req

    api_result = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Intercept the API response
        async def on_response(response):
            if "api.seekin.ai/ikool/media/download" in response.url:
                try:
                    api_result["data"] = await response.json()
                except Exception:
                    pass

        page.on("response", on_response)

        print("  打开 seekin.ai ...")
        await page.goto("https://www.seekin.ai/zh/douyin-downloader/",
                        wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        print(f"  输入链接...")
        await page.fill("#video-url", url)
        await page.wait_for_timeout(500)

        print("  点击解析...")
        btn = page.locator("button:has-text('立即下载')").first
        await btn.click()
        await page.wait_for_timeout(15000)

        await browser.close()

    if not api_result.get("data"):
        print("  ERROR: 未获取到 API 响应")
        return False

    data = api_result["data"]
    title = data.get("data", {}).get("title", "Unknown")
    medias = data.get("data", {}).get("medias", [])

    if not medias:
        print("  ERROR: 未找到视频地址")
        return False

    print(f"  视频: {title[:60]}")

    # Pick 720p or 1080p, fallback to first
    choice = medias[0]
    for m in medias:
        fmt = m.get("format") or ""
        if "720p" in fmt:
            choice = m
            break
    for m in medias:
        fmt = m.get("format") or ""
        if "1080p" in fmt:
            choice = m
            break

    video_url = choice["url"]
    print(f"  下载: {choice['format']} ({choice['fileSize'] / 1024 / 1024:.1f} MB)")

    resp = req.get(video_url, stream=True, timeout=180,
                   headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)

    return os.path.isfile(output_path) and os.path.getsize(output_path) > 50000


def download_direct(url, output_path):
    """下载普通视频直链"""
    import requests as req
    try:
        resp = req.get(url, stream=True, timeout=180,
                       headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
    except Exception:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "-f", "best", "-o", output_path,
             "--no-playlist", "--socket-timeout", "30", url],
            capture_output=True, text=True, timeout=180,
        )
    return os.path.isfile(output_path) and os.path.getsize(output_path) > 50000


def transcribe(video_path):
    """Whisper 语音转文字"""
    print("[2/3] 语音转文字 (Whisper)...")
    t0 = time.time()

    from faster_whisper import WhisperModel

    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_path, language="zh", beam_size=5)
    lines = []
    for seg in segments:
        line = f"[{seg.start:.0f}s] {seg.text.strip()}"
        lines.append(line)
        print(f"  {line}")
        if seg.start > 300:
            break

    elapsed = time.time() - t0
    print(f"  识别完成 ({elapsed:.0f}s)")
    return lines


def main():
    if len(sys.argv) < 2:
        print("用法: python video_to_text.py <视频URL或本地路径>")
        print("  - 抖音链接: python video_to_text.py https://v.douyin.com/xxx/")
        print("  - 本地文件: python video_to_text.py d:/downloads/video.mp4")
        free_sites = ["seekin.ai", "douyin-downloader"]
        sys.exit(1)

    arg = sys.argv[1]
    tmpdir = tempfile.mkdtemp(prefix="video_")
    video_path = os.path.join(tmpdir, "video.mp4")

    try:
        print("=" * 50)
        print("[1/3] 获取视频...")

        if os.path.isfile(arg):
            shutil.copy2(arg, video_path)
            print(f"  使用本地文件")
        elif "douyin.com" in arg or "iesdouyin" in arg:
            ok = asyncio.run(download_douyin(arg, video_path))
            if not ok:
                print("  ERROR: 解析失败")
                sys.exit(1)
        else:
            ok = download_direct(arg, video_path)
            if not ok:
                print("  ERROR: 下载失败")
                sys.exit(1)

        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"  视频就绪 ({size_mb:.1f} MB)")

        lines = transcribe(video_path)

        print("=" * 50)
        print("识别结果:")
        print("=" * 50)
        if lines:
            for line in lines:
                print(line)
        else:
            print("(未识别到语音)")
        print("=" * 50)

    finally:
        print("[3/3] 清理...")
        try:
            os.remove(video_path)
            os.rmdir(tmpdir)
            print("  已删除临时文件")
        except Exception:
            pass


if __name__ == "__main__":
    main()
