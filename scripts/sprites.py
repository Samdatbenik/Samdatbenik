"""Pixel-art sprites for the profile README (all drawn on a unit grid).

Every function returns SVG markup in sprite units; callers scale it with a transform.
"""
import math
import random

# ---------------------------------------------------------------- helpers

def paths_from_rects(rects):
    """rects: iterable of (x, y, w, h, colour) -> compact <path> per colour."""
    by = {}
    for x, y, w, h, c in rects:
        by.setdefault(c, []).append(f'M{x} {y}h{w}v{h}h-{w}z')
    return ''.join(f'<path d="{"".join(v)}" fill="{k}"/>' for k, v in by.items())


def ascii_rects(rows, pal, only=None, skip=None):
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            c = row[x]
            ok = lambda xx: (only is None or (xx, y) in only) and (skip is None or (xx, y) not in skip)
            if c == '.' or not ok(x):
                x += 1
                continue
            s = x
            while x < len(row) and row[x] == c and ok(x):
                x += 1
            out.append((s, y, x - s, 1, pal[c]))
    return out


# ---------------------------------------------------------------- shiba

SHIBA_PAL = {
    'D': '#3a2218', 'O': '#e3894a', 'S': '#b9622f', 'L': '#f2a865',
    'W': '#fff1dc', 'C': '#e2c9a8', 'K': '#1e1410', 'H': '#ffffff',
    'P': '#f7a1ae', 'E': '#f0a6a0',
}

FRONT = [
    "..DD..............DD..",
    ".DOOD............DOOD.",
    ".DOED............DEOD.",
    ".DOEOD..........DOEOD.",
    ".DOEEODDDDDDDDDDOEEOD.",
    "DOOOOOLLLLLLLLLLOOOOOD",
    "DOOOLLWLLLLLLLLWLLOOOD",
    "DOOLLLLLLLLLLLLLLLLOOD",
    "DOOLLHKKLLLLLLHKKLLOOD",
    "DOOLLKKKLLLLLLKKKLLOOD",
    "DOOWLKKHLWKKWLKKHLWOOD",
    "DOWPPWWWWKWWKWWWWPPWOD",
    ".DWWWWWWWWKKWWWWWWWWD.",
    ".DCWWWWWWWWWWWWWWWWCD.",
    "..DDCCWWWWWWWWWWCCDD..",
    "....DOOWWWWWWWWOOD....",
    "...DSOOWWWWWWWWOOSD...",
    "...DSOOCWWWWWWCOOSD...",
    "...DSSOWWWDDWWWOSSD...",
    "...DSDWWWWDDWWWWDSD...",
    "...DDDCWWCDDCWWCDDD...",
    "....DDDDDDDDDDDDDD....",
]
TAIL_FRONT = ["." * 22] * 14 + [
    "..................DD..",
    "..................DOLD",
    "..................DWOD",
    "...................DOD",
    "...................DD.",
]
EYES = {(x, y) for y in (8, 9, 10) for x in (5, 6, 7, 14, 15, 16)}


def shiba_front(asleep=False):
    """22x22 units. Awake: wagging tail + blinking eyes. Asleep: closed eyes."""
    tail = paths_from_rects(ascii_rects(TAIL_FRONT, SHIBA_PAL))
    if not asleep:
        body = paths_from_rects(ascii_rects(FRONT, SHIBA_PAL, skip=EYES))
        eyes = paths_from_rects(ascii_rects(FRONT, SHIBA_PAL, only=EYES))
        return f'<g class="wag">{tail}</g>{body}<g class="eye">{eyes}</g>'
    rows = [list(r) for r in FRONT]
    for (x, y) in EYES:
        rows[y][x] = 'L'
    for (x, y) in [(5, 9), (7, 9), (6, 10), (14, 9), (16, 9), (15, 10)]:
        rows[y][x] = 'K'
    rows = [''.join(r) for r in rows]
    return tail + paths_from_rects(ascii_rects(rows, SHIBA_PAL))


