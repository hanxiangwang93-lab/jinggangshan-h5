import pyautogui
import pygetwindow as gw
import pyperclip
import time
import os

MESSAGE = "1234567"
CONTACT = "文件传输助手"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


def find_main_window():
    """查找微信主窗口（尺寸 > 400x400）。"""
    for w in gw.getAllWindows():
        if w.title and w.width > 400 and w.height > 400:
            if "微信" in w.title or "WeChat" in w.title:
                return w
            # 也检查乱码形式 (Mojibake of 微信 = Î¢ÐÅ / ΢��)
            for pattern in ["΢", "Î", "Å", "Ð", "微信"]:
                if pattern in w.title:
                    return w
    return None


def main():
    # 1. 用热键唤出微信主窗口
    print("[1/7] Bringing up WeChat with Ctrl+Alt+W...")
    pyautogui.hotkey('ctrl', 'alt', 'w')
    time.sleep(2)

    win = find_main_window()
    if not win:
        # 再试一次
        pyautogui.hotkey('ctrl', 'alt', 'w')
        time.sleep(2)
        win = find_main_window()

    if not win:
        # 列出可能的窗口
        print("  Cannot find WeChat main window. Available large windows:")
        for w in gw.getAllWindows():
            if w.title and w.width > 400:
                print(f"    [{w.width}x{w.height}] \"{w.title}\"")
        print("Please open WeChat manually and try again.")
        return

    print(f"  Found: [{win.width}x{win.height}] \"{win.title}\"")

    # 2. 激活并前置
    print("[2/7] Activating window...")
    try:
        win.restore()
        time.sleep(0.3)
        win.activate()
        time.sleep(0.5)
    except Exception:
        pass

    # 3. 搜索联系人
    print("[3/7] Ctrl+F to search...")
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.8)

    print(f"[4/7] Pasting contact name...")
    pyperclip.copy(CONTACT)
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.2)

    # 4. 搜索后，Tab 跳到结果区 → 只按一次 Down 选第一个联系人 → 回车
    print("[5/7] Selecting contact from search results...")
    pyautogui.press('tab')    # 从搜索框跳到结果面板
    time.sleep(0.3)
    pyautogui.press('tab')    # 跳到「联系人」分类
    time.sleep(0.3)
    pyautogui.press('down')   # 选第一个联系人
    time.sleep(0.3)
    pyautogui.press('enter')  # 打开对话
    time.sleep(1.0)

    # 5. 输入消息
    print(f"[6/7] Typing message...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyperclip.copy(MESSAGE)
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.3)

    # 6. 发送
    print("[7/7] Sending...")
    pyautogui.press('enter')

    print("Done! Check your WeChat.")


if __name__ == "__main__":
    main()
