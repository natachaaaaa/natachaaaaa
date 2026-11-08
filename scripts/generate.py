"""Génère le README du profil et ses visuels (style sombre et tramé).

    pip install pillow numpy
    python scripts/generate.py

Tous les visuels partent de dessins procéduraux originaux, tramés ici même
(Atkinson et Bayer). Les textes se règlent dans scripts/config.json. Les dépôts
affichés, les chiffres, les langages et les dates sont lus sur GitHub à chaque
exécution ; si GitHub ne répond pas, le README et les images déjà présents sont
conservés.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
import zlib
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
FONT = ROOT / "fonts" / "VT323-Regular.ttf"
CFG = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
USER = CFG["user"]

INK = (11, 8, 17)          # #0b0811
DEEP = (6, 4, 9)           # #060409
LINE = (61, 43, 87)
MID = (120, 60, 200)
VIOLET = (192, 107, 255)   # #c06bff
PINK = (255, 95, 207)      # #ff5fcf
LAV = (220, 203, 245)      # #dccbf5
DIM = (110, 92, 140)

MOIS = ["JAN", "FÉV", "MAR", "AVR", "MAI", "JUN", "JUL", "AOÛ", "SEP", "OCT", "NOV", "DÉC"]


def x(s):
    return escape(str(s), quote=True)


def font(px):
    return ImageFont.truetype(str(FONT), px)


def save(img, name):
    DOCS.mkdir(parents=True, exist_ok=True)
    img.save(DOCS / name, optimize=True)


def fetch(url, raw=False):
    # PROFILE_CACHE=dossier : garde les réponses sur disque (tests en local sans
    # épuiser les 60 requêtes/heure de l'API sans jeton).
    cache = os.environ.get("PROFILE_CACHE")
    cfile = Path(cache) / f"{zlib.crc32(url.encode()):08x}" if cache else None
    if cfile and cfile.exists():
        data = cfile.read_text(encoding="utf-8")
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-generator"})
        tok = os.environ.get("GITHUB_TOKEN")
        if tok and "api.github.com" in url:
            req.add_header("Authorization", f"Bearer {tok}")
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode("utf-8")
        if cfile:
            cfile.parent.mkdir(parents=True, exist_ok=True)
            cfile.write_text(data, encoding="utf-8")
    return data if raw else json.loads(data)


# ---------------------------------------------------------------- tramage

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 + 1 / 32


def bayer_matrix(n):
    m = np.array([[0]], np.float32)
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)


def bayer(gray, levels, n=8):
    """Tramage ordonné : gray (0..1) -> indices 0..levels-1."""
    h, w = gray.shape
    t = np.tile(bayer_matrix(n), (h // n + 1, w // n + 1))[:h, :w]
    v = gray * (levels - 1)
    return np.clip(np.floor(v + t), 0, levels - 1).astype(np.int32)


def atkinson(gray, levels):
    """Diffusion d'erreur d'Atkinson (3/4 de l'erreur répartie, contrastes francs)."""
    h, w = gray.shape
    a = (gray * (levels - 1)).astype(np.float64).tolist()
    out = np.zeros((h, w), np.int32)
    top = levels - 1
    for y in range(h):
        row, r1 = a[y], a[y + 1] if y + 1 < h else None
        r2 = a[y + 2] if y + 2 < h else None
        orow = out[y]
        for xx in range(w):
            old = row[xx]
            q = 0 if old < 0.5 else (top if old > top - 0.5 else int(old + 0.5))
            orow[xx] = q
            e = (old - q) / 8
            if xx + 1 < w:
                row[xx + 1] += e
            if xx + 2 < w:
                row[xx + 2] += e
            if r1 is not None:
                if xx > 0:
                    r1[xx - 1] += e
                r1[xx] += e
                if xx + 1 < w:
                    r1[xx + 1] += e
            if r2 is not None:
                r2[xx] += e
    return out


def colorize(idx, palette, accent=None, accent_palette=None, scale=2):
    """Indices -> image RGB (agrandie sans lissage), avec une 2e palette sous un masque."""
    pal = np.array(palette, np.uint8)
    rgb = pal[idx]
    if accent is not None:
        rgb = np.where(accent[..., None], np.array(accent_palette, np.uint8)[idx], rgb)
    img = Image.fromarray(rgb, "RGB")
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def glow_text(img, xy, text, f, fill, glow, radius, anchor="mm", split=0):
    halo = Image.new("L", img.size, 0)
    ImageDraw.Draw(halo).text(xy, text, font=f, fill=255, anchor=anchor, stroke_width=max(1, radius // 3), stroke_fill=255)
    halo = halo.filter(ImageFilter.GaussianBlur(radius))
    img.paste(Image.new("RGB", img.size, glow), (0, 0), halo.point(lambda v: min(255, int(v * 1.8))))
    d = ImageDraw.Draw(img)
    if split:
        d.text((xy[0] - split, xy[1]), text, font=f, fill=(255, 40, 120), anchor=anchor)
        d.text((xy[0] + split, xy[1]), text, font=f, fill=(40, 220, 255), anchor=anchor)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def scanlines(img, strength=0.22):
    a = np.asarray(img, np.float32).copy()
    a[1::3] *= 1 - strength
    return Image.fromarray(a.astype(np.uint8), "RGB")


def vignette(img, power=0.55):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    k = np.clip(1.15 - power * r ** 2, 0.25, 1)
    return Image.fromarray((np.asarray(img, np.float32) * k[..., None]).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- dessins

def scene(w, h, seed=7):
    """Dessin original : ciel étoilé, planète à anneau, crêtes et grille en perspective."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hz = h * 0.62
    g = np.clip(0.10 + 0.22 * (yy / hz) ** 2.2, 0, 0.35) * (yy < hz)
    stars = rng.random((h, w)) > 0.9965
    g = np.where(stars & (yy < hz), rng.uniform(0.5, 1, (h, w)), g)

    # Planète éclairée par le haut-gauche, et son anneau.
    cx, cy, r = w * 0.70, h * 0.38, h * 0.27
    dx, dy = (xx - cx) / r, (yy - cy) / r
    d2 = dx ** 2 + dy ** 2
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    lam = np.clip(-0.55 * dx - 0.6 * dy + 0.58 * nz, 0, 1)
    bands = 0.08 * np.sin(dy * 14 + np.sin(dx * 3) * 1.5)
    planet = d2 < 1
    g = np.where(planet, np.clip(0.06 + 0.9 * lam ** 0.9 + bands * lam, 0, 1), g)
    rim = (d2 > 0.86) & (d2 < 1.0) & (dx > 0.1)
    ring_rx, ring_ry, tilt = r * 2.0, r * 0.42, -0.22
    rx = (xx - cx) * math.cos(tilt) - (yy - cy) * math.sin(tilt)
    ry = (xx - cx) * math.sin(tilt) + (yy - cy) * math.cos(tilt)
    e = (rx / ring_rx) ** 2 + (ry / ring_ry) ** 2
    ring = (e > 0.78) & (e < 1.0)
    front = ry > 0
    ring_v = 0.55 + 0.35 * np.cos(e * 60)
    g = np.where(ring & (front | ~planet), ring_v * (0.55 + 0.45 * (rx / ring_rx + 1) / 2), g)

    # Crêtes sombres sur l'horizon.
    ridge = hz - (h * 0.06) * (0.6 + 0.4 * np.sin(xx / w * 9 + 1.3) * np.sin(xx / w * 23))
    g = np.where((yy > ridge) & (yy < hz), 0.05, g)

    # Grille au sol, en perspective.
    floor = yy >= hz
    depth = np.clip((yy - hz) / (h - hz), 0, 1) + 1e-3
    zf = 1 / depth                       # profondeur du sol
    # Épaisseur d'une ligne d'environ 1 px à l'écran ; on n'en trace aucune là
    # où elles se confondraient (près de l'horizon).
    th = 0.7 * 1.4 * zf ** 2 / (h - hz)
    hl = (np.abs(((zf * 1.4) % 1) - 0.5) < th) & (th < 0.3)
    vx = (xx - w / 2) / depth            # abscisse sur le sol : les lignes fuient vers le centre
    sp = w * 0.11
    tv = 0.6 / (depth * sp)
    vl = (np.abs(((vx / sp) % 1) - 0.5) < tv) & (tv < 0.3)
    grid_v = np.where(hl | vl, 0.25 + 0.75 * depth ** 0.6, 0.03 + 0.05 * depth)
    g = np.where(floor, grid_v, g)
    accent = rim | (floor & (depth < 0.22)) | (ring & front & (rx > 0))
    return np.clip(g, 0, 1).astype(np.float32), accent


def motif(w, h, seed):
    """Petit dessin procédural propre à chaque dépôt (choisi par son nom)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    kind = seed % 4
    if kind == 0:   # interférences
        g = np.zeros((h, w), np.float32)
        for _ in range(3):
            px, py = rng.uniform(0, w), rng.uniform(0, h)
            g += np.cos(np.sqrt((xx - px) ** 2 + (yy - py) ** 2) / rng.uniform(3, 7))
        g = (g / 3 + 1) / 2 * np.clip(1.2 - yy / h, 0.2, 1)
    elif kind == 1:  # filaments
        img = Image.new("L", (w, h), 12)
        d = ImageDraw.Draw(img)
        for i in range(70):
            y0, amp, fr, ph = rng.uniform(-10, h + 10), rng.uniform(4, 24), rng.uniform(0.01, 0.04), rng.uniform(0, 6.3)
            pts = [(xv, y0 + amp * math.sin(xv * fr + ph)) for xv in range(0, w + 8, 8)]
            d.line(pts, fill=int(rng.uniform(70, 255)), width=1 + (i % 3 == 0))
        g = np.asarray(img, np.float32) / 255
    elif kind == 2:  # dunes
        g = np.full((h, w), 0.05, np.float32)
        for k in range(5):
            base = h * (0.25 + 0.15 * k)
            line = base + rng.uniform(6, 16) * np.sin(xx / rng.uniform(18, 40) + rng.uniform(0, 6))
            g = np.where(yy > line, 0.85 - 0.16 * k + 0.1 * np.sin(yy / 3), g)
    else:            # tunnel
        cx, cy = w * rng.uniform(0.3, 0.7), h * 0.5
        ang = np.arctan2(yy - cy, xx - cx)
        rad = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / h
        g = (0.5 + 0.5 * np.sin(ang * 12 + 1 / (rad + 0.08) * 3)) * np.clip(rad * 1.6, 0, 1)
    g = np.clip(g, 0, 1) * 0.85
    accent = (xx / w + (1 - yy / h)) > 1.45
    return g.astype(np.float32), accent


# ---------------------------------------------------------------- visuels

def hero():
    w, h = 640, 260
    g, accent = scene(w, h)
    idx = atkinson(g, 4)
    art = colorize(idx, [DEEP, LINE, VIOLET, LAV], accent, [DEEP, (110, 30, 90), PINK, (255, 200, 240)])
    band = Image.new("L", art.size, 0)
    ImageDraw.Draw(band).rectangle([0, int(art.height * 0.70), art.width, art.height], fill=150)
    art.paste(Image.new("RGB", art.size, DEEP), (0, 0), band.filter(ImageFilter.GaussianBlur(30)))
    W, H = art.size
    glow_text(art, (W // 2, int(H * 0.815)), CFG["name"], font(int(H * 0.21)), LAV, VIOLET, 14, split=2)
    glow_text(art, (W // 2, int(H * 0.935)), CFG["tagline"], font(int(H * 0.062)), (200, 170, 255), (60, 0, 110), 6)
    save(vignette(scanlines(art)), "hero.png")


def divider(w=1280, h=18):
    xs = np.linspace(-1, 1, w // 2, dtype=np.float32)[None, :]
    v = np.clip(1 - np.abs(xs) ** 1.6, 0, 1) * np.clip(1 - np.abs(np.linspace(-1, 1, h // 2))[:, None] * 0.9, 0, 1)
    h2, w2 = v.shape
    t = np.tile(BAYER4, (h2 // 4 + 1, w2 // 4 + 1))[:h2, :w2]
    idx = np.clip(np.floor(v * 4 + t), 0, 4).astype(np.int32)
    save(colorize(idx, [INK, LINE, MID, VIOLET, PINK]), "divider.png")


def contributions():
    html = fetch(f"https://github.com/users/{USER}/contributions", raw=True)
    ids = dict(re.findall(r'data-date="([\d-]+)" id="(contribution-day-component-[\d-]+)"', html))
    by_id = {v: k for k, v in ids.items()}
    days = {}
    for cid, tip in re.findall(r'for="(contribution-day-component-[\d-]+)"[^>]*>([^<]+)', html):
        m = re.match(r"(\d+)", tip)
        days[by_id[cid]] = int(m.group(1)) if m else 0
    if len(days) < 300:
        raise RuntimeError("calendrier illisible")
    return days


def activity(days):
    W, H = 1280, 360
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    total, active = sum(days.values()), sum(1 for v in days.values() if v)
    mx = max(days.values()) or 1
    glow_text(img, (36, 52), str(total), font(84), LAV, VIOLET, 10, anchor="lm", split=2)
    tx = 36 + d.textlength(str(total), font=font(84)) + 22
    d.text((tx, 58), "CONTRIBUTIONS · 12 MOIS", font=font(36), fill=VIOLET, anchor="lm")
    d.text((W - 36, 58), f"{active} JOUR{'S' if active > 1 else ''} ACTIF{'S' if active > 1 else ''}",
           font=font(36), fill=PINK, anchor="rm")
    dates = sorted(days)
    start = dt.date.fromisoformat(dates[0])
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    cell, gap, ox, oy = 18, 5, 36, 132
    off = np.array([[24, 16, 34]], np.uint8)
    for d_str, n in days.items():
        day = dt.date.fromisoformat(d_str)
        col, row = (day - start).days // 7, (day.weekday() + 1) % 7
        x0, y0 = ox + col * (cell + gap), oy + row * (cell + gap)
        if n == 0:
            d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=tuple(off[0]))
            continue
        lvl = 4 if mx == 1 else min(4, 1 + round(3 * (n - 1) / (mx - 1)))
        dens = {1: 0.3, 2: 0.55, 3: 0.8, 4: 1.0}[lvl]
        top = PINK if lvl == 4 else VIOLET
        t = np.tile(BAYER4, (3, 3))[:cell // 2, :cell // 2]
        on = (dens > t)
        block = np.where(on[..., None], np.array(top, np.uint8), np.array(LINE, np.uint8))
        img.paste(Image.fromarray(block, "RGB").resize((cell, cell), Image.NEAREST), (x0, y0))
    last = None
    for col in range(53):
        day = start + dt.timedelta(days=col * 7)
        if day.month != last and day.day <= 7:
            d.text((ox + col * (cell + gap), oy - 14), MOIS[day.month - 1], font=font(26), fill=DIM, anchor="ls")
        last = day.month
    d.line([(0, H - 46), (W, H - 46)], fill=LINE)
    d.text((36, H - 22), "SOURCE : CALENDRIER GITHUB · RECALCULÉ CHAQUE JOUR", font=font(26), fill=DIM, anchor="lm")
    save(img, "activity.png")
    return total, active


def tile(meta, origin, fork, langs):
    name = meta["name"]
    seed = zlib.crc32(name.encode())
    g, accent = motif(320, 130, seed)
    idx = bayer(g, 4) if seed % 2 == 0 else atkinson(g, 4)
    art = colorize(idx, [DEEP, LINE, VIOLET, LAV], accent, [DEEP, (110, 30, 90), PINK, (255, 200, 240)])
    shade = Image.new("L", art.size, 120)
    art.paste(Image.new("RGB", art.size, DEEP), (0, 0), shade)
    W, H = art.size
    size = 74 if len(name) <= 14 else int(74 * 14 / len(name))
    glow_text(art, (W // 2, H // 2), name.upper(), font(size), LAV, VIOLET, 10, split=2)
    art = scanlines(art, 0.18)
    bar = 44
    out = Image.new("RGB", (W, H + bar), INK)
    out.paste(art, (0, 0))
    d = ImageDraw.Draw(out)
    d.line([(0, H), (W, H)], fill=LINE)
    lang = max(langs, key=langs.get).upper() if langs else "—"
    d.text((14, H + bar // 2), f"{lang} · MAJ {meta['pushed_at'][:10]}", font=font(28), fill=VIOLET, anchor="lm")
    d.text((W - 14, H + bar // 2), "FORK" if (fork or origin) else "PUBLIC", font=font(28), fill=PINK, anchor="rm")
    fname = f"tile-{name.lower()}.png"
    save(out, fname)
    return fname


# ---------------------------------------------------------------- dépôts

def select_repos():
    """Projets : dépôts publics non-forks, du plus récent au plus ancien.
    Forks : seulement ceux qui ont au moins un commit d'avance sur l'original.
    config.json > repos permet par dépôt : desc, origin, hide, show."""
    over = CFG.get("repos", {})
    repos = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
    projects, forks = [], []
    for r in repos:
        name, o = r["name"], over.get(r["name"], {})
        if name.lower() == USER.lower() or r.get("private") or r.get("archived") or o.get("hide"):
            continue
        if r["fork"]:
            meta = fetch(r["url"])
            parent = meta.get("parent") or {}
            origin = parent.get("full_name")
            keep = o.get("show", False)
            if not keep and origin:
                try:
                    cmp = fetch(f"https://api.github.com/repos/{origin}/compare/"
                                f"{parent['default_branch']}...{USER}:{meta['default_branch']}")
                    keep = cmp.get("ahead_by", 0) > 0
                except Exception as e:
                    print(f"comparaison {name} impossible : {e}", file=sys.stderr)
            if keep:
                forks.append((r, origin))
        elif o.get("origin"):
            forks.append((r, o["origin"]))
        else:
            projects.append((r, None))
    return projects[:CFG.get("max_projects", 6)], forks[:CFG.get("max_forks", 4)], len([r for r in repos if not r.get("private")])


def build_cards(items, fork):
    out = []
    for meta, origin in items:
        name = meta["name"]
        langs = fetch(f"https://api.github.com/repos/{USER}/{name}/languages")
        tot = sum(langs.values()) or 1
        desc = CFG.get("repos", {}).get(name, {}).get("desc") or meta.get("description") or "Pas encore de description."
        out.append(dict(name=name, img=tile(meta, origin, fork, langs), desc=desc, origin=origin,
                        langs=" · ".join(f"{k} {100 * v / tot:.0f} %" for k, v in sorted(langs.items(), key=lambda kv: -kv[1])[:3])))
    return out


# ---------------------------------------------------------------- README

def shield(label, color, logo=None):
    q = urllib.parse.quote(label.replace("-", "--").replace("_", "__"), safe="")
    url = f"https://img.shields.io/badge/-{q}-{color}?style=for-the-badge&labelColor=0b0811"
    if logo:
        url += f"&logo={logo}&logoColor=dccbf5"
    return f'<img src="{url}" alt="{x(label)}">'


def grid(cards):
    rows = []
    for i in range(0, len(cards), 2):
        cells = []
        for c in cards[i:i + 2]:
            credit = f'<br><sub>d\'après <a href="https://github.com/{c["origin"]}">{x(c["origin"])}</a></sub>' if c["origin"] else ""
            cells.append(f'<td width="50%" valign="top"><a href="https://github.com/{USER}/{c["name"]}">'
                         f'<img src="docs/{c["img"]}" width="100%" alt="{x(c["name"])}"></a><br>'
                         f'<b><a href="https://github.com/{USER}/{c["name"]}">{x(c["name"])}</a></b>{credit}<br>'
                         f'{x(c["desc"])}<br><sub>{x(c["langs"])}</sub></td>')
        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def readme(cards, forks, total, active, nrepos):
    div = '<img src="docs/divider.png" width="100%" alt="">'
    site = CFG["site"]
    badges = "\n".join([
        f'<a href="https://github.com/{USER}?tab=followers"><img src="https://img.shields.io/github/followers/{USER}?style=for-the-badge&labelColor=0b0811&color=c06bff&label=followers" alt="Followers"></a>',
        f'<a href="https://github.com/{USER}?tab=repositories"><img src="https://img.shields.io/badge/dépôts_publics-{nrepos}-c06bff?style=for-the-badge&labelColor=0b0811" alt="{nrepos} dépôts publics"></a>',
        f'<img src="https://img.shields.io/badge/focus-{urllib.parse.quote(CFG["focus"])}-ff5fcf?style=for-the-badge&labelColor=0b0811" alt="Focus : {x(CFG["focus"])}">',
        f'<a href="{site}"><img src="https://img.shields.io/badge/site-{urllib.parse.quote(site.split("//")[1].replace("-", "--"))}-c06bff?style=for-the-badge&labelColor=0b0811" alt="Site"></a>',
    ])
    cols = []
    for group in CFG["stack"]:
        parts = []
        for gname, items in group.items():
            parts.append(f"<b>{x(gname)}</b><br>\n" + "\n".join(shield(label, "c06bff", logo) for logo, label in items))
        cols.append('<td width="50%" valign="top">\n' + "\n<br><br>\n".join(parts) + "\n</td>")
    fork_block = (f"\n{div}\n\n## ◉ Forks\n\nDes projets d'autres personnes, sur lesquels j'ai travaillé. Le crédit revient d'abord à leurs auteurs.\n\n{grid(forks)}\n"
                  if forks else "")
    return f"""<div align="center">

<img src="docs/hero.png" alt="{x(CFG['name'])} : une planète à anneau au-dessus d'une grille, tramée en violet" width="100%">

<br>

{badges}

**{x(CFG['pitch'])}**

### [⌂ {x(site.split('//')[1])}]({site}) &nbsp;·&nbsp; [▤ Mes dépôts](https://github.com/{USER}?tab=repositories)

<sub>Visuels générés par <a href="scripts/generate.py"><b>scripts/generate.py</b></a> · style emprunté au README de <a href="https://github.com/{USER}/dither-guy"><b>Dither Guy</b></a> · <a href="#-crédits">crédits ↓</a></sub>

</div>

{div}

## ◉ Activité

<img src="docs/activity.png" width="100%" alt="Calendrier des contributions : {total} sur douze mois, {active} jours actifs">

**{total}** contribution{'s' if total > 1 else ''} sur les douze derniers mois, réparties sur **{active}** jour{'s' if active > 1 else ''}. Recalculé chaque jour à partir du calendrier GitHub.

{div}

## ◉ Projets

{grid(cards)}
{fork_block}
{div}

## ◉ Stack

<table>
<tr>
{chr(10).join(cols)}
</tr>
</table>

{div}

## ◉ Crédits

- **Style** : repris du README de [Dither Guy](https://github.com/{USER}/dither-guy), lui-même un fork du projet de [Manoel Piovesan](https://github.com/manoelpiovesan/dither-guy), à qui revient l'idée de départ.
- **Visuels** : dessins procéduraux originaux, tramés (Atkinson et Bayer) par [`scripts/generate.py`](scripts/generate.py).
- **Police** : [VT323](https://fonts.google.com/specimen/VT323) de Peter Hull, sous [SIL Open Font License 1.1](fonts/OFL.txt).
- **Badges** : [shields.io](https://shields.io), logos [Simple Icons](https://simpleicons.org) (CC0).

<div align="center">

<sub>Mis à jour automatiquement chaque jour par une GitHub Action.</sub>

{div}

</div>
"""


def main():
    hero()
    divider()
    try:  # sans les données GitHub, on ne touche ni au README ni aux images de données
        days = contributions()
        projects, forks_sel, nrepos = select_repos()
        cards, forks = build_cards(projects, False), build_cards(forks_sel, True)
    except Exception as e:
        print(f"données GitHub indisponibles, README conservé : {e}", file=sys.stderr)
        return
    total, active = activity(days)
    used = {c["img"] for c in cards + forks}
    for old in DOCS.glob("tile-*.png"):
        if old.name not in used:
            old.unlink()
    (ROOT / "README.md").write_text(readme(cards, forks, total, active, nrepos), encoding="utf-8", newline="\n")
    print(f"ok : {len(cards)} projets, {len(forks)} forks, {total} contributions")


if __name__ == "__main__":
    main()
