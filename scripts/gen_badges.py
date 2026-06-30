#!/usr/bin/env python3
"""Generate classic web1.0 88x31 tech-stack buttons (static + animated).

Static styles: raised | sunken | double | flat | shadow | glossy | grey
Animated (GIF): sweep (moving shine) | blink | spin (3D rotating text on black)

Each button: brand-color (or Win9x grey) background, brand icon (simple-icons
SVG in images/badges/_src/), monospace label, retro border/bevel.

Deps: Pillow, JetBrains Mono font, rsvg-convert (icon render; text-only fallback).
GIFs use a shared quantized palette + few frames to stay a few KB each.
Regenerate:  python3 scripts/gen_badges.py
"""
import math
import os
import shutil
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "images", "badges", "_src")
OUT = os.path.join(ROOT, "images", "badges")
FONT_PATH = os.path.expanduser("~/Library/Fonts/JetBrainsMono[wght].ttf")
W, H = 88, 31

# name, label, brand-color, style
# static: raised sunken double flat shadow glossy grey
# anim:   sweep blink spin
STACK = [
    ("python",     "python",     "#3776AB", "sweep"),
    ("fastapi",    "FastAPI",    "#009688", "sweep"),
    ("sqlalchemy", "SQLAlchemy", "#BB2222", "shadow"),
    ("alembic",    "Alembic",    "#6BA81E", "grey"),
    ("typst",      "Typst",      "#239DAD", "spin"),
    ("postgresql", "PostgreSQL", "#336791", "double"),
    ("redis",      "Redis",      "#DC382D", "blink"),
    ("aiogram",    "aiogram",    "#2AABEE", "glossy"),
    ("qdrant",     "Qdrant",     "#DC244C", "raised"),
    ("nginx",      "nginx",      "#009639", "grey"),
    ("langchain",  "LangChain",  "#1C3C3C", "flat"),
    ("langgraph",  "LangGraph",  "#2F6E5B", "raised"),
    ("langfuse",   "Langfuse",   "#0E1117", "sunken"),
    ("docker",     "docker",     "#2496ED", "sweep"),
    ("grafana",    "Grafana",    "#F46800", "blink"),
    ("linux",      "GNU/Linux",  "#000000", "grey"),
    ("git",        "git",        "#F05032", "grey"),
    ("gitlab",     "GitLab CI",  "#E24329", "double"),
    ("django",     "django",     "#0C4B33", "double"),
    ("react",      "React",      "#149ECA", "raised"),
    ("kotlin",     "Kotlin",     "#7F52FF", "glossy"),
    ("grpc",       "gRPC",       "#2D6E7E", "flat"),
    ("kafka",      "Kafka",      "#231F20", "glossy"),
    ("prometheus", "Prometheus", "#E6522C", "blink"),
    ("caddy",      "Caddy",      "#1F88C0", "grey"),
    ("comfyui",    "ComfyUI",    "#6E33C9", "shadow"),
    ("onnx",       "ONNX",       "#5B6770", "grey"),
    ("mongodb",    "MongoDB",    "#47A248", "shadow"),
]

GREY = (192, 192, 192)
HAVE_RSVG = shutil.which("rsvg-convert") is not None


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def shift(rgb, d):
    return tuple(max(0, min(255, v + d)) for v in rgb)


def text_color(bg):
    lum = 0.299*bg[0] + 0.587*bg[1] + 0.114*bg[2]
    return (255, 255, 255) if lum < 150 else (24, 24, 24)


def load_font(label, maxw):
    f = None
    for size in (12, 11, 10, 9, 8, 7):
        f = ImageFont.truetype(FONT_PATH, size)
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
        if f.getbbox(label)[2] <= maxw:
            return f
    return f


