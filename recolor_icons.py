from PIL import Image
import os
import shutil

ICON_DIR = r"D:\ddx\TrayStatus\Icons"
DARK_DIR = os.path.join(ICON_DIR, "Dark Icons")

BACKUP_DIR = os.path.join(ICON_DIR, "Original Backup")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Color definitions
YELLOW_ON = (255, 220, 0)   # Bright yellow for CapsLock ON
GRAY_OFF = (128, 128, 128)  # Gray for CapsLock OFF

TARGET_COLORS = {
    "CapsLockOn.ico": YELLOW_ON,
    "CapsLockOff.ico": GRAY_OFF,
}

ALL_FOLDERS = [
    "Dark Icons",
    "Dark Icons with Green",
    "Light Icons",
    "Light Icons with Green",
    "Old Icons",
]


def recolor_ico(src_path, dst_path, target_color):
    """Recolor all frames: use alpha as mask, fill visible areas with target_color."""
    img = Image.open(src_path)
    frames = []
    sizes = []

    try:
        while True:
            w, h = img.size
            rgba = img.convert("RGBA")
            r, g, b, a_band = rgba.split()
            # Fill entire image with target color
            colored = Image.new("RGBA", (w, h), target_color + (255,))
            # Apply original alpha as mask
            colored.putalpha(a_band)

            frames.append(colored.copy())
            sizes.append((w, h))
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        print(f"  WARNING: No frames found in {src_path}")
        return

    # Save as ICO with all sizes
    frames[0].save(
        dst_path,
        format="ICO",
        sizes=[(s[0], s[1]) for s in sizes],
    )
    print(f"  -> Saved ({', '.join(f'{w}x{h}' for w, h in sizes)})")


def main():
    for folder in ALL_FOLDERS:
        folder_path = os.path.join(ICON_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        print(f"\nProcessing: {folder}")
        for filename, color in TARGET_COLORS.items():
            src = os.path.join(folder_path, filename)
            if not os.path.isfile(src):
                print(f"  {filename}: NOT FOUND, skipping")
                continue

            # Backup original if not already backed up
            backup = os.path.join(BACKUP_DIR, f"{folder}_{filename}")
            if not os.path.isfile(backup):
                shutil.copy2(src, backup)
                print(f"  Backed up: {filename}")

            recolor_ico(src, src, color)

    print(f"\nDone! Originals backed up to: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