SIDE = [
    "..............DD...DD...",
    ".............DOOD.DOOD..",
    ".............DOEODDOEOD.",
    "............DOOLLLLLLLOD",
    "............DOLLLWLLLLLD",
    "...........DOLLLLHKKLLLD",
    "...........DOLLLLKKKLWWD",
    "...........DOOLLLKKHWWKD",
    "...DDDDDDDDOOOWPPWWKWWD.",
    "..DOLLLLLLLLOOOWWWWWWD..",
    "..DOOOOOOOOOOOCWWWWCD...",
    "..DSOOOOOOOOOODDDDDD....",
    "..DSSOOOOOOOOOWWD.......",
    "...DSSCWWWWWWCSSD.......",
    "...DDSDDDDDDDDSDD.......",
    "........................",
    "........................",
]
TAIL_SIDE = ["." * 24] * 6 + [
    "..DD....................",
    ".DOLD...................",
    ".DWOD...................",
    "..DD....................",
] + ["." * 24] * 7
LEG_A = ["." * 24] * 15 + ["....DOD.......DOD.......", "....DWD.......DWD......."]
LEG_B = ["." * 24] * 15 + ["......DOD...DOD.........", "......DWD...DWD........."]


def shiba_side():
    """24x17 units, walking: wagging tail and two alternating leg frames."""
    p = lambda rows: paths_from_rects(ascii_rects(rows, SHIBA_PAL))
    return (f'<g class="wag2">{p(TAIL_SIDE)}</g>{p(SIDE)}'
            f'<g class="legA">{p(LEG_A)}</g><g class="legB">{p(LEG_B)}</g>')


HEART = paths_from_rects([
    (1, 0, 2, 1, '#f7a1ae'), (6, 0, 2, 1, '#f7a1ae'), (0, 1, 4, 1, '#f7a1ae'), (5, 1, 4, 1, '#f7a1ae'),
    (0, 2, 9, 2, '#f7a1ae'), (1, 4, 7, 1, '#f7a1ae'), (2, 5, 5, 1, '#f7a1ae'), (3, 6, 3, 1, '#f7a1ae'),
    (4, 7, 1, 1, '#f7a1ae'), (1, 1, 1, 1, '#ffffff'),
])


# ---------------------------------------------------------------- apple tree

