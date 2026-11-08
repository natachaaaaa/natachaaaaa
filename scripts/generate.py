"""Génère le README du profil et ses SVG (DA inspirée de Kang Tao, Cyberpunk 2077).

Aucune dépendance : Python 3.9+ et la bibliothèque standard.
    python scripts/generate.py
Les textes se modifient dans scripts/config.json. Les dépôts affichés (voir
select_repos), les chiffres, les langages et les dates sont lus sur GitHub à
chaque exécution. Si GitHub ne répond pas, le README et les SVG déjà présents
sont conservés.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICONS = Path(__file__).resolve().parent / "icons"
CFG = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
USER = CFG["user"]

# Palette
BG = "#121212"
PANEL = "#1a1a1a"
LINE = "#2e2e2e"
OR = "#EE6A2F"       # orange Kang Tao
OR_DK = "#8f3a17"
WHITE = "#F2F0EC"
GREY = "#8c8c8c"
LEVELS = ["#232323", "#4a2312", "#80361a", "#bb4f23", OR]

SANS = "'Arial Black','Segoe UI Black','Helvetica Neue',Arial,sans-serif"
MONO = "Consolas,'DejaVu Sans Mono',Menlo,monospace"
CJK = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Source Han Sans SC',sans-serif"

MOIS = ["JAN", "FÉV", "MAR", "AVR", "MAI", "JUN", "JUL", "AOÛ", "SEP", "OCT", "NOV", "DÉC"]


def x(s):
    return escape(str(s), quote=True)


def svg(w, h, body, label, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{x(label)}"><title>{x(label)}</title>'
            f'<style>{style}</style>{body}</svg>\n')


def write(name, content):
    p = ASSETS / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8", newline="\n")


def fetch(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-generator"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode("utf-8")
    return data if raw else json.loads(data)


def hatch(pid, color="#1c1c1c"):
    return (f'<pattern id="{pid}" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="10" stroke="{color}" stroke-width="3"/></pattern>')


# ---------------------------------------------------------------- statiques

def header():
    w, h = 900, 270
    c1, c2 = CFG["cjk"]
    style = (
        "@keyframes sweep{0%{transform:translateX(-300px)}55%,100%{transform:translateX(1100px)}}"
        ".sweep{animation:sweep 7s ease-in-out infinite}"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:blink 1.1s steps(1) infinite}"
        "@keyframes scan{0%{transform:translateY(0)}100%{transform:translateY(212px)}}"
        ".scan{animation:scan 2.6s linear infinite}"
    )
    body = f"""
