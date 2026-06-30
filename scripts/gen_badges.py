#!/usr/bin/env python3
"""Generate classic web1.0 88x31 tech-stack buttons.

Each button: brand-color background, brand icon (simple-icons SVG in
images/badges/_src/), monospace label, and one of several retro border/bevel
styles (raised, sunken, double frame, flat, bottom half-shadow, glossy top).

Deps: Pillow, JetBrains Mono font, rsvg-convert (for icon rendering; falls
back to text-only buttons when missing). Regenerate with:  python3 scripts/gen_badges.py
"""
import os
import shutil
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "images", "badges", "_src")
OUT = os.path.join(ROOT, "images", "badges")
FONT_PATH = os.path.expanduser("~/Library/Fonts/JetBrainsMono[wght].ttf")
W, H = 88, 31

# name, label, bg, style   (icon = _src/<name>.svg if present)
# styles: raised | sunken | double | flat | shadow | glossy
STACK = [
    ("python",     "python",     "#3776AB", "raised"),
    ("fastapi",    "FastAPI",    "#009688", "glossy"),
    ("django",     "django",     "#0C4B33", "double"),
    ("sqlalchemy", "SQLAlchemy", "#BB2222", "shadow"),
    ("grpc",       "gRPC",       "#2D6E7E", "flat"),
    ("postgresql", "PostgreSQL", "#336791", "sunken"),
    ("redis",      "Redis",      "#DC382D", "raised"),
    ("mongodb",    "MongoDB",    "#47A248", "shadow"),
    ("qdrant",     "Qdrant",     "#DC244C", "double"),
    ("kafka",      "Kafka",      "#231F20", "glossy"),
    ("langchain",  "LangChain",  "#1C3C3C", "flat"),
    ("langgraph",  "LangGraph",  "#2F6E5B", "raised"),
    ("langfuse",   "Langfuse",   "#0E1117", "sunken"),
    ("comfyui",    "ComfyUI",    "#6E33C9", "shadow"),
    ("onnx",       "ONNX",       "#5B6770", "double"),
    ("docker",     "docker",     "#2496ED", "glossy"),
    ("linux",      "GNU/Linux",  "#000000", "raised"),
    ("nginx",      "nginx",      "#009639", "flat"),
    ("caddy",      "Caddy",      "#1F88C0", "sunken"),
    ("git",        "git",        "#F05032", "shadow"),
    ("gitlab",     "GitLab CI",  "#E24329", "double"),
    ("prometheus", "Prometheus", "#E6522C", "raised"),
    ("grafana",    "Grafana",    "#F46800", "glossy"),
    ("aiogram",    "aiogram",    "#2AABEE", "flat"),
]

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
    """Return RGBA icon tinted, scaled to height h, or None."""
    svg = os.path.join(SRC, f"{name}.svg")
    if not (HAVE_RSVG and os.path.exists(svg)):
        return None
    key = svg
    if key not in _cache:
        tmp = os.path.join(tempfile.gettempdir(), f"_badge_{name}.png")
        try:
            subprocess.run(["rsvg-convert", "-w", "64", "-h", "64", svg, "-o", tmp],
                           check=True, capture_output=True)
            _cache[key] = Image.open(tmp).convert("RGBA").copy()
        except Exception:
            _cache[key] = None
    base = _cache[key]
    if base is None:
        return None
    scale = h / base.height
    ic = base.resize((max(1, round(base.width*scale)), h), Image.LANCZOS)
    solid = Image.new("RGBA", ic.size, tint + (255,))
    solid.putalpha(ic.split()[3])
    return solid


def grad_overlay(kind, bg):
    """RGBA overlay for shadow/glossy styles."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = ov.load()
    for y in range(H):
        if kind == "shadow":          # darken toward bottom third
            t = max(0.0, (y - H*0.55) / (H*0.45))
            a = int(95 * t * t)
            col = (0, 0, 0, a)
        else:                          # glossy: light band top half
            t = max(0.0, 1 - y / (H*0.5))
            a = int(60 * t)
            col = (255, 255, 255, a)
        if col[3]:
            for x in range(1, W-1):
                px[x, y] = col
    return ov


def draw_frame(d, style, bg):
    light, dark = shift(bg, 78), shift(bg, -78)
    d.rectangle([0, 0, W-1, H-1], outline=(0, 0, 0))
    if style in ("raised", "shadow", "glossy"):
        d.line([(1, 1), (W-2, 1)], fill=light)
        d.line([(1, 1), (1, H-2)], fill=light)
        d.line([(1, H-2), (W-2, H-2)], fill=dark)
        d.line([(W-2, 1), (W-2, H-2)], fill=dark)
    elif style == "sunken":
        d.line([(1, 1), (W-2, 1)], fill=dark)
        d.line([(1, 1), (1, H-2)], fill=dark)
        d.line([(1, H-2), (W-2, H-2)], fill=light)
        d.line([(W-2, 1), (W-2, H-2)], fill=light)
    elif style == "double":
        d.rectangle([2, 2, W-3, H-3], outline=shift(bg, 90))
    elif style == "flat":
        d.rectangle([1, 1, W-2, H-2], outline=shift(bg, 60))


def make(name, label, bghex, style):
    bg = hx(bghex)
    tc = text_color(bg)
    img = Image.new("RGBA", (W, H), bg + (255,))

    if style in ("shadow", "glossy"):
        img = Image.alpha_composite(img, grad_overlay(style, bg))

    d = ImageDraw.Draw(img)
    icon = render_icon(name, tc)
    pad_l = 5
    if icon:
        iy = (H - icon.height) // 2
        img.paste(icon, (pad_l, iy), icon)
        tx0 = pad_l + icon.width + 4
    else:
        tx0 = pad_l
    d = ImageDraw.Draw(img)

    maxw = W - tx0 - 4
    f = load_font(label, maxw)
    bbox = f.getbbox(label)
    tw, th = bbox[2], bbox[3] - bbox[1]
    # center text in remaining area when no icon, else left-align after icon
    if icon:
        tx = tx0 + max(0, (maxw - tw)//2)
    else:
        tx = (W - tw)//2
    ty = (H - th)//2 - bbox[1]
    d.text((tx+1, ty+1), label, font=f, fill=shift(bg, -45))
    d.text((tx, ty), label, font=f, fill=tc)

    draw_frame(d, style, bg)
    img.convert("RGB").save(os.path.join(OUT, f"{name}.png"))


def main():
    if not HAVE_RSVG:
        print("WARN: rsvg-convert missing -> text-only buttons")
    for n, l, c, s in STACK:
        make(n, l, c, s)
    print(f"generated {len(STACK)} buttons -> {OUT}")


if __name__ == "__main__":
    main()
