#!/usr/bin/env python3
"""Generate classic web1.0 88x31 tech-stack buttons (static + animated).

Static styles : raised | sunken | double | flat | shadow | glossy | grey
Animated (GIF): sweep (moving shine) | blink | marquee (scrolling text)
                barber (under-construction stripes) | spin (true-3D rotating text)

Per-badge typeface (FONTS) gives ransom-note variety. Brand icons from
simple-icons SVG in images/badges/_src/. GIFs use a shared quantized palette +
few frames to stay a few KB each.

Deps: Pillow, macOS system fonts + JetBrains Mono, rsvg-convert (text-only fallback).
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
W, H = 88, 31
GREY = (192, 192, 192)
SUP = "/System/Library/Fonts/Supplemental/"

# font key -> (path, variation-name-or-None)
FONTS = {
    "jb":        (os.path.expanduser("~/Library/Fonts/JetBrainsMono[wght].ttf"), "Bold"),
    "monaco":    ("/System/Library/Fonts/Monaco.ttf", None),
    "menlo":     ("/System/Library/Fonts/Menlo.ttc", None),
    "impact":    (SUP + "Impact.ttf", None),
    "ablack":    (SUP + "Arial Black.ttf", None),
    "courier":   (SUP + "Courier New Bold.ttf", None),
    "comic":     (SUP + "Comic Sans MS Bold.ttf", None),
    "times":     (SUP + "Times New Roman Bold.ttf", None),
    "georgia":   (SUP + "Georgia Bold.ttf", None),
    "trebuchet": (SUP + "Trebuchet MS Bold.ttf", None),
    "verdana":   (SUP + "Verdana Bold.ttf", None),
}

# name, label, brand-color, style, font
STACK = [
    ("python",     "python",     "#3776AB", "cute",    "comic"),
    ("fastapi",    "FastAPI",    "#009688", "sweep",   "menlo"),
    ("sqlalchemy", "SQLAlchemy", "#BB2222", "shadow",  "times"),
    ("alembic",    "Alembic",    "#6BA81E", "ribbon",  "georgia"),
    ("typst",      "Typst",      "#239DAD", "spin",    "ablack"),
    ("postgresql", "PostgreSQL", "#336791", "double",  "trebuchet"),
    ("redis",      "Redis",      "#DC382D", "cute",    "comic"),
    ("aiogram",    "aiogram",    "#2AABEE", "cute",    "comic"),
    ("qdrant",     "Qdrant",     "#DC244C", "marquee", "verdana"),
    ("nginx",      "nginx",      "#009639", "grey",    "courier"),
    ("langchain",  "LangChain",  "#1C3C3C", "flat",    "georgia"),
    ("langgraph",  "LangGraph",  "#2F6E5B", "marquee", "trebuchet"),
    ("langfuse",   "Langfuse",   "#0E1117", "sunken",  "jb"),
    ("docker",     "docker",     "#2496ED", "logospin", "monaco"),
    ("grafana",    "Grafana",    "#F46800", "blink",   "impact"),
    ("linux",      "GNU/Linux",  "#000000", "grey",    "courier"),
    ("git",        "git",        "#F05032", "ribbon",  "monaco"),
    ("gitlab",     "GitLab CI",  "#E24329", "barber",  "ablack"),
    ("django",     "django",     "#0C4B33", "double",  "georgia"),
    ("react",      "React",      "#149ECA", "raised",  "jb"),
    ("kotlin",     "Kotlin",     "#7F52FF", "glossy",  "verdana"),
    ("grpc",       "gRPC",       "#2D6E7E", "flat",    "courier"),
    ("kafka",      "Kafka",      "#231F20", "barber",  "impact"),
    ("prometheus", "Prometheus", "#E6522C", "blink",   "ablack"),
    ("caddy",      "Caddy",      "#1F88C0", "grey",    "trebuchet"),
    ("comfyui",    "ComfyUI",    "#6E33C9", "marquee", "comic"),
    ("onnx",       "ONNX",       "#5B6770", "grey",    "menlo"),
    ("mongodb",    "MongoDB",    "#47A248", "cute",    "comic"),
]
ANIM = {"sweep", "blink", "marquee", "barber", "spin", "cute", "logospin"}
HAVE_RSVG = shutil.which("rsvg-convert") is not None


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def shift(rgb, d):
    return tuple(max(0, min(255, v + d)) for v in rgb)


def text_color(bg):
    return (255, 255, 255) if 0.299*bg[0]+0.587*bg[1]+0.114*bg[2] < 150 else (24, 24, 24)


def font_at(key, size):
    path, var = FONTS[key]
    f = ImageFont.truetype(path, size)
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


def fit_font(key, label, maxw, maxh=23):
    f = None
    for size in range(16, 6, -1):
        f = font_at(key, size)
        b = f.getbbox(label)
        if (b[2]-b[0]) <= maxw and (b[3]-b[1]) <= maxh:
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
            t = max(0.0, (y - H*0.55)/(H*0.45)); a = int(95*t*t); col = (0, 0, 0, a)
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
        d.line([(1, 1), (W-2, 1)], fill=(255, 255, 255)); d.line([(1, 1), (1, H-2)], fill=(255, 255, 255))
        d.line([(1, H-2), (W-2, H-2)], fill=(128, 128, 128)); d.line([(W-2, 1), (W-2, H-2)], fill=(128, 128, 128))
        return
    d.rectangle([0, 0, W-1, H-1], outline=(0, 0, 0))
    if style in ("raised", "shadow", "glossy", "sweep", "blink", "marquee"):
        d.line([(1, 1), (W-2, 1)], fill=light); d.line([(1, 1), (1, H-2)], fill=light)
        d.line([(1, H-2), (W-2, H-2)], fill=dark); d.line([(W-2, 1), (W-2, H-2)], fill=dark)
    elif style == "sunken":
        d.line([(1, 1), (W-2, 1)], fill=dark); d.line([(1, 1), (1, H-2)], fill=dark)
        d.line([(1, H-2), (W-2, H-2)], fill=light); d.line([(W-2, 1), (W-2, H-2)], fill=light)
    elif style == "double":
        d.rectangle([2, 2, W-3, H-3], outline=shift(bg, 90))
    elif style == "flat":
        d.rectangle([1, 1, W-2, H-2], outline=shift(bg, 60))


def text_img(label, font, color):
    b = font.getbbox(label)
    im = Image.new("RGBA", (b[2]-b[0]+2, b[3]-b[1]+2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((1-b[0], 1-b[1]), label, font=font, fill=color+(255,))
    return im


def render(name, label, bg, tc, tint, style, fkey, with_text=True):
    """One static RGBA button frame (icon + optional label)."""
    img = Image.new("RGBA", (W, H), bg + (255,))
    if style in ("shadow", "glossy"):
        img = Image.alpha_composite(img, grad_overlay(style, bg))
    d = ImageDraw.Draw(img)
    icon = render_icon(name, tint)
    pad_l = 5
    tx0 = pad_l + (icon.width + 4 if icon else 0)
    if icon:
        img.paste(icon, (pad_l, (H-icon.height)//2), icon)
    if with_text:
        d = ImageDraw.Draw(img)
        maxw = W - tx0 - 4
        f = fit_font(fkey, label, maxw)
        b = f.getbbox(label); tw, th = b[2]-b[0], b[3]-b[1]
        tx = tx0 + max(0, (maxw-tw)//2) if icon else (W-tw)//2
        ty = (H-th)//2 - b[1]
        d.text((tx+1, ty+1), label, font=f, fill=shift(bg, -45))
        d.text((tx, ty), label, font=f, fill=tc)
    draw_frame(d, style, bg)
    return img, tx0


def save_gif(path, frames, durs, colors=48):
    rgb = [f.convert("RGB") for f in frames]
    base = rgb[0].quantize(colors=colors, method=Image.MEDIANCUT)
    imgs = [base] + [r.quantize(colors=colors, palette=base, dither=Image.NONE) for r in rgb[1:]]
    imgs[0].save(path, save_all=True, append_images=imgs[1:],
                 duration=durs, loop=0, optimize=True, disposal=1)


# ---------- animations ----------

def anim_sweep(name, label, bg, tc, tint, fkey):
    base, _ = render(name, label, bg, tc, tint, "sweep", fkey)
    frames, durs, N = [], [], 8
    for i in range(N):
        cx = -16 + (W+32)*i/(N-1)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = ov.load()
        for y in range(1, H-1):
            c = cx + (y - H/2)*0.55
            for x in range(1, W-1):
                dd = abs(x - c)
                if dd < 11:
                    px[x, y] = (255, 255, 255, int(130*(1-dd/11)))
        frames.append(Image.alpha_composite(base, ov)); durs.append(70)
    return frames, durs


def anim_blink(name, label, bg, tc, tint, fkey):
    a, _ = render(name, label, bg, tc, tint, "blink", fkey)
    b, _ = render(name, label, shift(bg, 26), (255, 255, 120), tint, "blink", fkey)
    ImageDraw.Draw(b).rectangle([2, 2, W-3, H-3], outline=(255, 255, 120))
    return [a, b], [620, 430]


def anim_marquee(name, label, bg, tc, tint, fkey):
    base, tx0 = render(name, label, bg, tc, tint, "marquee", fkey, with_text=False)
    rw = (W - 3) - tx0
    f = fit_font(fkey, label, rw*3)          # don't shrink to region; let it scroll
    txt = text_img(label, f, tc)
    ty = (H - txt.height)//2
    gap = rw
    strip = txt.width + gap
    frames, durs, N = [], [], 14
    for k in range(N):
        off = round(strip * k/N)
        layer = Image.new("RGBA", (rw, H), (0, 0, 0, 0))
        for bx in (-off, strip - off):
            layer.alpha_composite(txt, (bx, ty))
        fr = base.copy(); fr.alpha_composite(layer, (tx0, 0))
        frames.append(fr); durs.append(95)
    return frames, durs


def anim_barber(name, label, bg, tc, tint, fkey):
    a, b = bg, shift(bg, -70)
    band = 8                                  # stripe width (px, diagonal)
    f = fit_font(fkey, label, W-10, 17)
    txt = text_img(label, f, (255, 255, 255))
    frames, durs, N = [], [], 8
    for k in range(N):
        off = round(2*band * k/N)
        img = Image.new("RGBA", (W, H), bg+(255,))
        px = img.load()
        for y in range(1, H-1):
            for x in range(1, W-1):
                px[x, y] = (a if ((x+y+off)//band) % 2 == 0 else b) + (255,)
        d = ImageDraw.Draw(img)
        d.rectangle([1, (H-15)//2, W-2, (H+15)//2], fill=(18, 18, 18))   # text plate
        img.alpha_composite(txt, ((W-txt.width)//2, (H-txt.height)//2))
        draw_frame(d, "raised", bg)
        frames.append(img); durs.append(110)
    return frames, durs


def solve(A, b):
    """Gaussian elimination, square A (list of rows), vector b."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        for j in range(c, n+1):
            M[c][j] /= pv
        for r in range(n):
            if r != c and M[r][c]:
                fac = M[r][c]
                for j in range(c, n+1):
                    M[r][j] -= fac*M[c][j]
    return [M[i][n] for i in range(n)]