<defs>{hatch('hh')}
<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="hc"><rect width="{w}" height="{h}" rx="6"/></clipPath><clipPath id="bc"><rect x="24" y="29" width="112" height="212"/></clipPath></defs>
<g clip-path="url(#hc)">
<rect width="{w}" height="{h}" fill="{BG}"/>
<rect x="560" width="340" height="{h}" fill="url(#hh)"/>
<rect width="{w}" height="5" fill="{OR}"/>
<rect y="{h-5}" width="{w}" height="5" fill="{OR}"/>
<rect x="24" y="29" width="112" height="212" fill="{OR}"/>
<text x="80" y="122" text-anchor="middle" font-family="{CJK}" font-weight="700" font-size="76" fill="{BG}">{c1}</text>
<text x="80" y="216" text-anchor="middle" font-family="{CJK}" font-weight="700" font-size="76" fill="{BG}">{c2}</text>
<g clip-path="url(#bc)"><rect class="scan" x="24" y="29" width="112" height="3" fill="{BG}" opacity=".35"/></g>
<text x="162" y="66" font-family="{MONO}" font-weight="700" font-size="18" letter-spacing="3" fill="{OR}">{x(CFG['role'])}</text>
<text x="158" y="142" font-family="{SANS}" font-weight="900" font-style="italic" font-size="70" letter-spacing="1" fill="{WHITE}">{x(CFG['name'])}</text>
<rect class="cur" x="612" y="92" width="16" height="52" fill="{OR}"/>
<line x1="162" y1="176" x2="196" y2="176" stroke="{OR}" stroke-width="2"/>
<text x="206" y="183" font-family="{CJK}" font-size="20" fill="{OR}">{x(CFG['tagline_cjk'])}</text>
<line x1="420" y1="176" x2="600" y2="176" stroke="{OR}" stroke-width="2"/>
<text x="162" y="226" font-family="{MONO}" font-size="18" fill="{GREY}">@{x(USER)}</text>
<text x="636" y="226" text-anchor="end" font-family="{SANS}" font-weight="900" font-style="italic" font-size="15" letter-spacing="1" fill="{WHITE}">{x(CFG['slogan'])}</text>
<g font-family="{MONO}" font-size="16" letter-spacing="1">
<rect x="660" y="44" width="216" height="182" fill="{PANEL}" stroke="{LINE}"/>
<rect x="660" y="44" width="216" height="30" fill="{OR}"/>
<text x="674" y="65" font-weight="700" fill="{BG}">// DOSSIER</text>
<text x="674" y="104" fill="{GREY}">ID</text><text x="862" y="104" text-anchor="end" fill="{WHITE}">{x(USER.upper())}</text>
<text x="674" y="140" fill="{GREY}">DEPUIS</text><text x="862" y="140" text-anchor="end" fill="{WHITE}">{x(CFG['since'])}</text>
<text x="674" y="176" fill="{GREY}">FOCUS</text><text x="862" y="176" text-anchor="end" fill="{OR}">{x(CFG['focus'])}</text>
<text x="674" y="212" fill="{GREY}">ZONE</text><text x="862" y="212" text-anchor="end" fill="{WHITE}">FR</text>
</g>
<rect class="sweep" x="0" y="0" width="260" height="{h}" fill="url(#sw)"/>
</g>"""
    write("header.svg", svg(w, h, body, f"{CFG['name']}, {CFG['role']}", style))


def title(fname, num, text, cjk):
    w, h = 900, 64
    body = f"""
<rect x="0" y="12" width="52" height="40" fill="{OR}"/>
<text x="26" y="40" text-anchor="middle" font-family="{MONO}" font-weight="700" font-size="20" fill="{BG}">{num}</text>
<text x="68" y="44" font-family="{SANS}" font-weight="900" font-style="italic" font-size="28" letter-spacing="2" fill="{OR}">{x(text)}</text>
<line x1="{80 + len(text) * 22}" y1="32" x2="820" y2="32" stroke="{LINE}" stroke-width="2"/>
<rect x="812" y="28" width="8" height="8" fill="{OR}"/>
<text x="900" y="42" text-anchor="end" font-family="{CJK}" font-size="24" fill="{GREY}">{x(cjk)}</text>"""
    write(fname, svg(w, h, body, text))


def badge(icon, label):
    path = re.search(r'<path d="([^"]+)"', (ICONS / f"{icon}.svg").read_text(encoding="utf-8")).group(1)
    tw = len(label) * 10.5
    w, h = int(44 + 14 + tw + 16 + 8), 44
    bw = w - 8
    body = f"""
<rect x=".5" y=".5" width="{bw - 1}" height="{h - 1}" fill="{PANEL}" stroke="{LINE}"/>
<rect width="44" height="{h}" fill="{OR}"/>
<g transform="translate(11 11) scale(0.917)"><path d="{path}" fill="{BG}"/></g>
<text x="58" y="28" font-family="{MONO}" font-weight="700" font-size="17" letter-spacing="1" fill="{WHITE}">{x(label.upper())}</text>
<rect x="{bw - 6}" y="{h - 6}" width="6" height="6" fill="{OR}"/>"""
    write(f"stack/{icon}.svg", svg(w, h, body, label))


def group(name):
    w = int(len(name) * 12 + 60)
    body = f"""
