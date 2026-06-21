import pygetwindow as gw

print("=== All visible windows (filtered by size > 200x200) ===\n")
for w in gw.getAllWindows():
    if w.title and w.width > 200 and w.height > 200:
        print(f"  [{w.width}x{w.height}] \"{w.title}\"")

print("\n=== All windows with 'WeChat' or Chinese chars ===\n")
for w in gw.getAllWindows():
    if w.title:
        try:
            if "微信" in w.title or "WeChat" in w.title or "chat" in w.title.lower():
                print(f"  [{w.width}x{w.height}] \"{w.title}\"")
        except Exception:
            pass

print("\n=== All windows (any size, has title) ===\n")
for w in gw.getAllWindows():
    if w.title and w.title.strip():
        print(f"  [{w.width}x{w.height}] \"{w.title}\"")
