"""Code ligatures for Heliopause Mono.

Every glyph stays one cell wide. A ligature of n characters becomes n-1
empty LIG spacers followed by one glyph whose drawing reaches back over
the spacers' cells (it spans x = -(n-1)*600 .. 600). Ligatures live in
`calt`, so they switch off with `font-variant-ligatures: none` or an
editor's ligature setting.

They never fire next to another operator character, so runs like
`<!--`, `-->`, `====` or `>>=` stay as plain characters.
"""
import math

from geom import PI, rect, poly, clip_half, diag, diag_fit, rotate_fn
from glyphs import XH, AXIS, zigzag, dot
from mono import CELL

NAMES = {'-': 'hyphen', '>': 'greater', '<': 'less', '=': 'equal', '!': 'exclam',
         ':': 'colon', '|': 'bar'}
# characters that block a ligature when they touch it
JOIN = '<>=-!|:'

M = 70          # side margin, the same as the = sign's in its cell


def lig_name(seq):
    return '_'.join(NAMES[c] for c in seq) + '.liga'


def span(n):
    return -(n - 1) * CELL, CELL


def H(p):
    return p.H


def bar_off(p):
    """Half distance between the two bars of =, as Heliopause draws it."""
    return p.H / 2 + 50


def head(p, tip, direction, hh=None, w=None):
    """The arrow glyph's chevron head, tip at `tip`, pointing right (+1) or left (-1).
    Returns the contours and the two arms' centrelines."""
    hh = hh or 190 + 0.35 * p.g
    w = w or p.wd * 0.95
    cs, lines = zigzag([(-hh, -hh, 0), (0, 0, 0.55 * p.S), (hh, -hh, 0)], w)
    f = rotate_fn(0, 0, -90 * direction)
    g = lambda q: (f(q)[0] + tip[0], f(q)[1] + tip[1])
    return [c.map(g) for c in cs], [(g(a), g(b)) for a, b in lines]


def clip_to_arms(box, arms, keep):
    """Cut a bar so that it ends on the arms' centrelines, hidden inside the head."""
    pts = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
    for a, b in arms:
        pts = clip_half(pts, a, (b[0] - a[0], b[1] - a[1]), keep)
    return poly(pts)


def arrow(p, n, heads, double=False):
    x0, x1 = span(n)
    a, b = x0 + M, x1 - M
    out = []
    if double:
        o = bar_off(p)
        hh = o + p.H / 2 + 120
        ys = [AXIS - o, AXIS + o]
    else:
        hh = None
        ys = [AXIS]
    arms = []
    if heads[1]:
        cs, ln = head(p, (b, AXIS), +1, hh)
        out += cs
        arms += [(ln, (a, AXIS))]
    if heads[0]:
        cs, ln = head(p, (a, AXIS), -1, hh)
        out += cs
        arms += [(ln, (b, AXIS))]
    for y in ys:
        box = (a, y - p.H / 2, b, y + p.H / 2)
        pts = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
        for ln, keep in arms:
            for q0, q1 in ln:
                pts = clip_half(pts, q0, (q1[0] - q0[0], q1[1] - q0[1]), ((a + b) / 2, y))
        out.append(poly(pts))
    return out


def bars(p, n, k):
    """k parallel bars across n cells, centred on the maths axis."""
    x0, x1 = span(n)
    gap = 50 if k == 2 else 40
    pitch = p.H + gap
    ys = [AXIS + (i - (k - 1) / 2) * pitch for i in range(k)]
    return [(x0 + M, y - p.H / 2, x1 - M, y + p.H / 2) for y in ys]


def struck(p, n, k):
    """k bars broken around a slash with the orbital cross's gap."""
    x0, x1 = span(n)
    cx = (x0 + x1) / 2
    bs = bars(p, n, k)
    top = bs[-1][3] + 150
    bot = bs[0][1] - 150
    w = p.wd * 0.9
    t, b = diag_fit(cx + 150, top, cx - 150, bot, w, +1, -1)
    out = [diag(t, b, w)]
    d = (t[0] - b[0], t[1] - b[1])
    ln = math.hypot(*d)
    nrm = (-d[1] / ln, d[0] / ln)          # points to the upper left
    off = w / 2 + p.w('x.gap', 0.38 * p.S + 8)
    mid = ((t[0] + b[0]) / 2, (t[1] + b[1]) / 2)
    for (ax, ay, bx, by) in bs:
        pts = [(ax, ay), (bx, ay), (bx, by), (ax, by)]
        left = clip_half(pts, (mid[0] + nrm[0] * off, mid[1] + nrm[1] * off), d, (ax, (ay + by) / 2))
        right = clip_half(pts, (mid[0] - nrm[0] * off, mid[1] - nrm[1] * off), d, (bx, (ay + by) / 2))
        out += [poly(left), poly(right)]
    return out


