import subprocess
import shutil
from pathlib import Path
from PIL import Image

# alpha 阈值：低于此值的像素视为透明，越大裁得越激进
ALPHA_THRESHOLD = 128


def trim_transparent(image_path: str) -> None:
    path = Path(image_path.strip().strip("'\""))

    if not path.exists():
        print(f"[错误] 文件不存在: {path}")
        return

    if path.suffix.lower() != ".png":
        print(f"[错误] 仅支持 PNG 文件: {path}")
        return

    img = Image.open(path).convert("RGBA")

    alpha = img.getchannel("A").point(lambda x: 255 if x >= ALPHA_THRESHOLD else 0)
    bbox = alpha.getbbox()
    if bbox is None:
        print("[错误] 图片完全透明，无内容可裁剪。")
        return

    cropped = img.crop(bbox)

    output_path = path.with_stem(path.stem + "-cut")
    cropped.save(output_path, "PNG")

    print(f"[完成] 已裁剪并保存到: {output_path}")
    print(f"       原始尺寸: {img.size[0]}x{img.size[1]}  →  裁剪后: {cropped.size[0]}x{cropped.size[1]}")

    # 复制到剪贴板
    copied = False

    # Wayland: wl-copy
    if not copied and shutil.which("wl-copy"):
        try:
            with open(output_path, "rb") as f:
                subprocess.run(["wl-copy", "--type", "image/png"], stdin=f, check=True)
            copied = True
            print("[剪贴板] 已通过 wl-copy 复制到剪贴板。")
        except subprocess.CalledProcessError:
            pass

    # X11: xclip
    if not copied and shutil.which("xclip"):
        try:
            with open(output_path, "rb") as f:
                subprocess.run(
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-i"],
                    stdin=f,
                    check=True,
                )
            copied = True
            print("[剪贴板] 已通过 xclip 复制到剪贴板。")
        except subprocess.CalledProcessError:
            pass

    # X11: xdotool fallback via xclip alternative: xdg-open不适合，跳过
    if not copied:
        print("[剪贴板] 未找到 wl-copy 或 xclip，跳过剪贴板复制。")
        print("         可安装: sudo apt install wl-clipboard  或  sudo apt install xclip")


def main():
    print("=== Transparent Cut ===")
    print("将 PNG 图片路径拖入此窗口后按回车，输入 q 退出。\n")

    while True:
        try:
            raw = input("图片路径> ").strip().strip("'\"")
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break

        if raw.lower() in ("q", "quit", "exit"):
            print("已退出。")
            break

        if not raw:
            continue

        trim_transparent(raw)
        print()


if __name__ == "__main__":
    main()