def apple_tree():
    """36x44 units: clumpy canopy, 5-tone shading lit from the top-left, apples, bark."""
    circles = [(18, 13, 10), (9, 18, 8), (27, 18, 8), (12, 9, 7), (24, 9, 7), (18, 22, 9), (6, 13, 5), (30, 12, 5)]
    W, H = 36, 44

    def inside(x, y):
        return any((x - cx) ** 2 + (y - cy) ** 2 <= r * r for cx, cy, r in circles)

    def shade(x, y):
        best = None
        for cx, cy, r in circles:
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                v = ((x - cx) + (y - cy) * 1.2) / r
                if best is None or cy > best[1]:
                    best = (v, cy)
        return best[0]

    R = [(7, 42, 22, 2, '#2f5a33')]
    for y in range(24, 44):
        flare = max(0, y - 39)
        x0, x1 = 15 - flare, 20 + flare
        R += [(x0 - 1, y, 1, 1, '#2e1a10'), (x1 + 1, y, 1, 1, '#2e1a10'), (x0, y, 1, 1, '#9a6a3e'),
              (x0 + 1, y, x1 - x0 - 1, 1, '#7a4c2a'), (x1, y, 1, 1, '#4a2c1a')]
    R.append((13, 43, 10, 1, '#2e1a10'))
    R += [(x, y, 1, 2, '#4a2c1a') for x, y in [(17, 30), (18, 34), (16, 37), (18, 39)]]
    R += [(13, 29, 2, 1, '#7a4c2a'), (12, 28, 2, 1, '#7a4c2a'), (21, 29, 2, 1, '#7a4c2a'), (22, 28, 2, 1, '#4a2c1a')]
    for y in range(H):
        for x in range(W):
            if not inside(x, y) and any(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                R.append((x, y, 1, 1, '#1f3a26'))
    rnd = random.Random(3)
    tones = ['#9ad470', '#6fb55f', '#4d9a5a', '#3a7d48', '#2a5e38']
    cuts = [-0.6, -0.15, 0.35, 0.75]
    for y in range(H):
        for x in range(W):
            if not inside(x, y):
                continue
            v = shade(x, y)
            i = sum(v > c for c in cuts)
            if min(abs(v - c) for c in cuts) < 0.09 and (x + y) % 2 == 0:
                i = min(4, i + 1)
            if not inside(x, y + 1):
                i = min(4, i + 1)
            if i <= 2 and rnd.random() < 0.08:
                i += 1
            R.append((x, y, 1, 1, tones[i]))
    for (x, y) in [(7, 20), (26, 23), (13, 13), (22, 11), (17, 27), (30, 16), (9, 10)]:
        R += [(x + 1, y - 1, 1, 1, '#5d3a20'), (x, y, 2, 2, '#d8423e'), (x, y, 1, 1, '#ff8a7a'), (x + 1, y + 1, 1, 1, '#a8302c')]
    return paths_from_rects(R)


# ---------------------------------------------------------------- tiles

FARM_PAL = {
    'day': dict(base='#4f8f4a', alt='#4b8a47', dark='#3f7a3d', light='#6aa85e', soil='#7a5233', soilHi='#8a6140',
                soilLo='#664328', edge='#5c3d24', leaf='#6fb55f', leafD='#4d9a5a', leafL='#a8d88a', carrot='#e8823a',
                tomato='#e0504a', pump='#e8923a', pumpD='#c9762a', pink='#f2a3c8', yellow='#f4d06f', white='#fff1dc',
                stone='#8a8f7a', stoneHi='#a4a994'),
    'night': dict(base='#1f3a2c', alt='#1d3729', dark='#172e22', light='#2c5238', soil='#3a2a22', soilHi='#46332a',
                  soilLo='#2e211a', edge='#261b15', leaf='#2f5a3c', leafD='#244830', leafL='#3f7050', carrot='#8a5a3a',
                  tomato='#8a3a3a', pump='#8f5a2e', pumpD='#734822', pink='#a86f8f', yellow='#a89a5a', white='#8c8a80',
                  stone='#3c4a42', stoneHi='#4a584f'),
}


def farm_tile(mode):
    """128x128 units: grass with two small vegetable beds, stones, tufts and flowers."""
    p = FARM_PAL[mode]
    rnd = random.Random(7)
    R = [(0, 0, 128, 128, p['base'])]
    px = lambda x, y, w, h, c: R.append((x, y, w, h, p[c]))
    S = 128
    for _ in range(40):
        px(rnd.randrange(S), rnd.randrange(S), rnd.choice([6, 8, 10]), rnd.choice([4, 6]), 'alt')

    def plot(x0, y0, w, rows):
        h = rows * 6 + 2
        px(x0 - 1, y0 - 1, w + 2, h + 2, 'edge')
        px(x0, y0, w, h, 'soil')
        for r in range(rows):
            ry = y0 + r * 6
            px(x0, ry + 4, w, 1, 'soilHi')
            px(x0, ry + 5, w, 1, 'soilLo')
            for i, cx in enumerate(range(x0 + 2, x0 + w - 3, 6)):
                kind = (r + i) % 3
                if kind == 0:
                    px(cx + 1, ry, 1, 3, 'leaf'); px(cx, ry + 1, 1, 2, 'leaf'); px(cx + 2, ry + 1, 1, 2, 'leaf'); px(cx, ry + 3, 3, 1, 'carrot')
                elif kind == 1:
                    px(cx, ry + 1, 4, 3, 'leaf'); px(cx + 1, ry, 2, 1, 'leaf'); px(cx + 1, ry + 2, 2, 1, 'leafD'); px(cx + 1, ry + 1, 1, 1, 'leafL')
                elif r % 2 == 0:
                    px(cx + 1, ry - 1, 1, 5, 'leafD'); px(cx, ry, 1, 1, 'leaf'); px(cx + 2, ry + 1, 1, 1, 'leaf')
                    px(cx + 2, ry + 2, 2, 2, 'tomato'); px(cx - 1, ry + 2, 2, 1, 'tomato')
                else:
                    px(cx, ry + 1, 4, 3, 'pump'); px(cx + 1, ry, 2, 1, 'pump'); px(cx + 2, ry + 1, 1, 3, 'pumpD'); px(cx + 2, ry - 1, 1, 1, 'leafD')

    plot(18, 30, 30, 3)
    plot(96, 92, 24, 2)
    for (x, y) in [(60, 20), (110, 50), (30, 110), (100, 8)]:
        px(x, y, 3, 2, 'stone'); px(x, y, 2, 1, 'stoneHi')
    occupied = lambda x, y: (17 <= x <= 49 and 29 <= y <= 49) or (95 <= x <= 121 and 91 <= y <= 106)
    for _ in range(90):
        x, y = rnd.randrange(S - 2), rnd.randrange(S - 2)
        if occupied(x, y):
            continue
        c = rnd.choice(['dark', 'dark', 'light'])
        px(x, y, 1, 2, c); px(x + 1, y + 1, 1, 1, c)
    for _ in range(14):
        x, y = rnd.randrange(S - 2), rnd.randrange(S - 2)
        if occupied(x, y):
            continue
        c = rnd.choice(['pink', 'yellow', 'white'])
        px(x, y, 2, 2, c); px(x, y, 1, 1, 'yellow' if c != 'yellow' else 'white'); px(x, y + 2, 1, 1, 'dark')
    return paths_from_rects(R)


def vine_tile():
    """24x24 unit nine-slice tile (8-unit slices): a leafy vine running along every edge."""
    S, L1, L2, D, P, Y = '#5d7d3a', '#4d9a5a', '#6fb55f', '#3f8253', '#f2a3c8', '#f4d06f'
    top = [
        (3, 3, 5, 1, S), (8, 3, 2, 1, S), (10, 4, 4, 1, S), (14, 3, 2, 1, S), (16, 3, 5, 1, S),
        (2, 2, 1, 1, S), (1, 1, 1, 1, L1), (5, 1, 2, 2, L1), (5, 1, 1, 1, L2), (6, 4, 2, 2, D),
        (9, 1, 2, 2, L1), (9, 1, 1, 1, L2), (12, 5, 2, 2, L1), (13, 6, 1, 1, D),
        (15, 1, 2, 2, L2), (18, 4, 2, 2, L1), (19, 1, 1, 2, D), (12, 2, 1, 1, P), (7, 6, 1, 1, Y),
    ]
    rects = []
    for (x, y, w, h, c) in top:
        rects += [(x, y, w, h, c), (x, 24 - y - h, w, h, c), (y, x, h, w, c), (24 - y - h, x, h, w, c)]
    return rects


def path_tile():
    """24x24 unit nine-slice tile: gravel with offset flagstones and creeping grass."""
    G, F, FH, FL, T = '#a8956e', '#b9b4a4', '#d6d2c4', '#8f8a7c', '#3f7a3d'
    inside = lambda x, y: 8 <= x < 16 and 8 <= y < 16
    rects = [(0, 0, 24, 8, G), (0, 16, 24, 8, G), (0, 8, 8, 8, G), (16, 8, 8, 8, G)]
    for row, y in enumerate(range(0, 24, 4)):
        off = (row % 2) * 2
        for x in range(-2 + off, 24, 4):
            cells = [(xx, yy) for xx in range(x, x + 3) for yy in range(y, y + 3) if 0 <= xx < 24 and not inside(xx, yy)]
            if len(cells) < 9:
                continue
            rects += [(x, y, 3, 3, F), (x, y, 3, 1, FH), (x + 2, y + 1, 1, 2, FL)]
    for i in range(1, 24, 5):
        rects += [(i, 0, 1, 1, T), (i, 23, 1, 1, T), (0, i, 1, 1, T), (23, i, 1, 1, T)]
    rects += [(x, y, 1, 1, T) for x, y in [(9, 7), (13, 7), (7, 10), (7, 14), (16, 9), (16, 13), (10, 16), (14, 16)]]
    return rects


def clip_rects(rects, x0, y0, x1, y1):
    """Rects clipped to the unit region [x0,x1)x[y0,y1), shifted to the region origin."""
    out = []
    for x, y, w, h, c in rects:
        ax, ay, bx, by = max(x, x0), max(y, y0), min(x + w, x1), min(y + h, y1)
        if ax < bx and ay < by:
            out.append((ax - x0, ay - y0, bx - ax, by - ay, c))
    return out


# ---------------------------------------------------------------- garden cells (5x5 units)

CELLS = [
    [(0, 0, 5, 5, '#241f38'), (1, 3, 1, 1, '#332c4d')],
    [(0, 0, 5, 5, '#1f3a2c'), (2, 2, 1, 3, '#4d9a5a'), (1, 2, 1, 1, '#8fc27a')],
    [(0, 0, 5, 5, '#1f3a2c'), (1, 1, 1, 4, '#6fb55f'), (3, 2, 1, 3, '#4d9a5a'), (2, 3, 1, 2, '#8fc27a')],
    [(0, 0, 5, 5, '#1f3a2c'), (2, 2, 1, 3, '#4d9a5a'), (1, 1, 3, 1, '#f2a3c8'), (2, 0, 1, 3, '#f2a3c8'), (2, 1, 1, 1, '#f4d06f')],
    [(0, 0, 5, 5, '#1f3a2c'), (0, 1, 5, 4, '#3f8253'), (1, 0, 3, 1, '#6fb55f'), (1, 2, 1, 1, '#f4d06f'), (3, 1, 1, 1, '#f2a3c8'), (3, 3, 1, 1, '#f2a3c8')],
]

LEAF = [(2, 0, 4, 1), (1, 1, 6, 1), (0, 2, 7, 1), (1, 3, 6, 1), (2, 4, 4, 1)]
PETAL = [(1, 0, 3, 1), (0, 1, 5, 3), (1, 4, 3, 1)]