def render_icon(name, tint, h=18, _cache={}):
    svg = os.path.join(SRC, f"{name}.svg")
    if not (HAVE_RSVG and os.path.exists(svg)):
        return None
    if svg not in _cache:
        tmp = os.path.join(tempfile.gettempdir(), f"_badge_{name}.png")
        try:
            subprocess.run(["rsvg-convert", "-w", "64", "-h", "64", svg, "-o", tmp],
                           check=True, capture_output=True)
            _cache[svg] = Image.open(tmp).convert("RGBA").copy()
        except Exception:
            _cache[svg] = None
    base = _cache[svg]
    if base is None:
        return None
    scale = h / base.height
    ic = base.resize((max(1, round(base.width*scale)), h), Image.LANCZOS)
    solid = Image.new("RGBA", ic.size, tint + (255,))
    solid.putalpha(ic.split()[3])
    return solid


def grad_overlay(kind, bg):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = ov.load()
    for y in range(H):
        if kind == "shadow":
            t = max(0.0, (y - H*0.55) / (H*0.45)); a = int(95*t*t); col = (0, 0, 0, a)
        else:
            t = max(0.0, 1 - y/(H*0.5)); a = int(60*t); col = (255, 255, 255, a)
        if col[3]:
            for x in range(1, W-1):
                px[x, y] = col
    return ov


def draw_frame(d, style, bg):
    light, dark = shift(bg, 78), shift(bg, -78)
    if style == "grey":
        d.rectangle([0, 0, W-1, H-1], outline=(0, 0, 0))
        d.line([(1, 1), (W-2, 1)], fill=(255, 255, 255))
        d.line([(1, 1), (1, H-2)], fill=(255, 255, 255))
        d.line([(1, H-2), (W-2, H-2)], fill=(128, 128, 128))
        d.line([(W-2, 1), (W-2, H-2)], fill=(128, 128, 128))
        return
    d.rectangle([0, 0, W-1, H-1], outline=(0, 0, 0))
    if style in ("raised", "shadow", "glossy", "sweep", "blink"):
        d.line([(1, 1), (W-2, 1)], fill=light); d.line([(1, 1), (1, H-2)], fill=light)
        d.line([(1, H-2), (W-2, H-2)], fill=dark); d.line([(W-2, 1), (W-2, H-2)], fill=dark)
    elif style == "sunken":
        d.line([(1, 1), (W-2, 1)], fill=dark); d.line([(1, 1), (1, H-2)], fill=dark)
        d.line([(1, H-2), (W-2, H-2)], fill=light); d.line([(W-2, 1), (W-2, H-2)], fill=light)
    elif style == "double":
        d.rectangle([2, 2, W-3, H-3], outline=shift(bg, 90))
    elif style == "flat":
        d.rectangle([1, 1, W-2, H-2], outline=shift(bg, 60))