def perspective_coeffs(dst, src):
    """Coeffs mapping output(dst) -> input(src) for Image.PERSPECTIVE."""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -x*u, -y*u]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -x*v, -y*v]); b.append(v)
    return solve(A, b)


def anim_spin3d(label, color):
    """True-3D: text card rotates about Y with perspective + extruded depth."""
    f = font_at("ablack", 22)
    txt = text_img(label, f, color)
    if txt.height > 26:
        s = 26/txt.height
        txt = txt.resize((max(1, int(txt.width*s)), 26), Image.LANCZOS)
    tw, th = txt.size
    src = [(0, 0), (tw, 0), (tw, th), (0, th)]
    cx, cy = W/2, H/2
    cam = 150.0                      # camera distance (perspective strength)
    hw, hh = tw/2.0, th/2.0
    frames, durs, N, layers = [], [], 14, 4
    for k in range(N):
        ang = 2*math.pi*k/N
        ca, sa = math.cos(ang), math.sin(ang)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        # extruded slabs back->front along the card normal (z thickness)
        for li in range(layers-1, -1, -1):
            depth = li * 2.2
            pts = []
            for (sx, sy) in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
                x3 = sx*ca + depth*sa
                z3 = -sx*sa + depth*ca
                p = cam/(cam + z3)
                pts.append((cx + x3*p, cy + sy*p))
            try:
                co = perspective_coeffs(pts, src)
            except ZeroDivisionError:
                continue
            warp = txt.transform((W, H), Image.PERSPECTIVE, co, Image.BILINEAR)
            if li == 0:
                shade = 0.45 + 0.55*abs(ca)          # front face lit by facing
                warp = ImageEnhance.Brightness(warp).enhance(shade)
            else:
                warp = ImageEnhance.Brightness(warp).enhance(0.28)   # dark body
            canvas.alpha_composite(warp)
        ImageDraw.Draw(canvas).rectangle([0, 0, W-1, H-1], outline=(40, 40, 40))
        frames.append(canvas); durs.append(95)
    return frames, durs


