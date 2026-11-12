#!/usr/bin/env python3
"""Builds assets/garden.svg — the animated pixel-garden profile README.

The sky follows the time of day in the Netherlands (dawn / day / sunset / night), the shiba
sleeps in the evening, and the commit garden is drawn from the real contribution calendar.

Usage:
    python scripts/build_readme.py                 # phase from the clock, data from GitHub
    python scripts/build_readme.py --phase night   # force a phase
    python scripts/build_readme.py --sample        # fake contribution data (offline preview)

Environment:
    GITHUB_TOKEN / GH_TOKEN   token for the GraphQL contribution query (optional)
    GITHUB_USER               defaults to Samdatbenik
"""
import argparse
import base64
import datetime as dt
import json
import os
import random
import sys
import urllib.request
from html import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites as sp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER = os.environ.get('GITHUB_USER', 'Samdatbenik')

W = 880
PAD = 32
X0 = PAD
CW = W - 2 * PAD
FONT = "'Pixelify Sans', 'Courier New', monospace"

# ================================================================ content

ABOUT = [
    "I build full-stack apps, from Next.js frontends to C# and Node.js backends.",
    "Software Engineering student at Fontys ICT, full-stack developer at Code for Good.",
    "Lately I'm into AI integrations, the Model Context Protocol and RAG services.",
    "Best enjoyed with coffee, a lo-fi playlist and a sleepy shiba.",
]
BACKPACK = [
    ('TypeScript', '#3178c6'), ('Next.js', '#efe6d6'), ('React', '#61dafb'), ('Tailwind CSS', '#38bdf8'),
    ('C# / .NET', '#9b6ee0'), ('Python', '#e8b931'), ('Java', '#e07a3a'), ('AI · MCP', '#8fc27a'),
    ('Node.js', '#5fa04e'), ('PostgreSQL', '#4f7fbf'), ('Docker', '#2496ed'), ('Git', '#f05032'),
]
PROJECTS = [
    ('ndex', 'Productivity platform with real-time collaboration, built on a shared TypeScript/React core and data engine.', 'TypeScript', '#3178c6', 0),
    ('Lodestar', 'Gamified quest tracker with a C# clean-architecture API, Next.js frontend and Python ML recommendations.', 'C#', '#9b6ee0', 1),
    ('Vektor', 'AI-powered dev hub bridging Claude & Codex with GitHub PR pre-reviews, diff tracking and chat alerts.', 'TypeScript', '#3178c6', 2),
    ('Music app', 'Next.js + React frontend with charts, backed by a Python FastAPI service and trained AI models.', 'TypeScript · Python', '#3178c6', 3),
]
LINKS = ['github', 'linkedin']

SKIES = {
    'dawn':   dict(top='#2f3270', mid='#b8789f', bot='#f6c39a', neb=.35, stars=.35, moon=0, clouds=.8, cloud='#ffe0e6', sunHi=0, sunLo=1, sunCol='#ffd9a0', lamp=.5, lampFill='#f4b860', far='#5a4a78', hill='#2c4a3a', ink='#f6eedd', sub='#f3e6f0', shadow='#2f3270'),
    'day':    dict(top='#5aa3e0', mid='#8cc4ee', bot='#d4ebf6', neb=0, stars=0, moon=0, clouds=1, cloud='#ffffff', sunHi=1, sunLo=0, sunCol='#fff1a8', lamp=0, lampFill='#8a7a5a', far='#6f9fb8', hill='#3f7a55', ink='#1d2445', sub='#1d2445', shadow='#d4ebf6'),
    'sunset': dict(top='#2a2766', mid='#c4577a', bot='#f7a35c', neb=.5, stars=.4, moon=0, clouds=.75, cloud='#ffc9a8', sunHi=0, sunLo=1, sunCol='#ffa24d', lamp=.85, lampFill='#f4b860', far='#4a2f5a', hill='#2c4a3a', ink='#f6eedd', sub='#ffe6d6', shadow='#2a2766'),
    'night':  dict(top='#0b0920', mid='#1a1840', bot='#2a2152', neb=1, stars=1, moon=1, clouds=0, cloud='#ffffff', sunHi=0, sunLo=0, sunCol='#ffa24d', lamp=1, lampFill='#f4b860', far='#141c30', hill='#1d3329', ink='#f6eedd', sub='#cfc6e0', shadow='#0b0920'),
}
BYE = {'dawn': 'thanks for visiting ~ good morning', 'day': 'thanks for visiting ~ have a lovely day',
       'sunset': 'thanks for visiting ~ cozy evening', 'night': 'thanks for visiting ~ sleep well'}

# ================================================================ time + data


def nl_now():
    """Current time in Europe/Amsterdam without needing tz data (CET/CEST rules)."""
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo('Europe/Amsterdam'))
    except Exception:
        utc = dt.datetime.now(dt.timezone.utc)
        y = utc.year

        def last_sunday(month):
            d = dt.datetime(y, month + 1, 1, tzinfo=dt.timezone.utc) - dt.timedelta(days=1)
            return d - dt.timedelta(days=(d.weekday() + 1) % 7)
        start = last_sunday(3).replace(hour=1)
        end = last_sunday(10).replace(hour=1)
        return utc + dt.timedelta(hours=2 if start <= utc < end else 1)


def phase_for(hour):
    if 5 <= hour < 8:
        return 'dawn'
    if 8 <= hour < 18:
        return 'day'
    if 18 <= hour < 21:
        return 'sunset'
    return 'night'


def fetch_calendar(token):
    query = ('query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{'
             'totalContributions weeks{contributionDays{weekday contributionLevel}}}}}}')
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'login': USER}}).encode(),
        headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json', 'User-Agent': 'readme-garden'})
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)['data']['user']['contributionsCollection']['contributionCalendar']
    lv = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}
    weeks = []
    for w in cal['weeks'][-53:]:
        days = [None] * 7
        for d in w['contributionDays']:
            days[d['weekday']] = lv[d['contributionLevel']]
        weeks.append(days)
    return cal['totalContributions'], weeks


def sample_calendar():
    rnd = random.Random(42)
    weeks = []
    for w in range(53):
        season = 0.5 + 0.5 * __import__('math').sin(w / 6)
        days = []
        for d in range(7):
            r = rnd.random() * season * (0.4 if d in (0, 6) else 1) + rnd.random() * 0.25
            days.append(0 if r < .25 else 1 if r < .45 else 2 if r < .62 else 3 if r < .78 else 4)
        weeks.append(days)
    return None, weeks

# ================================================================ svg helpers


def tw(s, size):
    # conservative: also fits the monospace fallback when the pixel font is missing
    return len(s) * size * 0.6