def render(name, label, bg, tc, tint, style):
    """One static RGBA button frame."""
    img = Image.new("RGBA", (W, H), bg + (255,))
    if style in ("shadow", "glossy"):
        img = Image.alpha_composite(img, grad_overlay(style, bg))
    d = ImageDraw.Draw(img)
    icon = render_icon(name, tint)
    pad_l = 5
    if icon:
        img.paste(icon, (pad_l, (H-icon.height)//2), icon)
        tx0 = pad_l + icon.width + 4
    else:
        tx0 = pad_l
    d = ImageDraw.Draw(img)
    maxw = W - tx0 - 4
    f = load_font(label, maxw)
    b = f.getbbox(label); tw, th = b[2], b[3]-b[1]
    tx = tx0 + max(0, (maxw-tw)//2) if icon else (W-tw)//2
    ty = (H-th)//2 - b[1]
    d.text((tx+1, ty+1), label, font=f, fill=shift(bg, -45))
    d.text((tx, ty), label, font=f, fill=tc)
    draw_frame(d, style, bg)
    return img


def save_gif(path, frames, durs, colors=48):
    rgb = [f.convert("RGB") for f in frames]
    base = rgb[0].quantize(colors=colors, method=Image.MEDIANCUT)
    imgs = [base] + [r.quantize(colors=colors, palette=base, dither=Image.NONE) for r in rgb[1:]]
    imgs[0].save(path, save_all=True, append_images=imgs[1:],
                 duration=durs, loop=0, optimize=True, disposal=1)


def anim_sweep(name, label, bg, tc, tint):
    base = render(name, label, bg, tc, tint, "sweep")
    frames, durs = [], []
    N = 8
    for i in range(N):
        cx = -16 + (W+32) * i/(N-1)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = ov.load()
        for y in range(1, H-1):
            c = cx + (y - H/2)*0.55
            for x in range(1, W-1):
                dd = abs(x - c)
                if dd < 11:
                    a = int(130 * (1 - dd/11))
                    if a > 0:
                        px[x, y] = (255, 255, 255, a)
        frames.append(Image.alpha_composite(base, ov)); durs.append(70)
    return frames, durs


def anim_blink(name, label, bg, tc, tint):
    a = render(name, label, bg, tc, tint, "blink")
    b = render(name, label, shift(bg, 26), (255, 255, 120), tint, "blink")
    d = ImageDraw.Draw(b)
    d.rectangle([2, 2, W-3, H-3], outline=(255, 255, 120))
    return [a, b], [620, 430]


def anim_spin(label, fg):
    """3D Y-axis rotating text on black."""
    f = ImageFont.truetype(FONT_PATH, 18)
    try:
        f.set_variation_by_name("ExtraBold")
    except Exception:
        pass
    bb = f.getbbox(label)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    txt = Image.new("RGBA", (tw+4, th+4), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((2-bb[0], 2-bb[1]), label, font=f, fill=fg+(255,))
    if txt.height > 27:
        s = 27/txt.height
        txt = txt.resize((max(1, int(txt.width*s)), 27), Image.LANCZOS)
    bw, bh = txt.size
    frames, durs = [], []
    N = 10
    for k in range(N):
        th_ = 2*math.pi*k/N
        c = math.cos(th_)
        w = max(2, int(bw*abs(c)))
        sc = txt.resize((w, bh), Image.LANCZOS)
        if c < 0:
            sc = sc.transpose(Image.FLIP_LEFT_RIGHT)
        bright = 0.35 + 0.65*abs(c)
        sc = ImageEnhance.Brightness(sc).enhance(bright)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        canvas.paste(sc, ((W-w)//2, (H-bh)//2), sc)
        dd = ImageDraw.Draw(canvas)
        dd.rectangle([0, 0, W-1, H-1], outline=(40, 40, 40))
        frames.append(canvas); durs.append(95)
    return frames, durs


def make(name, label, bghex, style):
    brand = hx(bghex)
    # resolve panel bg / text / icon tint
    if style == "grey":
        bg, tc, tint = GREY, (10, 10, 10), brand
    else:
        bg = brand; tc = text_color(bg); tint = tc

    if style == "sweep":
        fr, du = anim_sweep(name, label, bg, tc, tint)
        save_gif(os.path.join(OUT, f"{name}.gif"), fr, du)
    elif style == "blink":
        fr, du = anim_blink(name, label, bg, tc, tint)
        save_gif(os.path.join(OUT, f"{name}.gif"), fr, du)
    elif style == "spin":
        fr, du = anim_spin(label, brand)
        save_gif(os.path.join(OUT, f"{name}.gif"), fr, du, colors=32)
    else:
        render(name, label, bg, tc, tint, style).convert("RGB").save(
            os.path.join(OUT, f"{name}.png"))


def main():
    if not HAVE_RSVG:
        print("WARN: rsvg-convert missing -> text-only buttons")
    anim = {n: s for n, _, _, s in STACK if s in ("sweep", "blink", "spin")}
    # drop stale png for now-animated names
    for n, s in anim.items():
        p = os.path.join(OUT, f"{n}.png")
        if os.path.exists(p):
            os.remove(p)
    for n, l, c, s in STACK:
        make(n, l, c, s)
    print(f"generated {len(STACK)} buttons ({len(anim)} gif) -> {OUT}")


if __name__ == "__main__":
    main()