def compare(p, direction):
    """>= and <=: a long chevron resting over a bar, across two cells."""
    x0, x1 = span(2)
    depth = 700
    hh = 175 + 0.2 * p.g
    w = p.wd * 0.92
    ychev = AXIS + 70
    cs, _ = zigzag([(0, 0, 0), (hh, depth, 0.45 * p.S), (2 * hh, 0, 0)], w)
    # zigzag draws it pointing up; turn it to point right (>) or left (<)
    f = rotate_fn(hh, 0, -90 * direction)
    tipx = (x0 + x1) / 2 + direction * depth / 2
    pts = []
    for c in cs:
        pts.append(c.map(lambda q: f(q)))
    # find the turned chevron's tip and move it into place
    xs = [q[0] for c in pts for q in c.flatten(4)]
    ys_ = [q[1] for c in pts for q in c.flatten(4)]
    tip_now = max(xs) if direction > 0 else min(xs)
    cy_now = (max(ys_) + min(ys_)) / 2
    dx, dy = tipx - tip_now, ychev - cy_now
    out = [c.map(lambda q: (q[0] + dx, q[1] + dy)) for c in pts]
    ybar = AXIS - hh - 80 + 70
    lo, hi = (x0 + x1) / 2 - depth / 2 - 20, (x0 + x1) / 2 + depth / 2 + 20
    out.append(rect(lo, ybar - p.H / 2, hi, ybar + p.H / 2))
    return out


def pipe(p, direction):
    """|> and <|: the bar and the chevron close into an outlined triangle."""
    x0, x1 = span(2)
    hh = 250 + 0.2 * p.g
    w = p.wd * 0.95
    S = p.S
    if direction > 0:
        xb = x0 + 330
        tip = x1 - 120
    else:
        xb = x1 - 330
        tip = x0 + 120
    out = [rect(xb - S / 2, AXIS - hh, xb + S / 2, AXIS + hh)]
    # each arm runs from the bar's outer end to the tip
    for sgn in (1, -1):
        y_end = AXIS + sgn * hh
        side = -direction                     # which corner of the bar the arm starts at
        xe = xb + side * S / 2
        t, b = (xe, y_end), (tip, AXIS)
        d = (b[0] - t[0], b[1] - t[1])
        k = 60 / math.hypot(*d)
        a = (t[0] - d[0] * k, t[1] - d[1] * k)
        e = (b[0] + d[0] * k, b[1] + d[1] * k)
        arm = diag(a, e, w, ('perp',), ('perp',))
        q = [arm.start] + [s[1] for s in arm.segs]
        q = q[:-1] if abs(q[-1][0] - q[0][0]) + abs(q[-1][1] - q[0][1]) < 1e-6 else q
        # trim flush with the bar's outer edge and the triangle's bounding lines
        q = clip_half(q, (xe, 0), (0, 1), (tip, AXIS))
        q = clip_half(q, (0, AXIS + hh), (1, 0), (tip, AXIS))
        q = clip_half(q, (0, AXIS - hh), (1, 0), (tip, AXIS))
        q = clip_half(q, (tip + direction * 0.0, 0), (0, 1), (xb, AXIS))
        out.append(poly(q))
    return out


def colons(p):
    """:: pulls the two colons together over the cell edge."""
    r = p.rd
    out = []
    for x in (-170, 170):
        out += [dot(x, r - 4, r), dot(x, XH - r + 4, r)]
    return out


DRAW = {
    '<->': lambda p: arrow(p, 3, (True, True)),
    '<=>': lambda p: arrow(p, 3, (True, True), double=True),
    '===': lambda p: [rect(*b) for b in bars(p, 3, 3)],
    '!==': lambda p: struck(p, 3, 3),
    '->': lambda p: arrow(p, 2, (False, True)),
    '<-': lambda p: arrow(p, 2, (True, False)),
    '=>': lambda p: arrow(p, 2, (False, True), double=True),
    '==': lambda p: [rect(*b) for b in bars(p, 2, 2)],
    '!=': lambda p: struck(p, 2, 2),
    '>=': lambda p: compare(p, +1),
    '<=': lambda p: compare(p, -1),
    '::': colons,
    '|>': lambda p: pipe(p, +1),
    '<|': lambda p: pipe(p, -1),
}
# longest first, so <-> wins over <- and ->
ORDER = sorted(DRAW, key=lambda s: -len(s))


def _draw(seq):
    def f(p, G):
        G.add(*DRAW[seq](p))
    return f


def _spacer(p, G):
    pass


LIGATURES = [('LIG', _spacer)] + [(lig_name(s), _draw(s)) for s in ORDER]


def calt_fea(glyphs):
    have = {g.name for g in glyphs}
    join = ' '.join(NAMES[c] for c in JOIN)
    out = [f'@JOIN = [{join}];']
    lookups = []
    for seq in ORDER:
        lig = lig_name(seq)
        if lig not in have:
            continue
        gs = [NAMES[c] for c in seq]
        n = len(gs)
        name = 'L_' + '_'.join(gs)
        body = [f"  ignore sub @JOIN {gs[0]}' {' '.join(gs[1:])};",
                f"  ignore sub {gs[0]}' {' '.join(gs[1:])} @JOIN;"]
        # the last character becomes the ligature, once all before it are spacers
        body.append(f"  sub {' '.join(['LIG'] * (n - 1))} {gs[-1]}' by {lig};")
        # earlier characters become spacers, in reverse so the longest backtrack is tried first
        for i in range(n - 2, -1, -1):
            back = ' '.join(['LIG'] * i)
            ahead = ' '.join(gs[i + 1:])
            body.append(f"  sub {back + ' ' if back else ''}{gs[i]}' {ahead} by LIG;")
        out.append(f'lookup {name} {{\n' + '\n'.join(body) + f'\n}} {name};')
        lookups.append(name)
    out.append('feature calt {\n' + '\n'.join(f'  lookup {n};' for n in lookups) + '\n} calt;')
    return '\n'.join(out) + '\n'