def wrap(text, size, maxw):
    lines, cur = [], ''
    for word in text.split():
        nxt = (cur + ' ' + word).strip()
        if tw(nxt, size) > maxw and cur:
            lines.append(cur)
            cur = word
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    return lines


def text(x, y, s, size, fill, weight=400, anchor='start', shadow=None, cls='', style=''):
    attrs = f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"'
    c = f' class="{cls}"' if cls else ''
    st = f' style="{style}"' if style else ''
    out = ''
    if shadow:
        out += f'<text x="{x + shadow[0]}" y="{y + shadow[1]}" {attrs} fill="{shadow[2]}"{c}{st}>{escape(s)}</text>'
    return out + f'<text x="{x}" y="{y}" {attrs} fill="{fill}"{c}{st}>{escape(s)}</text>'


def rect(x, y, w, h, fill, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{extra}/>'


R1, R2 = '#6e4527', '#8a5a34'
VD, VL1, VL2, VP, VY = '#3f8253', '#4d9a5a', '#6fb55f', '#f2a3c8', '#f4d06f'
VINE_TL = [(30, 6, 8, 8, VD), (36, 2, 10, 8, VL1), (44, 8, 8, 8, VL2), (52, 4, 10, 8, VL1), (60, 10, 8, 6, VD),
           (70, 6, 8, 8, VL2), (78, 2, 8, 8, VL1), (86, 10, 12, 6, VD), (98, 6, 6, 6, VL2),
           (0, 34, 8, 8, VL1), (2, 42, 6, 8, VD), (0, 50, 8, 6, VL2), (2, 56, 5, 6, VD), (1, 67, 5, 5, VL1),
           (42, 0, 6, 6, VP), (66, 4, 6, 6, VY), (88, 6, 6, 6, VP), (0, 62, 5, 5, VP)]
VINE_TR = [(30, 4, 10, 8, VL1), (40, 0, 8, 8, VL2), (48, 8, 10, 6, VD), (58, 4, 8, 8, VL1),
           (0, 30, 8, 8, VD), (1, 38, 6, 6, VL2), (0, 44, 7, 7, VL1), (54, 2, 6, 6, VP), (1, 51, 5, 5, VY)]
ROOTS_L = [(70, 0, 4, 22, R1), (62, 7, 8, 3, R1), (59, 1, 3, 7, R1), (74, 11, 8, 3, R2), (81, 6, 3, 6, R2)]
ROOTS_R = [(110, 2, 4, 20, R1), (114, 9, 9, 3, R1), (100, 5, 10, 3, R2), (97, 0, 3, 6, R2)]
ROOTS_P = [(.48, 4, 3, 18, R1), (.46, 9, 10, 3, R2), (.51, 3, 8, 3, R2)]


def wood(x, y, w, h, bg='#1b1a33', vine=True):
    """Plank frame with fence posts (and optional vines + roots). (x,y,w,h) is the outer box."""
    o = [rect(x - 3 + 8, y - 3 + 8, w + 6, h + 6, '#0a0914'), rect(x - 3, y - 3, w + 6, h + 6, '#4a2c1a')]
    if bg:
        o.append(rect(x + 6, y + 6, w - 12, h - 12, bg))
    o += [rect(x, y, w, 6, 'url(#plankH)'), rect(x, y + h - 6, w, 6, 'url(#plankH)'),
          rect(x, y, 6, h, 'url(#plankV)'), rect(x + w - 6, y, 6, h, 'url(#plankV)')]
    return ''.join(o)


def wood_deco(x, y, w, h, vine=True):
    """Posts / vines / roots drawn above the frame content."""
    o = []
    ax, ay, aw, ah = x - 16, y - 16, w + 32, h + 32
    for (px, top) in [(ax, True), (ax + aw - 18, True), (ax, False), (ax + aw - 18, False)]:
        py = ay if top else ay + ah - 26
        o += [rect(px, py, 18, 26, '#3a2218'), rect(px + 3, py + 3, 12, 20, '#7a4c2a'), rect(px + 3, py + 3, 12, 4, '#e2b47e')]
    if vine:
        bx, by, bw, bh = x - 6, y - 12, w + 12, h + 34
        for (l, t, ww, hh, c) in VINE_TL:
            o.append(rect(bx + l, by + t, ww, hh, c))
        for (r, t, ww, hh, c) in VINE_TR:
            o.append(rect(bx + bw - r - ww, by + t, ww, hh, c))
        for (l, b, ww, hh, c) in ROOTS_L:
            o.append(rect(bx + l, by + bh - b - hh, ww, hh, c))
        for (r, b, ww, hh, c) in ROOTS_R:
            o.append(rect(bx + bw - r - ww, by + bh - b - hh, ww, hh, c))
        for (p, b, ww, hh, c) in ROOTS_P:
            o.append(rect(round(bx + (bw - ww) * p), by + bh - b - hh, ww, hh, c))
    return ''.join(o)


def plank_box(x, y, w, h, bg='#1b1a33', shadow=True):
    o = []
    if shadow:
        o.append(rect(x - 2 + 4, y - 2 + 4, w + 4, h + 4, '#0a0914'))
    o += [rect(x - 2, y - 2, w + 4, h + 4, '#4a2c1a'), rect(x, y, w, h, 'url(#plankH)'), rect(x + 4, y + 4, w - 8, h - 8, bg)]
    return ''.join(o)


def sign(x, y, label, icon=False):
    size = 24
    w = int(tw(label, size)) + 32 + (30 if icon else 0)
    h = 53
    o = [rect(x + 5, y + 5, w, h, '#0a0914'), rect(x, y, w, h, '#4a2c1a'),
         rect(x + 3, y + 3, w - 6, h - 6, 'url(#plankSign)'), rect(x + 3, y + 3, w - 6, 3, '#c99460')]
    tx = x + 19
    if icon:
        o.append(f'<g transform="translate({tx} {y + 16}) scale(4)">{sp.paths_from_rects([(2, 1, 1, 4, "#4d9a5a"), (0, 1, 2, 1, "#8fc27a"), (3, 0, 2, 1, "#8fc27a"), (3, 2, 1, 1, "#8fc27a")])}</g>')
        tx += 30
    o.append(text(tx, y + 35, label, size, '#fff1dc', 700, shadow=(2, 2, '#4a2c1a')))
    return ''.join(o), h


def bubble_group(lines, x, y, cls_delay_step=4, size=15, tail='down', tail_x=50):
    """Speech bubbles that take turns (CSS class .say, 16s cycle)."""
    o = []
    for i, s in enumerate(lines):
        bw = int(tw(s, size)) + 26
        bh = size + 18
        g = [rect(x + 3, y + 3, bw, bh, '#0a0914'), rect(x, y, bw, bh, '#3a2218'), rect(x + 3, y + 3, bw - 6, bh - 6, '#fff6ee'),
             text(x + 13, y + bh - 11, s, size, '#3a2218')]
        if tail == 'down':
            g.append(rect(x + tail_x, y + bh, 9, 6, '#3a2218'))
        else:
            g.insert(0, rect(x - 6, y + bh // 2 - 4, 6, 8, '#3a2218'))
        o.append(f'<g class="say" style="animation-delay:{i * cls_delay_step}s">{"".join(g)}</g>')
    return ''.join(o)


def nebula(fid, items, opacity):
    a, b, c = items
    return (f'<g filter="url(#{fid})" style="mix-blend-mode:screen" opacity="{opacity}">'
            f'<g class="nebA">{a}</g><g class="nebB">{b}</g><g class="breathe">{c}</g></g>')


def wisp_filter(fid, seed, freq, scale):
    f1 = f'{freq[0]} {freq[1]}'
    f2 = f'{freq[0] * 1.35:.4f} {freq[1] * 1.3:.4f}'
    f3 = f'{freq[0] * .85:.4f} {freq[1] * .85:.4f}'
    return (f'<filter id="{fid}" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feGaussianBlur in="SourceGraphic" stdDeviation="15" result="b"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency="{f1}" numOctaves="3" seed="{seed}" result="t">'
            f'<animate attributeName="baseFrequency" values="{f1};{f2};{f3};{f1}" dur="24s" repeatCount="indefinite"/></feTurbulence>'
            f'<feDisplacementMap in="b" in2="t" scale="{scale}" xChannelSelector="R" yChannelSelector="G">'
            f'<animate attributeName="scale" values="{scale - 20};{scale + 30};{scale - 5};{scale - 20}" dur="16s" repeatCount="indefinite"/></feDisplacementMap></filter>')


def stars(pts, opacity):
    o = [f'<g opacity="{opacity}">']
    for i, (x, y, s, c) in enumerate(pts):
        o.append(rect(x, y, s, s, c, f' class="tw" style="animation-delay:{(i * .7) % 3:.1f}s"'))
    o.append('</g>')
    return ''.join(o)


def cloud_band(fill, opacity, shapes, width):
    d = ' '.join(shapes)
    return (f'<g opacity="{opacity}"><g class="drift" style="--w:-{width}px"><path d="{d}" fill="{fill}"/>'
            f'<path d="{d}" fill="{fill}" transform="translate({width} 0)"/></g></g>')


def tree(x, y, scale):
    return f'<use href="#tree" transform="translate({x} {y}) scale({scale})"/>'


def bushes(items):
    shapes = {
        'a': ('M0 0v-16h8v-8h8v-8h24v4h12v8h8v8h4v12z', '#2f6b45', [(12, -30, 20, 4, '#4d9a5a'), (40, -22, 10, 4, '#4d9a5a'), (20, -18, 4, 4, '#f2a3c8'), (44, -12, 4, 4, '#f4d06f')]),
        'b': ('M0 0v-12h12v-12h16v-8h28v8h12v12h8v12z', '#275a3b', [(30, -30, 22, 4, '#3f8253'), (18, -14, 4, 4, '#f4d06f'), (52, -18, 4, 4, '#f2a3c8')]),
        'c': ('M0 0v-14h10v-10h26v6h12v18z', '#2f6b45', [(12, -22, 18, 4, '#4d9a5a'), (34, -12, 4, 4, '#f4d06f')]),
        'd': ('M0 0v-18h12v-8h28v8h20v18z', '#275a3b', [(14, -24, 22, 4, '#3f8253'), (44, -12, 4, 4, '#f2a3c8')]),
    }
    o = []
    for kind, x, y in items:
        d, f, extra = shapes[kind]
        o.append(f'<g transform="translate({x} {y})"><path d="{d}" fill="{f}"/>' + ''.join(rect(*e) for e in extra) + '</g>')
    return ''.join(o)

# ================================================================ scenes


def header_scene(ph, sky, now):
    """Local coords 804 x 396."""
    W_, H_ = 804, 396
    asleep = ph in ('sunset', 'night')
    o = [rect(0, 0, W_, H_, 'url(#hSky)')]
    if sky['sunHi']:
        o.append(f'<g opacity="{sky["sunHi"]}"><circle class="sunpulse" cx="660" cy="74" r="90" fill="url(#sunGlow)"/>'
                 + rect(640, 50, 40, 48, sky['sunCol']) + rect(632, 58, 56, 32, sky['sunCol']) + rect(648, 56, 10, 6, '#ffffff', ' opacity=".6"') + '</g>')
    if sky['sunLo']:
        o.append(f'<g opacity="{sky["sunLo"]}"><circle class="sunpulse" cx="560" cy="250" r="110" fill="url(#sunGlow)"/>'
                 + rect(536, 222, 48, 56, sky['sunCol']) + rect(528, 230, 64, 40, sky['sunCol']) + '</g>')
    if sky['neb']:
        o.append(nebula('wispH', (
            '<ellipse cx="560" cy="120" rx="230" ry="90" fill="#3a3fb0" opacity=".75"/><ellipse cx="660" cy="190" rx="150" ry="70" fill="#5b4fd0" opacity=".6"/><ellipse cx="420" cy="200" rx="160" ry="60" fill="#2b3d9a" opacity=".6"/>',
            '<ellipse cx="500" cy="90" rx="130" ry="70" fill="#b2305a" opacity=".8"/><ellipse cx="610" cy="140" rx="110" ry="50" fill="#7a2f8f" opacity=".7"/><ellipse cx="300" cy="150" rx="120" ry="40" fill="#6a3aa8" opacity=".45"/>',
            '<ellipse cx="510" cy="96" rx="44" ry="26" fill="#ffd0e0"/><ellipse cx="640" cy="170" rx="50" ry="22" fill="#9fb6ff" opacity=".7"/>'), sky['neb']))
    if sky['stars']:
        o.append(stars([(60, 40, 3, '#fff'), (150, 110, 2, '#cfd8ff'), (260, 30, 3, '#fff'), (380, 70, 2, '#ffd0e0'), (470, 24, 3, '#fff'),
                        (540, 160, 2, '#fff'), (620, 60, 3, '#cfd8ff'), (760, 36, 3, '#fff'), (330, 190, 2, '#fff'), (210, 200, 2, '#cfd8ff')], sky['stars']))
        o.append(f'<g opacity="{sky["stars"]}"><g transform="rotate(-27 742 41)"><rect class="shoot" x="720" y="40" width="44" height="2" fill="#fff"/></g>'
                 f'<g transform="rotate(-27 478 21)"><rect class="shoot" x="460" y="20" width="36" height="2" fill="#ffd0e0" style="animation-delay:5s;animation-duration:9s"/></g></g>')
    if sky['moon']:
        o.append(rect(700, 44, 28, 36, '#fff0c9') + rect(694, 52, 40, 20, '#fff0c9') + rect(712, 44, 22, 26, sky['top']))
    if sky['clouds']:
        o.append(cloud_band(sky['cloud'], sky['clouds'], [
            'M60 96h24v-8h16v-8h32v8h16v8h16v12H60z', 'M330 140h16v-8h24v-6h28v6h12v8h12v10h-92z', 'M560 110h20v-8h16v-8h28v8h14v8h14v10h-92z'], 808))
    # landscape
    o.append(f'<path d="M0 396V296h24v-8h40v-12h32v8h48v-16h40v12h56v8h48v-20h32v8h60v12h44v-8h52v-16h36v12h56v8h48v-12h40v8h56v16h48v12h48v100z" fill="{sky["far"]}"/>')
    o.append(f'<path d="M0 396V326h72v-6h120v6h96v-8h120v8h104v-6h136v6h160v70z" fill="{sky["hill"]}"/>')
    o.append(rect(0, 352, 808, 44, '#22402f') + rect(0, 352, 808, 4, '#33583f'))
    o.append(''.join(rect(x, y, w, 4, '#3a5a46') for x, y, w in [(120, 364, 12), (300, 372, 16), (520, 366, 12), (690, 374, 16)]))
    # trees, lantern, bushes
    o.append(tree(250, 259, 2.2) + tree(340, 202, 3.5) + tree(676, 202, 3.5))
    o.append(f'<g class="apple">{rect(770, 290, 8, 8, "#e0504a")}{rect(770, 290, 4, 4, "#f59a8a")}{rect(774, 286, 4, 4, "#5d7d3a")}</g>')
    o.append(f'<g class="apple" style="animation-delay:4.5s">{rect(372, 290, 8, 8, "#e0504a")}{rect(372, 290, 4, 4, "#f59a8a")}{rect(376, 286, 4, 4, "#5d7d3a")}</g>')
    o.append(rect(662, 292, 4, 62, '#3a3046') + rect(654, 272, 20, 22, '#3a3046') + rect(658, 276, 12, 14, sky['lampFill']))
    o.append(bushes([('a', 0, 356), ('b', 70, 356), ('a', 170, 356), ('c', 590, 356), ('d', 748, 356)]))
    o.append('<g class="grass">' + ''.join(rect(x, y, 3, h, c) for x, y, h, c in [(150, 342, 12, '#4d9a5a'), (155, 338, 16, '#3f8253'), (350, 340, 14, '#4d9a5a'), (560, 342, 12, '#4d9a5a'), (565, 338, 16, '#3f8253')]) + '</g>')
    if sky['lamp']:
        o.append(f'<g opacity="{sky["lamp"]}"><circle class="lamp" cx="664" cy="283" r="70" fill="url(#lampGlow)"/>'
                 + ''.join(rect(x, y, 4, 4, '#e8f59a', f' class="ff" style="animation-delay:{d}s"') for x, y, d in [(120, 300, 0), (330, 280, 1.3), (620, 250, 2.1), (560, 310, .6), (780, 290, 2.8)]) + '</g>')
    # shiba
    if asleep:
        o.append(f'<g transform="translate(506 246) scale(5)">{sp.shiba_front(True)}</g>')
        o.append(text(602, 258, 'z', 18, '#f6eedd', 700, cls='zz') + text(612, 246, 'Z', 24, '#f6eedd', 700, cls='zz', style='animation-delay:1.6s'))
    else:
        chat = (['*yawn* good morning!'] if ph == 'dawn' else ['woof! welcome to my garden']) + \
               ["i'm sam's shiba~", 'nice weather for coding!' if ph == 'day' else 'look, the sun is up!', 'psst... check out Vektor']
        o.append(bubble_group(chat, 470, 200))
        o.append(f'<g class="hop"><g transform="translate(506 246)"><g class="tilt"><g transform="scale(5)">{sp.shiba_front(False)}</g></g></g></g>')
        o.append(f'<g class="heart"><g transform="translate(596 240) scale(2)">{sp.HEART}</g></g>')
    # title
    sh = (3, 3, sky['shadow'])
    o.append(text(40, 62, "hi there, i'm", 18, sky['sub'], shadow=sh, cls='fade'))
    o.append(text(40, 128, 'Sam Huang', 60, sky['ink'], 700, shadow=sh, cls='fade', style='animation-delay:.3s'))
    o.append(text(40, 162, 'full-stack developer & student', 21, sky['ink'], shadow=sh, cls='fade', style='animation-delay:.6s'))
    chip = 'currently growing: ndex'
    cw = int(tw(chip, 16)) + 54
    o.append(f'<g class="fade" style="animation-delay:.9s">{plank_box(40, 182, cw, 40, shadow=False)}'
             f'<g transform="translate(56 196) scale(4)">{sp.paths_from_rects([(1, 0, 1, 3, "#4d9a5a"), (0, 1, 1, 1, "#8fc27a"), (2, 0, 1, 1, "#8fc27a")])}</g>'
             + text(78, 208, chip, 16, '#efe6d6') + '</g>')
    label = f'{ph} · updated {now:%H:%M} NL' + (' · shh, shiba is sleeping' if asleep else '')
    lw = int(tw(label, 14)) + 28
    o.append(plank_box(W_ - 14 - lw, 14, lw, 32, shadow=False) + text(W_ - 14 - lw + 14, 35, label, 14, '#efe6d6'))
    return ''.join(o)


def garden_scene(ph, sky, total, weeks):
    """Local coords 804 x 324."""
    W_, H_ = 804, 324
    asleep = ph in ('sunset', 'night')
    o = [rect(0, 0, W_, H_, 'url(#gSky)')]
    if sky['sunHi'] or sky['sunLo']:
        o.append(f'<g opacity="{max(sky["sunHi"], sky["sunLo"] * .9)}"><circle cx="520" cy="56" r="70" fill="url(#sunGlow)"/>'
                 + rect(504, 38, 32, 36, sky['sunCol']) + rect(498, 44, 44, 24, sky['sunCol']) + '</g>')
    if sky['neb']:
        o.append(nebula('wispG', (
            '<ellipse cx="520" cy="50" rx="230" ry="50" fill="#3a3fb0" opacity=".7"/><ellipse cx="680" cy="70" rx="120" ry="34" fill="#7a2f8f" opacity=".6"/>',
            '<ellipse cx="560" cy="44" rx="110" ry="30" fill="#b2305a" opacity=".7"/>',
            '<ellipse cx="566" cy="46" rx="36" ry="14" fill="#ffd0e0" opacity=".8"/>'), sky['neb']))
    if sky['stars']:
        o.append(stars([(300, 20, 3, '#fff'), (420, 70, 2, '#cfd8ff'), (760, 24, 3, '#fff'), (640, 96, 2, '#fff')], sky['stars']))
    if sky['clouds']:
        o.append(cloud_band(sky['cloud'], sky['clouds'], ['M380 70h20v-8h14v-8h26v8h14v8h12v10h-86z', 'M640 92h14v-6h20v-6h22v6h10v6h10v8h-76z'], 808))
    o.append(rect(0, 112, W_, 128, '#171528') + rect(0, 112, W_, 4, '#2c4a3a') + rect(0, 236, W_, 4, '#2c4a3a'))
    o.append(f'<path d="M0 324v-56h64v-6h120v6h160v-6h140v6h120v-6h200v62z" fill="{sky["hill"]}"/>')
    o.append(rect(0, 284, W_, 40, '#22402f') + rect(0, 284, W_, 4, '#33583f'))
    o.append('<g class="grass">' + ''.join(rect(x, y, 3, h, c) for x, y, h, c in [(90, 272, 12, '#4d9a5a'), (95, 268, 16, '#3f8253'), (330, 270, 14, '#4d9a5a'), (560, 272, 12, '#4d9a5a'), (740, 268, 16, '#3f8253')]) + '</g>')
    o.append(rect(96, 264, 4, 4, '#f2a3c8') + rect(742, 262, 4, 4, '#f4d06f'))
    # cells
    cells = []
    for wi, days in enumerate(weeks):
        for d, lvl in enumerate(days):
            if lvl is None:
                continue
            x, y = 4 + wi * 15, 124 + d * 15
            cells.append(f'<g class="cell" style="animation-delay:{wi * .035 + d * .01:.2f}s"><use href="#c{lvl}" transform="translate({x} {y}) scale(2.6)"/></g>')
    o.append(''.join(cells))
    # texts
    sh = (2, 2, sky['shadow'])
    o.append(text(24, 46, "sam's commit garden", 28, sky['ink'], 700, shadow=sh))
    sub = 'every commit plants something ~ last 12 months' if total is None else f'{total} contribution{"" if total == 1 else "s"} in the last year ~ every commit plants something'
    o.append(text(24, 72, sub, 17, sky['ink'], shadow=sh))
    lx = W_ - 16 - 232
    o.append(plank_box(lx, 16, 232, 34, shadow=False) + text(lx + 12, 39, 'less', 15, '#efe6d6') + text(lx + 220, 39, 'more', 15, '#efe6d6', anchor='end'))
    o.append(''.join(f'<use href="#c{i}" transform="translate({lx + 56 + i * 18} {27}) scale(2.6)"/>' for i in range(5)))
    if asleep:
        o.append(f'<g transform="translate(372 230) scale(2.5)">{sp.shiba_front(True)}</g>')
        o.append(text(426, 236, 'z', 15, '#f6eedd', 700, cls='zz') + text(434, 226, 'Z', 20, '#f6eedd', 700, cls='zz', style='animation-delay:1.6s'))
    else:
        walker = (f'<g transform="translate(0 233)"><g class="bob"><g transform="scale(3)">{sp.shiba_side()}</g></g>'
                  + bubble_group(['sniff sniff...', 'so many flowers!', 'every commit = a flower', 'woof!'], 80, 4, size=13, tail='left') + '</g>')
        o.append(f'<g class="walk">{walker}</g>')
    if sky['lamp']:
        o.append(f'<g opacity="{sky["lamp"]}">' + ''.join(rect(x, y, 4, 4, '#e8f59a', f' class="ff" style="animation-delay:{d}s"') for x, y, d in [(220, 254, .7), (500, 250, 2.2), (700, 258, 1.3)]) + '</g>')
    return ''.join(o)


def footer_scene(ph, sky):
    """Local coords 804 x 196."""
    W_, H_ = 804, 196
    asleep = ph in ('sunset', 'night')
    o = [rect(0, 0, W_, H_, 'url(#gSky)')]
    if sky['sunHi']:
        o.append(f'<g opacity="{sky["sunHi"]}"><circle cx="560" cy="50" r="60" fill="url(#sunGlow)"/>' + rect(546, 34, 28, 32, sky['sunCol']) + rect(540, 40, 40, 20, sky['sunCol']) + '</g>')
    if sky['sunLo']:
        o.append(f'<g opacity="{sky["sunLo"]}"><circle cx="560" cy="140" r="70" fill="url(#sunGlow)"/>' + rect(544, 118, 32, 40, sky['sunCol']) + rect(538, 126, 44, 24, sky['sunCol']) + '</g>')
    if sky['clouds']:
        o.append(cloud_band(sky['cloud'], sky['clouds'], ['M120 60h20v-8h14v-8h26v8h14v8h12v10h-86z', 'M420 84h14v-6h20v-6h22v6h10v6h10v8h-76z'], 808))
    if sky['neb']:
        o.append(nebula('wispF', (
            '<ellipse cx="300" cy="60" rx="220" ry="50" fill="#3a3fb0" opacity=".7"/><ellipse cx="560" cy="70" rx="160" ry="44" fill="#7a2f8f" opacity=".6"/>',
            '<ellipse cx="420" cy="50" rx="110" ry="34" fill="#b2305a" opacity=".7"/>',
            '<ellipse cx="430" cy="52" rx="40" ry="16" fill="#ffd0e0" opacity=".8"/>'), sky['neb']))
    if sky['stars']:
        o.append(stars([(80, 30, 3, '#fff'), (220, 80, 2, '#cfd8ff'), (520, 22, 3, '#fff'), (700, 64, 2, '#fff')], sky['stars']))
    o.append(f'<path d="M0 196v-56h40v-8h56v8h80v-6h120v6h104v-8h140v8h120v-6h144v62z" fill="{sky["hill"]}"/>')
    o.append(rect(0, 168, W_, 28, '#22402f') + rect(0, 168, W_, 3, '#33583f'))
    o.append(tree(10, 45, 2.8) + tree(246, 80, 2))
    o.append(bushes([('c', 40, 170), ('b', 250, 170), ('d', 720, 170)]))
    if sky['lamp']:
        o.append(f'<g opacity="{sky["lamp"]}">' + ''.join(rect(x, y, 4, 4, '#e8f59a', f' class="ff" style="animation-delay:{d}s"') for x, y, d in [(260, 120, .7), (460, 104, 2.2), (640, 130, 1.3)]) + '</g>')
    if asleep:
        o.append(f'<g transform="translate(146 84) scale(4)">{sp.shiba_front(True)}</g>')
        o.append(text(236, 110, 'z', 18, '#f6eedd', 700, cls='zz') + text(246, 98, 'Z', 24, '#f6eedd', 700, cls='zz', style='animation-delay:1.6s'))
    else:
        o.append(bubble_group(['bye bye! come back soon', 'woof woof!', 'leave a star? pretty please', 'see you next commit~'], 160, 30, tail_x=26))
        o.append(f'<g class="hop"><g transform="translate(146 84)"><g class="tilt"><g transform="scale(4)">{sp.shiba_front(False)}</g></g></g></g>')
    o.append(text(W_ - 36, 128, BYE[ph], 20, sky['ink'], anchor='end', shadow=(2, 2, sky['shadow'])))
    return ''.join(o)

# ================================================================ page


CSS = """
text{font-family:%(font)s}
@keyframes nebA{0%%,100%%{transform:translate(0,0) scale(1) rotate(0)}33%%{transform:translate(-70px,18px) scale(1.15) rotate(-4deg)}66%%{transform:translate(40px,-14px) scale(.95) rotate(3deg)}}
@keyframes nebB{0%%,100%%{transform:translate(0,0) scale(1.05) rotate(0)}50%%{transform:translate(64px,-16px) scale(.88) rotate(5deg)}}
@keyframes breathe{0%%,100%%{opacity:.4}50%%{opacity:1}}
@keyframes twinkle{0%%,100%%{opacity:.25}50%%{opacity:1}}
@keyframes shoot{0%%,86%%{transform:translate(0,0);opacity:0}88%%{opacity:1}96%%,100%%{transform:translate(-280px,140px);opacity:0}}
@keyframes drift{from{transform:translateX(0)}to{transform:translateX(-808px)}}
@keyframes sunpulse{0%%,100%%{opacity:.5}50%%{opacity:.85}}
@keyframes wag{0%%,100%%{transform:rotate(-14deg)}50%%{transform:rotate(10deg)}}
@keyframes wag2{0%%,100%%{transform:rotate(-16deg)}50%%{transform:rotate(12deg)}}
@keyframes blinkEye{0%%,92%%,100%%{transform:scaleY(1)}95%%{transform:scaleY(.15)}}
@keyframes hop{0%%,80%%,100%%{transform:translateY(0)}86%%{transform:translateY(-6px)}92%%{transform:translateY(0)}}
@keyframes tilt{0%%,60%%,100%%{transform:rotate(0)}70%%,85%%{transform:rotate(-6deg)}}
@keyframes heart{0%%,70%%{transform:translateY(0);opacity:0}75%%{opacity:1}100%%{transform:translateY(-22px);opacity:0}}
@keyframes grass{0%%,100%%{transform:skewX(0)}50%%{transform:skewX(-10deg)}}
@keyframes float{0%%,100%%{transform:translateY(0)}50%%{transform:translateY(-4px)}}
@keyframes firefly{0%%,100%%{opacity:.1;transform:translate(0,0)}50%%{opacity:1;transform:translate(6px,-8px)}}
@keyframes lamp{0%%,100%%{opacity:.55}50%%{opacity:.9}}
@keyframes grow{from{transform:scaleY(0);opacity:0}to{transform:scaleY(1);opacity:1}}
@keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes zz{0%%{transform:translate(0,0);opacity:0}20%%{opacity:1}100%%{transform:translate(14px,-40px);opacity:0}}
@keyframes say{0%%{opacity:0;transform:translateY(4px)}3%%,22%%{opacity:1;transform:none}25%%,100%%{opacity:0;transform:translateY(4px)}}
@keyframes appledrop{0%%,60%%{transform:translate(0,0);opacity:0}62%%{opacity:1}74%%{transform:translate(0,58px)}79%%{transform:translate(4px,48px)}84%%{transform:translate(8px,58px)}94%%{opacity:1;transform:translate(8px,58px)}100%%{opacity:0;transform:translate(8px,58px)}}
@keyframes walk{from{transform:translateX(-90px)}to{transform:translateX(830px)}}
@keyframes bob{0%%,100%%{transform:translateY(0)}50%%{transform:translateY(-2px)}}
@keyframes legA{0%%,49%%{opacity:1}50%%,100%%{opacity:0}}
@keyframes legB{0%%,49%%{opacity:0}50%%,100%%{opacity:1}}
@keyframes leaffall{0%%{transform:translate(0,-30px) rotate(0)}25%%{transform:translate(34px,%(q1)spx) rotate(90deg)}50%%{transform:translate(-12px,%(q2)spx) rotate(180deg)}75%%{transform:translate(28px,%(q3)spx) rotate(270deg)}100%%{transform:translate(0,%(h)spx) rotate(360deg)}}
.nebA{transform-box:fill-box;transform-origin:center;animation:nebA 22s ease-in-out infinite}
.nebB{transform-box:fill-box;transform-origin:center;animation:nebB 28s ease-in-out infinite}
.breathe{animation:breathe 6s ease-in-out infinite}
.tw{animation:twinkle 3s ease-in-out infinite}
.shoot{animation:shoot 11s linear infinite}
.drift{animation:drift 90s linear infinite}
.sunpulse{animation:sunpulse 6s ease-in-out infinite}
.wag{transform-box:fill-box;transform-origin:0%% 100%%;animation:wag 1.1s ease-in-out infinite}
.wag2{transform-box:fill-box;transform-origin:100%% 100%%;animation:wag2 .7s ease-in-out infinite}
.eye{transform-box:fill-box;transform-origin:center;animation:blinkEye 4.5s steps(1) infinite}
.hop{animation:hop 5s steps(3) infinite}
.tilt{transform-box:fill-box;transform-origin:50%% 100%%;animation:tilt 7s steps(2) infinite}
.heart{animation:heart 5s ease-out infinite}
.grass{transform-box:fill-box;transform-origin:50%% 100%%;animation:grass 3.5s ease-in-out infinite}
.float{animation:float 4s steps(4) infinite}
.ff{animation:firefly 4s ease-in-out infinite}
.lamp{animation:lamp 3s ease-in-out infinite}
.grow{transform-box:fill-box;transform-origin:50%% 100%%;animation:grow 1.6s steps(4) both}
.cell{transform-box:fill-box;transform-origin:50%% 100%%;animation:grow .6s steps(3) both}
.fade{animation:fadein 1.2s ease-out both}
.zz{animation:zz 3.2s ease-out infinite}
.say{opacity:0;animation:say 16s ease-out infinite}
.apple{animation:appledrop 9s ease-in infinite}
.walk{animation:walk 30s linear infinite}
.bob{animation:bob .4s steps(2) infinite}
.legA{animation:legA .4s steps(1) infinite}
.legB{animation:legB .4s steps(1) infinite}
.leaf{animation:leaffall 48s linear infinite}
@media (prefers-reduced-motion:reduce){*{animation-duration:0s!important;animation-iteration-count:1!important;animation-delay:0s!important}}
"""


def font_face():
    for name in ('PixelifySans.ttf', 'PixelifySans[wght].ttf'):
        path = os.path.join(ROOT, 'fonts', name)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode()
            return f"@font-face{{font-family:'Pixelify Sans';src:url(data:font/ttf;base64,{data}) format('truetype');font-weight:400 700}}"
    return ''


def nine_slice(tile, prefix, x, y, w, h, t=16, unit=2):
    """Draw a 24x24-unit nine-slice tile around the box (x,y,w,h), slice thickness t px."""
    s = t // unit  # slice size in units (8)
    regions = {
        'tl': (0, 0), 'tr': (2 * s, 0), 'bl': (0, 2 * s), 'br': (2 * s, 2 * s),
        't': (s, 0), 'b': (s, 2 * s), 'l': (0, s), 'r': (2 * s, s),
    }
    defs = ''.join(
        f'<g id="{prefix}{k}" transform="scale({unit})">{sp.paths_from_rects(sp.clip_rects(tile, rx, ry, rx + s, ry + s))}</g>'
        for k, (rx, ry) in regions.items())
    o = []
    o.append(f'<use href="#{prefix}tl" x="{x}" y="{y}"/><use href="#{prefix}tr" x="{x + w - t}" y="{y}"/>'
             f'<use href="#{prefix}bl" x="{x}" y="{y + h - t}"/><use href="#{prefix}br" x="{x + w - t}" y="{y + h - t}"/>')
    o.append(f'<clipPath id="{prefix}cx"><rect x="{x + t}" y="{y}" width="{w - 2 * t}" height="{h}"/></clipPath>'
             f'<clipPath id="{prefix}cy"><rect x="{x}" y="{y + t}" width="{w}" height="{h - 2 * t}"/></clipPath>')
    o.append(f'<g clip-path="url(#{prefix}cx)">')
    for xx in range(x + t, x + w - t, t):
        o.append(f'<use href="#{prefix}t" x="{xx}" y="{y}"/><use href="#{prefix}b" x="{xx}" y="{y + h - t}"/>')
    o.append(f'</g><g clip-path="url(#{prefix}cy)">')
    for yy in range(y + t, y + h - t, t):
        o.append(f'<use href="#{prefix}l" x="{x}" y="{yy}"/><use href="#{prefix}r" x="{x + w - t}" y="{yy}"/>')
    o.append('</g>')
    return defs, ''.join(o)


def build(ph, now, total, weeks):
    sky = SKIES[ph]
    night_ground = ph in ('sunset', 'night')
    body, deco = [], []
    y = PAD

    # header
    hh = 408
    body.append(wood(X0, y, CW, hh, bg=None))
    body.append(f'<g transform="translate({X0 + 6} {y + 6})" clip-path="url(#clipHeader)">{header_scene(ph, sky, now)}</g>')
    deco.append(wood_deco(X0, y, CW, hh))
    y += hh + 44

    # about
    s, sh = sign(X0, y, 'a little about me', icon=True)
    body.append(s)
    y += sh + 28
    lines = []
    for item in ABOUT:
        for i, ln in enumerate(wrap(item, 19, CW - 12 - 48 - 22)):
            lines.append(('~ ' if i == 0 else '  ') + ln)
    ah = 12 + 40 + len(lines) * 28 + 4
    body.append(wood(X0, y, CW, ah))
    for i, ln in enumerate(lines):
        delay = .2 + i * .4
        if ln.startswith('~ '):
            body.append(f'<g class="fade" style="animation-delay:{delay:.1f}s">' + text(X0 + 30, y + 46 + i * 28, '~', 19, '#8fc27a') + text(X0 + 52, y + 46 + i * 28, ln[2:], 19, '#efe6d6') + '</g>')
        else:
            body.append(f'<g class="fade" style="animation-delay:{delay:.1f}s">' + text(X0 + 52, y + 46 + i * 28, ln.strip(), 19, '#efe6d6') + '</g>')
    deco.append(wood_deco(X0, y, CW, ah))
    y += ah + 44

    # backpack
    s, sh = sign(X0, y, 'things in my backpack')
    body.append(s)
    y += sh + 28
    tw_, th = (CW - 3 * 14) / 4, 52
    for i, (name, col) in enumerate(BACKPACK):
        cx, cy = X0 + (i % 4) * (tw_ + 14), y + (i // 4) * (th + 16)
        body.append(f'<g class="float" style="animation-delay:{(i * .5) % 4:.2f}s">' + plank_box(round(cx), cy, round(tw_), th)
                    + rect(round(cx) + 18, cy + 19, 14, 14, col) + text(round(cx) + 42, cy + 32, name, 19, '#efe6d6') + '</g>')
    y += 3 * th + 2 * 16 + 44

    # projects
    s, sh = sign(X0, y, "little things i'm growing")
    body.append(s)
    y += sh + 28
    cw_ = (CW - 36) // 2
    plants = [
        [(2, 1, 1, 4, '#4d9a5a'), (0, 1, 2, 1, '#8fc27a'), (3, 0, 2, 1, '#8fc27a'), (3, 2, 1, 1, '#8fc27a')],
        [(2, 1, 1, 4, '#4d9a5a'), (1, 0, 3, 1, '#f2a3c8'), (2, 0, 1, 1, '#f4d06f'), (3, 3, 2, 1, '#8fc27a')],
        [(2, 2, 1, 3, '#4d9a5a'), (1, 1, 1, 1, '#8fc27a'), (3, 1, 1, 1, '#8fc27a'), (2, 0, 1, 2, '#8fc27a')],
        [(2, 1, 1, 4, '#4d9a5a'), (3, 1, 2, 1, '#8fc27a'), (0, 3, 2, 1, '#8fc27a'), (1, 0, 3, 1, '#efe6d6')],
    ]
    descs = [wrap(p[1], 17, cw_ - 12 - 36 - 56) for p in PROJECTS]
    ch = 12 + 36 + 28 + max(len(d) for d in descs) * 24 + 8 + 22
    for i, (name, desc, lang, col, _) in enumerate(PROJECTS):
        cx, cy = X0 + (i % 2) * (cw_ + 36), y + (i // 2) * (ch + 36)
        body.append(wood(cx, cy, cw_, ch))
        body.append(f'<g class="grow" style="animation-delay:{i * .4:.1f}s"><g transform="translate({cx + 24} {cy + 24}) scale(8)">{sp.paths_from_rects(plants[i])}</g></g>'
                    + f'<g transform="translate({cx + 24} {cy + 24}) scale(8)">{sp.paths_from_rects([(1, 5, 3, 1, "#a0603a")])}</g>')
        tx = cx + 24 + 56
        body.append(text(tx, cy + 46, name, 22, '#f6eedd', 700))
        for j, ln in enumerate(descs[i]):
            body.append(text(tx, cy + 76 + j * 24, ln, 17, '#bdb5cf'))
        ly = cy + 76 + len(descs[i]) * 24 + 8
        body.append(rect(tx, ly - 10, 10, 10, col) + text(tx + 16, ly, lang, 15, '#bdb5cf'))
        deco.append(wood_deco(cx, cy, cw_, ch))
    y += 2 * ch + 36 + 44

    # commit garden
    gh = 336
    body.append(wood(X0, y, CW, gh, bg=None))
    body.append(f'<g transform="translate({X0 + 6} {y + 6})" clip-path="url(#clipGarden)">{garden_scene(ph, sky, total, weeks)}</g>')
    deco.append(wood_deco(X0, y, CW, gh))
    y += gh + 44

    # connect + footer
    s, sh = sign(X0, y, 'come say hi')
    body.append(s)
    y += sh + 28
    bx = X0
    for name in LINKS:
        bw = int(tw(name, 18)) + 40
        body.append(plank_box(bx, y, bw, 44) + text(bx + 20, y + 28, name, 18, '#efe6d6'))
        bx += bw + 16
    y += 44 + 36
    fh = 208
    body.append(wood(X0, y, CW, fh, bg=None))
    body.append(f'<g transform="translate({X0 + 6} {y + 6})" clip-path="url(#clipFooter)">{footer_scene(ph, sky)}</g>')
    deco.append(wood_deco(X0, y, CW, fh))
    clip_footer = f'<clipPath id="clipFooter"><rect width="{CW - 12}" height="{fh - 12}"/></clipPath>'
    y += fh + PAD + 8
    H = y

    vine_defs, vines = nine_slice(sp.vine_tile(), 'v', 0, 0, W, H)
    path_defs, path = nine_slice(sp.path_tile(), 'p', 16, 16, W - 32, H - 32)

    leaves = []
    lc = [('#6fb55f', '#4d9a5a', 90, 0, 48), ('#e0a24a', '#c4823a', 260, -12, 56), ('#f2a3c8', None, 420, -30, 44), ('#8fc27a', '#6fb55f', 560, -22, 52),
          ('#f4d06f', None, 700, -6, 60), ('#d9773f', '#b85f2e', 800, -38, 50), ('#4d9a5a', '#3f8253', 30, -44, 58)]
    for c1, c2, x, delay, dur in lc:
        if c2:
            shape = sp.paths_from_rects([(a, b, w_, h_, c1) for a, b, w_, h_ in sp.LEAF] + [(1, 2, 5, 1, c2), (6, 4, 1, 2, '#6e4527')])
        else:
            shape = sp.paths_from_rects([(a, b, w_, h_, c1) for a, b, w_, h_ in sp.PETAL] + [(1, 1, 1, 1, '#ffffff')])
        leaves.append(f'<g class="leaf" style="animation-delay:{delay}s;animation-duration:{dur}s"><g transform="translate({x} -30) scale(2)">{shape}</g></g>')

    tile = sp.farm_tile('night' if night_ground else 'day')
    dim = ' filter="url(#dim)"' if night_ground else ''
    defs = (
        f'<pattern id="lawn" width="512" height="512" patternUnits="userSpaceOnUse"><g transform="scale(4)">{tile}</g></pattern>'
        '<pattern id="plankH" width="20" height="6" patternUnits="userSpaceOnUse"><rect width="18" height="6" fill="#a8733f"/><rect x="18" width="2" height="6" fill="#8f5f33"/></pattern>'
        '<pattern id="plankV" width="6" height="20" patternUnits="userSpaceOnUse"><rect width="6" height="18" fill="#a8733f"/><rect y="18" width="6" height="2" fill="#8f5f33"/></pattern>'
        '<pattern id="plankSign" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="10" fill="#a8733f"/><rect y="10" width="12" height="2" fill="#8f5f33"/></pattern>'
        f'<linearGradient id="hSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky["top"]}"/><stop offset=".6" stop-color="{sky["mid"]}"/><stop offset="1" stop-color="{sky["bot"]}"/></linearGradient>'
        f'<linearGradient id="gSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky["top"]}"/><stop offset="1" stop-color="{sky["mid"]}"/></linearGradient>'
        '<radialGradient id="sunGlow"><stop offset="0" stop-color="#fff6c8" stop-opacity=".7"/><stop offset="1" stop-color="#fff6c8" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="lampGlow"><stop offset="0" stop-color="#f4b860" stop-opacity=".55"/><stop offset="1" stop-color="#f4b860" stop-opacity="0"/></radialGradient>'
        + wisp_filter('wispH', 7, (0.011, 0.018), 90) + wisp_filter('wispG', 11, (0.012, 0.02), 80) + wisp_filter('wispF', 3, (0.012, 0.02), 80)
        + '<filter id="dim"><feColorMatrix type="matrix" values=".55 0 0 0 0  0 .55 0 0 0  0 0 .6 0 0  0 0 0 1 0"/></filter>'
        + f'<g id="tree">{sp.apple_tree()}</g>'
        + ''.join(f'<g id="c{i}">{sp.paths_from_rects(c)}</g>' for i, c in enumerate(sp.CELLS))
        + f'<clipPath id="clipHeader"><rect width="{CW - 12}" height="{hh - 12}"/></clipPath>'
        + f'<clipPath id="clipGarden"><rect width="{CW - 12}" height="{gh - 12}"/></clipPath>' + clip_footer
        + vine_defs + path_defs
    )
    css = CSS % {'font': FONT, 'h': H + 60, 'q1': H // 4, 'q2': H // 2, 'q3': 3 * H // 4}
    title = f"Sam Huang's pixel garden ({ph})"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" shape-rendering="crispEdges" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><style>{font_face()}{css}</style><defs>{defs}</defs>'
            f'<rect width="{W}" height="{H}" fill="url(#lawn)"/>'
            f'<g{dim}>{path}</g>'
            + ''.join(body) + ''.join(deco) + ''.join(leaves)
            + f'<g{dim}>{vines}</g></svg>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=list(SKIES))
    ap.add_argument('--sample', action='store_true', help='use fake contribution data')
    ap.add_argument('--out', default=os.path.join(ROOT, 'assets', 'garden.svg'))
    args = ap.parse_args()

    now = nl_now()
    ph = args.phase or phase_for(now.hour)
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if args.sample or not token:
        total, weeks = sample_calendar()
        if not args.sample:
            print('no token: using sample contribution data', file=sys.stderr)
    else:
        try:
            total, weeks = fetch_calendar(token)
        except Exception as e:  # never fake data in the live README: fall back to an empty garden
            print(f'contribution query failed ({e}); drawing an empty garden', file=sys.stderr)
            total, weeks = 0, [[0] * 7 for _ in range(53)]

    svg = build(ph, now, total, weeks)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'wrote {args.out} ({len(svg) // 1024} KB, phase={ph})')


if __name__ == '__main__':
    main()
