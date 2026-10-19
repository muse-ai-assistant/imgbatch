#!/usr/bin/env python3
"""imgbatch - 批量图片处理命令行工具
resize / convert / compress / watermark，一条命令搞定一堆图。
只依赖 Pillow。
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("缺少依赖，请先运行: pip install -r requirements.txt")

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}


def iter_images(paths, recursive):
    seen = set()
    for p in paths:
        p = Path(p)
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                yield p
        elif p.is_dir():
            it = p.rglob("*") if recursive else p.glob("*")
            for f in sorted(it):
                if f.is_file() and f.suffix.lower() in IMG_EXTS:
                    rp = f.resolve()
                    if rp not in seen:
                        seen.add(rp)
                        yield f
        else:
            print(f"跳过(不存在): {p}", file=sys.stderr)


def out_path(src, outdir, suffix=None, name_suffix=""):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    name = src.stem + name_suffix + (suffix or src.suffix)
    return outdir / name


def do_resize(args):
    n = 0
    for src in iter_images(args.inputs, args.recursive):
        dst = out_path(src, args.out or src.parent,
                       name_suffix="" if args.out else "_resized")
        if args.dry_run:
            print(f"[dry] resize {src} -> {dst}")
            n += 1
            continue
        img = Image.open(src).convert("RGB")
        w, h = img.size
        if args.width and args.height:
            nw, nh = args.width, args.height
        elif args.width:
            nw, nh = args.width, round(h * args.width / w)
        elif args.height:
            nh, nw = args.height, round(w * args.height / h)
        else:
            scale = args.max_size / max(w, h) if max(w, h) > args.max_size else 1
            nw, nh = round(w * scale), round(h * scale)
        img.resize((nw, nh), Image.LANCZOS).save(dst)
        print(f"{src.name} {w}x{h} -> {nw}x{nh}")
        n += 1
    print(f"完成 {n} 张")


def do_convert(args):
    fmt = args.format.lower().lstrip(".")
    n = 0
    for src in iter_images(args.inputs, args.recursive):
        dst = out_path(src, args.out or src.parent, suffix="." + fmt,
                       name_suffix="" if args.out else "_converted")
        if args.dry_run:
            print(f"[dry] convert {src} -> {dst}")
            n += 1
            continue
        img = Image.open(src).convert("RGB")
        kw = {"quality": args.quality} if fmt in ("jpg", "jpeg", "webp") else {}
        img.save(dst, **kw)
        print(f"{src.name} -> {dst.name}")
        n += 1
    print(f"完成 {n} 张")


def do_compress(args):
    n = 0
    for src in iter_images(args.inputs, args.recursive):
        dst = out_path(src, args.out or src.parent,
                       name_suffix="" if args.out else "_compressed")
        if args.dry_run:
            print(f"[dry] compress {src} -> {dst}")
            n += 1
            continue
        img = Image.open(src)
        before = src.stat().st_size
        if dst.suffix.lower() in (".jpg", ".jpeg"):
            img.convert("RGB").save(dst, quality=args.quality, optimize=True)
        elif dst.suffix.lower() == ".png":
            img.save(dst, optimize=True)
        else:
            img.convert("RGB").save(dst.with_suffix(".jpg"),
                                    quality=args.quality, optimize=True)
            dst = dst.with_suffix(".jpg")
        after = dst.stat().st_size
        print(f"{src.name}: {before//1024}KB -> {after//1024}KB")
        n += 1
    print(f"完成 {n} 张")


def do_watermark(args):
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", args.size)
    except OSError:
        font = ImageFont.load_default()
    n = 0
    for src in iter_images(args.inputs, args.recursive):
        dst = out_path(src, args.out or src.parent,
                       name_suffix="" if args.out else "_wm")
        if args.dry_run:
            print(f"[dry] watermark {src} -> {dst}")
            n += 1
            continue
        img = Image.open(src).convert("RGBA")
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bbox = d.textbbox((0, 0), args.text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        margin = 12
        pos = {"br": (img.width - tw - margin, img.height - th - margin),
               "bl": (margin, img.height - th - margin),
               "tr": (margin, margin),
               "tl": (margin, margin)}[args.position]
        # bl 修正为左下
        if args.position == "bl":
            pos = (margin, img.height - th - margin)
        d.text(pos, args.text, font=font, fill=(255, 255, 255, args.opacity))
        out = Image.alpha_composite(img, layer).convert("RGB")
        out.save(dst)
        print(f"{src.name} -> {dst.name}")
        n += 1
    print(f"完成 {n} 张")


def main():
    ap = argparse.ArgumentParser(prog="imgbatch", description="批量图片处理: resize/convert/compress/watermark")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("inputs", nargs="+", help="图片文件或目录")
        p.add_argument("-o", "--out", default=None, help="输出目录(默认原地,文件名加后缀)")
        p.add_argument("-r", "--recursive", action="store_true", help="递归子目录")
        p.add_argument("--dry-run", action="store_true", help="只预览不执行")

    p = sub.add_parser("resize", help="批量缩放")
    common(p)
    p.add_argument("-w", "--width", type=int)
    p.add_argument("-e", "--height", type=int)
    p.add_argument("--max-size", type=int, default=1920, help="最长边上限(默认1920)")
    p.set_defaults(func=do_resize)

    p = sub.add_parser("convert", help="批量格式转换")
    common(p)
    p.add_argument("-f", "--format", default="webp", help="目标格式(jpg/png/webp)")
    p.add_argument("-q", "--quality", type=int, default=85)
    p.set_defaults(func=do_convert)

    p = sub.add_parser("compress", help="批量压缩")
    common(p)
    p.add_argument("-q", "--quality", type=int, default=70)
    p.set_defaults(func=do_compress)

    p = sub.add_parser("watermark", help="批量加文字水印")
    common(p)
    p.add_argument("-t", "--text", required=True)
    p.add_argument("--size", type=int, default=36)
    p.add_argument("--opacity", type=int, default=128)
    p.add_argument("--position", default="br", choices=["tl", "tr", "bl", "br"])
    p.set_defaults(func=do_watermark)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