<text x="0" y="30" font-family="{MONO}" font-weight="700" font-size="18" letter-spacing="3" fill="{OR}">// {x(name)}</text>"""
    write(f"stack/g-{name.lower()}.svg", svg(w, 44, body, name))


def footer():
    w, h = 900, 130
    c1, c2 = CFG["cjk"]
    body = f"""
<defs>{hatch('fh', '#191919')}</defs>
<rect width="{w}" height="{h}" rx="6" fill="{BG}"/>
<rect x="0" y="0" width="{w}" height="{h}" rx="6" fill="url(#fh)"/>
<rect x="0" y="20" width="10" height="90" fill="{OR}"/>
<rect x="34" y="20" width="90" height="90" fill="{OR}"/>
<text x="79" y="80" text-anchor="middle" font-family="{CJK}" font-weight="700" font-size="40" fill="{BG}">{c1}{c2}</text>
<text x="146" y="70" font-family="{SANS}" font-weight="900" font-style="italic" font-size="44" fill="{OR}">{x(USER.upper())}</text>
<line x1="148" y1="88" x2="866" y2="88" stroke="{OR_DK}" stroke-width="2"/>
<text x="148" y="110" font-family="{MONO}" font-size="15" letter-spacing="1" fill="{GREY}">{x(CFG['slogan'])}</text>
<text x="866" y="110" text-anchor="end" font-family="{MONO}" font-size="13" fill="#5c5c5c">DA fan-made inspirée de Kang Tao · Cyberpunk 2077</text>"""
    write("footer.svg", svg(w, h, body, f"{USER}, {CFG['slogan']}"))


# ---------------------------------------------------------------- données

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
    w, h = 900, 300
    dates = sorted(days)
    start = dt.date.fromisoformat(dates[0])
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # semaine commençant dimanche (comme GitHub)
    total = sum(days.values())
    active = sum(1 for v in days.values() if v)
    mx = max(days.values()) or 1
    cell, gap, ox, oy = 13, 3, 30, 112
    cells, months, last_m = [], [], None
    for d_str, n in days.items():
        d = dt.date.fromisoformat(d_str)
        col = (d - start).days // 7
        row = (d.weekday() + 1) % 7
        lvl = 0 if n == 0 else min(4, 1 + int(3 * n / mx + 0.5) if mx > 1 else 4)
        cells.append(f'<rect x="{ox + col * (cell + gap)}" y="{oy + row * (cell + gap)}" width="{cell}" height="{cell}" fill="{LEVELS[lvl]}"/>')
    for col in range(54):
        d = start + dt.timedelta(days=col * 7)
        if d.month != last_m and d.day <= 7 and col < 52:
            months.append(f'<text x="{ox + col * (cell + gap)}" y="{oy - 12}" font-family="{MONO}" font-size="15" fill="{GREY}">{MOIS[d.month - 1]}</text>')
        last_m = d.month
    legend = "".join(f'<rect x="{760 + i * 19}" y="266" width="13" height="13" fill="{c}"/>' for i, c in enumerate(LEVELS))
    body = f"""
<defs>{hatch('ah', '#181818')}</defs>
<rect width="{w}" height="{h}" rx="6" fill="{BG}"/>
<rect x="0" y="0" width="{w}" height="64" fill="url(#ah)"/>
<rect x="0" y="0" width="{w}" height="4" fill="{OR}"/>
<text x="30" y="46" font-family="{SANS}" font-weight="900" font-style="italic" font-size="40" fill="{WHITE}">{total}</text>
<text x="{44 + len(str(total)) * 30}" y="44" font-family="{MONO}" font-weight="700" font-size="17" letter-spacing="2" fill="{OR}">CONTRIBUTIONS · 12 MOIS</text>
<text x="870" y="44" text-anchor="end" font-family="{MONO}" font-size="17" letter-spacing="1" fill="{GREY}">{active} JOUR{'S' if active > 1 else ''} ACTIF{'S' if active > 1 else ''}</text>
{''.join(months)}
{''.join(cells)}
<text x="30" y="279" font-family="{MONO}" font-size="14" fill="#5c5c5c">SOURCE : CALENDRIER GITHUB · RECALCULÉ CHAQUE JOUR</text>
<text x="750" y="279" text-anchor="end" font-family="{MONO}" font-size="14" fill="{GREY}">MOINS</text>{legend}
<text x="860" y="279" font-family="{MONO}" font-size="14" fill="{GREY}">PLUS</text>"""
    write("activity.svg", svg(w, h, body, f"{total} contributions et {active} jours actifs sur douze mois"))


