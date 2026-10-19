# imgbatch 🖼️

Batch image processing from the command line: **resize · convert · compress · watermark**.
Single file, only depends on Pillow.

图片批量处理命令行工具：缩放、格式转换、压缩、加水印。单文件，仅依赖 Pillow。

## Install

```bash
pip install pillow
# run directly, or:
pip install .
```

## Usage

```bash
# Resize to width 800 (keeps aspect ratio)
imgbatch resize ./photos -w 800 -o ./out

# Convert everything to webp
imgbatch convert ./photos -f webp -o ./out

# Compress with quality 70
imgbatch compress ./photos -q 70 -o ./out

# Text watermark at bottom-right
imgbatch watermark ./photos -t "© Muse" -o ./out
```

Common flags: `-o/--out` output dir (default: same dir with filename suffix),
`-r/--recursive` include subdirectories, `--dry-run` preview without writing.

### resize options
`-w/--width`, `-e/--height`, `--max-size` (default 1920, caps the long edge)

### convert options
`-f/--format` target format (jpg/png/webp), `-q/--quality` (default 85)

### compress options
`-q/--quality` (default 70)

### watermark options
`-t/--text` (required), `--size` (default 36), `--opacity` (default 128),
`--position` tl/tr/bl/br (default br)

## License

MIT