BG_DIR = os.path.join(OUT, "_bg")


def load_photo(name):
    img = Image.open(os.path.join(BG_DIR, f"{name}.jpg")).convert("RGBA")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    return img


def sparkle_stamp(_c=[]):
    """Glowing yellow-white 4-point star."""
    if _c:
        return _c[0]
    S = 9; c = S//2
    s = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    for r in range(c, 0, -1):                              # soft yellow glow halo
        a = int(70 * (1 - r/c))
        d.ellipse([c-r, c-r, c+r, c+r], fill=(255, 224, 110, a))
    d.line([(c, 1), (c, S-2)], fill=(255, 255, 200, 255))  # star spikes
    d.line([(1, c), (S-2, c)], fill=(255, 255, 200, 255))
    d.ellipse([c-1, c-1, c+1, c+1], fill=(255, 255, 255, 255))
    _c.append(s)
    return s


def rose_pattern():
    """Seamless tiled rose wallpaper (pink bg, red roses, green leaves)."""
    bgcol, rose, dark, light, leaf = (
        (246, 201, 214), (194, 30, 86), (120, 12, 48), (236, 120, 160), (58, 125, 68))
    T = 22
    tile = Image.new("RGBA", (T, T), bgcol + (255,))
    d = ImageDraw.Draw(tile)
    cx, cy, r = T//2, T//2, 6
    d.ellipse([cx-2, cy+2, cx-2+5, cy+2+4], fill=leaf)          # leaves
    d.ellipse([cx-3, cy+3, cx+2, cy+7], fill=leaf)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=rose)             # bloom
    d.arc([cx-r, cy-r, cx+r, cy+r], 0, 360, fill=dark)
    d.arc([cx-4, cy-4, cx+4, cy+4], 20, 300, fill=light)        # petal swirl
    d.arc([cx-2, cy-2, cx+2, cy+2], 60, 340, fill=dark)
    d.point((cx, cy), fill=dark)
    pat = Image.new("RGBA", (W, H), bgcol + (255,))
    for row, ty in enumerate(range(-T, H + T, T)):
        off = (T//2) if row % 2 else 0                         # brick offset
        for tx in range(-T + off, W + T, T):
            pat.alpha_composite(tile, (tx, ty))
    return pat


def cute_base(name, label):
    """Full-bleed background (photo / rose pattern) + outlined label."""
    bg = rose_pattern() if name == "mongodb" else load_photo(name)
    d = ImageDraw.Draw(bg)
    f = fit_font("comic", label, W-8, 18)
    b = f.getbbox(label); tw, th = b[2]-b[0], b[3]-b[1]
    tx = (W-tw)//2 - b[0]; ty = (H-th)//2 - b[1]
    d.text((tx, ty), label, font=f, fill=(255, 255, 255),
           stroke_width=2, stroke_fill=(25, 10, 35))
    d.rectangle([0, 0, W-1, H-1], outline=(0, 0, 0))
    return bg


def anim_cute(name, label):
    base = cute_base(name, label)
    star = sparkle_stamp()
    spots = [(6, 5), (82, 5), (6, 26), (82, 26), (44, 4)]   # corners + top, off face
    frames, durs = [], []
    for k in range(6):
        fr = base.copy()
        for i, (sx, sy) in enumerate(spots):
            if (i + k) % 2 == 0:                           # gentle twinkle
                fr.alpha_composite(star, (sx-star.width//2, sy-star.height//2))
        frames.append(fr); durs.append(170)
    return frames, durs


def ribbon_png(name, label, brand, fkey):
    img, _ = render(name, label, GREY, (10, 10, 10), brand, "grey", fkey)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(band)
    p1, p2 = (-4, H+3), (W+4, -4)                          # full diagonal /
    d.line([p1, p2], fill=(110, 0, 0, 255), width=15)      # dark border
    d.line([p1, p2], fill=(210, 28, 28, 255), width=11)    # red band
    ang = math.degrees(math.atan2(H, W))
    tt = text_img("HATE EM", font_at("ablack", 11), (255, 255, 255))
    tt = tt.rotate(ang, expand=True, resample=Image.BICUBIC)
    band.alpha_composite(tt, ((W-tt.width)//2, (H-tt.height)//2))
    img.alpha_composite(band)
    ImageDraw.Draw(img).rectangle([0, 0, W-1, H-1], outline=(0, 0, 0))
    return img


def anim_logospin(name, label, bg, tc):
    """In-plane CCW spin of the brand logo; static label kept."""
    base, _ = render(name, "", bg, tc, tc, "raised", "monaco", with_text=False)
    d = ImageDraw.Draw(base)
    zone = 30                                          # left logo zone width
    maxw = W - zone - 5
    f = fit_font("monaco", label, maxw)
    b = f.getbbox(label); tw, th = b[2]-b[0], b[3]-b[1]
    tx = zone + max(0, (maxw-tw)//2); ty = (H-th)//2 - b[1]
    d.text((tx+1, ty+1), label, font=f, fill=shift(bg, -45))
    d.text((tx, ty), label, font=f, fill=tc)           # static "docker"
    logo = render_icon(name, (255, 255, 255), h=22)
    pad = Image.new("RGBA", (34, 34), (0, 0, 0, 0))
    pad.alpha_composite(logo, ((34-logo.width)//2, (34-logo.height)//2))
    frames, durs, N = [], [], 12
    for k in range(N):
        ang = 360.0 * k / N                            # CCW
        r = pad.rotate(ang, resample=Image.BICUBIC, expand=False)
        fr = base.copy()
        fr.alpha_composite(r, (zone//2 - 17, (H-34)//2))
        frames.append(fr); durs.append(85)
    return frames, durs


# ---------- dispatch ----------

def make(name, label, bghex, style, fkey):
    brand = hx(bghex)
    if style == "grey":
        bg, tc, tint = GREY, (10, 10, 10), brand
    else:
        bg, tc, tint = brand, text_color(brand), text_color(brand)

    if style == "ribbon":
        ribbon_png(name, label, brand, fkey).convert("RGB").save(
            os.path.join(OUT, f"{name}.png"))
    elif style in ANIM:
        builders = {
            "sweep": anim_sweep, "blink": anim_blink,
            "marquee": anim_marquee, "barber": anim_barber,
        }
        if style == "spin":
            fr, du = anim_spin3d(label, brand); cols = 32
        elif style == "cute":
            fr, du = anim_cute(name, label); cols = 64
        elif style == "logospin":
            fr, du = anim_logospin(name, label, brand, text_color(brand)); cols = 32
        else:
            fr, du = builders[style](name, label, bg, tc, tint, fkey); cols = 48
        save_gif(os.path.join(OUT, f"{name}.gif"), fr, du, cols)
    else:
        render(name, label, bg, tc, tint, style, fkey)[0].convert("RGB").save(
            os.path.join(OUT, f"{name}.png"))


def main():
    if not HAVE_RSVG:
        print("WARN: rsvg-convert missing -> text-only buttons")
    anim_names = {n for n, _, _, s, _ in STACK if s in ANIM}
    for n in anim_names:                      # drop stale png for now-animated names
        p = os.path.join(OUT, f"{n}.png")
        if os.path.exists(p):
            os.remove(p)
    for n, l, c, s, fk in STACK:
        make(n, l, c, s, fk)
    print(f"generated {len(STACK)} buttons ({len(anim_names)} gif) -> {OUT}")


if __name__ == "__main__":
    main()