def wrap(text, n):
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > n and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    lines.append(cur)
    return lines


def select_repos():
    """Choisit les dépôts à afficher, sans liste à tenir à jour.

    Projets : tous les dépôts publics qui ne sont pas des forks (hors dépôt du
    profil), du plus récemment poussé au plus ancien.
    Forks : seulement ceux qui ont au moins un commit d'avance sur l'original,
    c'est-à-dire ceux où il y a vraiment du travail à toi.
    Le champ "repos" de config.json permet, par dépôt, de forcer une description
    ("desc"), de déclarer une origine pour une copie non marquée comme fork
    ("origin"), de masquer ("hide") ou de forcer l'affichage d'un fork ("show").
    """
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
    return projects[:CFG.get("max_projects", 6)], forks[:CFG.get("max_forks", 4)]


def card(idx, meta, origin, fork):
    repo = meta["name"]
    item = CFG.get("repos", {}).get(repo, {})
    langs = fetch(f"https://api.github.com/repos/{USER}/{repo}/languages")
    tag = f"FORK ← {origin}" if origin else ("FORK" if fork else "PUBLIC")
    desc = item.get("desc") or meta.get("description") or "Pas encore de description."
    lines = wrap(desc, 76)[:2]
    pushed = meta["pushed_at"][:10]
    w, h = 900, 200
    tot = sum(langs.values()) or 1
    shades = [OR, "#b9b4ac", "#bb4f23", "#6e6e6e", "#80361a"]
    bar, leg, xx, lx = [], [], 30.0, 30
    for i, (lang, b) in enumerate(sorted(langs.items(), key=lambda kv: -kv[1])[:5]):
        bw = 840 * b / tot
        bar.append(f'<rect x="{xx:.1f}" y="152" width="{bw:.1f}" height="8" fill="{shades[i]}"/>')
        xx += bw
        lbl = f"{lang.upper()} {100 * b / tot:.0f}%"
        leg.append(f'<rect x="{lx}" y="174" width="10" height="10" fill="{shades[i]}"/>'
                   f'<text x="{lx + 16}" y="184" font-family="{MONO}" font-size="15" fill="{GREY}">{x(lbl)}</text>')
        lx += 16 + len(lbl) * 8.5 + 22
    if not langs:
        bar.append(f'<rect x="30" y="152" width="840" height="8" fill="{LINE}"/>')
    text = "".join(f'<text x="30" y="{108 + i * 30}" font-family="Arial,\'Helvetica Neue\',sans-serif" font-size="21" fill="{WHITE}">{x(l)}</text>' for i, l in enumerate(lines))
    tag_w = len(tag) * 10 + 24
    body = f"""
<rect width="{w}" height="{h}" rx="6" fill="{PANEL}"/>
<rect x="0" y="0" width="8" height="{h}" fill="{OR}"/>
<text x="30" y="40" font-family="{MONO}" font-weight="700" font-size="16" letter-spacing="2" fill="{OR}">{'F' if fork else 'P'}-{idx:02d}</text>
<text x="96" y="40" font-family="{MONO}" font-size="16" fill="{GREY}">MAJ {pushed}</text>
<rect x="{870 - tag_w}" y="20" width="{tag_w}" height="28" fill="none" stroke="{OR}" stroke-width="1.5"/>
<text x="{870 - tag_w / 2}" y="40" text-anchor="middle" font-family="{MONO}" font-weight="700" font-size="15" fill="{OR}">{x(tag)}</text>
<text x="30" y="76" font-family="{SANS}" font-weight="900" font-style="italic" font-size="30" letter-spacing="1" fill="{WHITE}">{x(repo.upper())}</text>
{text}
{''.join(bar)}
{''.join(leg)}"""
    name = f"card-{repo.lower()}.svg"
    write(name, svg(w, h, body, f"{repo} : {desc}"))
    return name, repo, desc


# ---------------------------------------------------------------- README

def readme(cards, forks):
    def links(items):
        return "\n".join(f'<a href="https://github.com/{USER}/{repo}"><img src="assets/{n}" alt="{x(repo)} : {x(d)}" width="100%"></a>'
                         for n, repo, d in items)

    stack = []
    for gname, items in CFG["stack"].items():
        stack.append(f'<img src="assets/stack/g-{gname.lower()}.svg" alt="{gname}" height="44"><br>')
        stack.append("".join(f'<img src="assets/stack/{i}.svg" alt="{x(l)}" height="44">' for i, l in items) + "<br>")
    site = CFG["site"]
    fork_block = (f'\n<img src="assets/t-forks.svg" alt="Forks" width="100%">\n\n{links(forks)}\n'
                  if forks else "")
    return f"""<img src="assets/header.svg" alt="{x(CFG['name'])}, {x(CFG['role'])}" width="100%">

<p align="center">{x(CFG['bio'])}<br><b><a href="{site}">{x(site.split('//')[1])}</a></b></p>

<img src="assets/t-activite.svg" alt="Activité" width="100%">
<img src="assets/activity.svg" alt="Calendrier des contributions sur douze mois" width="100%">

<img src="assets/t-projets.svg" alt="Projets" width="100%">

{links(cards)}
{fork_block}
<img src="assets/t-stack.svg" alt="Stack" width="100%">

{chr(10).join(stack)}

<br>
<img src="assets/footer.svg" alt="{x(USER)}" width="100%">
"""


def main():
    header()
    title("t-activite.svg", "01", "ACTIVITÉ", "活动")
    title("t-projets.svg", "02", "PROJETS", "项目")
    title("t-forks.svg", "03", "FORKS", "分支")
    title("t-stack.svg", "04", "STACK", "技术")
    for gname, items in CFG["stack"].items():
        group(gname)
        for icon, label in items:
            badge(icon, label)
    footer()

    try:
        activity(contributions())
    except Exception as e:  # on garde l'ancien SVG
        print(f"activité non mise à jour : {e}", file=sys.stderr)

    try:
        projects, forks_sel = select_repos()
    except Exception as e:  # sans la liste des dépôts, on ne touche pas au README
        print(f"liste des dépôts indisponible, README conservé : {e}", file=sys.stderr)
        return

    def build(items, fork):
        out = []
        for i, (meta, origin) in enumerate(items, 1):
            name = meta["name"]
            try:
                out.append(card(i, meta, origin, fork))
            except Exception as e:
                print(f"carte {name} non mise à jour : {e}", file=sys.stderr)
                if (ASSETS / f"card-{name.lower()}.svg").exists():
                    out.append((f"card-{name.lower()}.svg", name, meta.get("description") or ""))
        return out

    cards, forks = build(projects, False), build(forks_sel, True)
    used = {n for n, _, _ in cards + forks}
    for old in ASSETS.glob("card-*.svg"):  # cartes des dépôts qui ne sont plus affichés
        if old.name not in used:
            old.unlink()
    (ROOT / "README.md").write_text(readme(cards, forks), encoding="utf-8", newline="\n")
    print(f"ok : {len(cards)} projets, {len(forks)} forks")


if __name__ == "__main__":
    main()
