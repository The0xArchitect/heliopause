"""Heliopause Mono: the Heliopause construction fitted to a 600-unit cell.

Every glyph Heliopause draws is drawn here by the same function, with the
width-bearing dimensions read from WIDTHS (via P.w) instead of growing with
weight. Glyphs whose proportional design can't live in a fixed cell (i l I
1 j f t r m w W M S @ & ellipsis arrows) are redrawn below with the same
pieces: arches, orbit bands, zigzags, signal dots.
"""
import copy
import math

from geom import PI, TAU, rect, poly, ellipse, ept, band, diag, diag_fit, Glyph, rotate_fn
from glyphs import (P, XH, CAP, ASC, DESC, OS, OSC, CY, RYO, AXIS, glyph_table, arch, zigzag,
                    s_shape, dot, f1, crossed_x, g_O, g_Oplain)

CELL = 600

# Width-bearing dimensions, constant across weights (heavier weights fill
# the counters instead of growing wider). A value may be a function of P.
WIDTHS = {
    # lowercase
    'j.rx': 165, 'k': 470, 'v': 500, 'y': 500, 'x': 490, 'z': 440,
    # capitals
    'Orx': 248, 'H': 480, 'N': 490, 'U': 490, 'A': 570, 'V': 540, 'X': 520, 'Y': 540,
    'Z': 470, 'K': 490, 'T': 500, 'M': 540,
    'L': 440, 'E': 450, 'E.mid': 420, 'E.bot': 460, 'F': 450, 'F.mid': 410,
    'D.xf': 240, 'D.rx': 250, 'B.xf': 235, 'B.rxu': 195, 'B.rxl': 230,
    'P.xf': 230, 'P.rx': 245, 'R.xf': 225, 'R.rx': 240, 'R.leg': 30, 'J.rx': 195,
    # symbols
    'hyphen': 360, 'endash': 480, 'emdash': CELL, 'underscore': CELL,
    'numbersign': 500, 'percent': 520, 'percent.r': lambda p: 122 + 0.3 * p.g,
    'tilde': 420, 'less': 400,
    'x.gap': lambda p: 0.24 * p.S + 8,
    'A.flat': lambda p: 0.4 * p.SC - 0.15 * p.g, 'A.yb': lambda p: 205 - 45 * p.t,
    # ampersand: a lighter, narrower build of the same construction
    'amp.Cs': lambda p: p.Cs * 0.95, 'amp.Ct': lambda p: p.Ct * 0.95,
    'amp.wd': lambda p: p.wd, 'amp.rxl': lambda p: 135 + 0.35 * p.g,
    'amp.ryl': lambda p: 150 + 0.3 * p.g, 'amp.xl': -70,
    'amp.rxb': lambda p: 200 + 0.1 * p.g, 'amp.xb': 10, 'amp.foot': 5,
}


class PMono(P):
    def __init__(self, S):
        super().__init__(S)
        self.brx = 250                 # lowercase bowl half width: o is 500 wide
        self.ncnt = 470 - 2 * S        # n, h, u: 470 wide at every weight
        self.fig = 590                 # figure construction width (as Heliopause Regular)
        self.R = self.fig / 2 - 50 - 0.1 * self.g
        # diagonals lighten a little with weight: the cell can't widen to
        # give heavy diagonal strokes room
        self.wd *= 1 - 0.08 * self.t
        self.wdC *= 1 - 0.1 * self.t

    def w(self, key, default):
        v = WIDTHS.get(key)
        if v is None:
            return default
        return v(self) if callable(v) else v


MONO = {}       # name -> (unicode, draw)

# Heliopause alternates the mono names differently. Heliopause's O carries
# the planet dot and ss04 gives O.plain; in code the dot has to mean zero,
# so the mono's O stays plain and its ss04 gives the dotted O.dot.
RENAME = {'O.plain': 'O.dot'}


def mono_glyph(name, uni=None):
    def deco(f):
        MONO[name] = (uni, f)
        return f
    return deco


# Optical horizontal shifts after the ink is centred in the cell.
DX = {
    'r': 22, 'f': 8, 'j': -18, 'l': -10, 't': -12, 'L': 18, 'F': 14, 'E': 10, 'P': 12,
    'one': -8, 'quotesingle': 0, 'parenleft': 40, 'parenright': -40,
    'bracketleft': 45, 'bracketright': -45, 'braceleft': 25, 'braceright': -25,
    'quoteright': 0, 'comma': 0, 'semicolon': 0, 'J': -12, 'question': 8,
    'questiondown': -8, 'C': 18, 'c': 14, 'G': 6, 'K': 10, 'k': 14,
}


# =====================================================================
# narrow letters: i l I 1 j f t r
# =====================================================================

def spur(p, x_right, y_top, length):
    """A flat spur running left from a stem, flush with its top."""
    return rect(x_right - length, y_top - p.H, x_right, y_top)


def orbit_foot(p, sL, top, ry=None, rx=None, end=-0.62):
    """A stem from `top` that rounds into a quarter orbit at the baseline,
    sweeping right: the j/f hook language turned to the foot."""
    S = p.S
    ryo = ry or 205
    rxo = rx or 205
    cy = ryo - OS
    cx = sL + rxo
    foot = band(cx, cy, rxo, ryo, rxo - S, ryo - p.Ct, ('a', PI - 0.02), ('a', TAU + end))
    return [rect(sL, cy, sL + S, top), foot]


@mono_glyph('i', 0x69)
def m_i(p, G):
    S = p.S
    sL = -S / 2 + 20
    G.add(rect(sL, 0, sL + S, XH), spur(p, sL + 1, XH, 150),
          rect(-205, 0, 215, p.H), dot(sL + S / 2, 770 - p.rd, p.rd))


@mono_glyph('l', 0x6C)
def m_l(p, G):
    S = p.S
    sL = -S / 2 - 50
    G.add(spur(p, sL + 1, ASC, 165), *orbit_foot(p, sL, ASC))


@mono_glyph('I', 0x49)
def m_I(p, G):
    S, H = p.SC, p.HC
    W = 390
    G.add(rect(-S / 2, 0, S / 2, CAP), rect(-W / 2, CAP - H, W / 2, CAP), rect(-W / 2, 0, W / 2, H))


@mono_glyph('one', 0x31)
def m_one(p, G):
    f1(p, G)
    c = -p.S / 2 + 40 + p.S / 2           # stem centre
    G.add(rect(c - 205, 0, c + 205, p.H))


@mono_glyph('j', 0x6A)
def m_j(p, G):
    S = p.S
    rxo = p.w('j.rx', 165)
    sR, sL = 0, -S
    ycT = -40
    ryo = ycT - (DESC - OS)
    tail = band(sR - rxo, ycT, rxo, ryo, rxo - S, ryo - p.Ct, ('a', 0.06), ('a', -2.45))
    G.add(rect(sL, ycT, sR, XH), tail, spur(p, sL + 1, XH, 165), dot(-S / 2, 770 - p.rd, p.rd))


@mono_glyph('f', 0x66)
def m_f(p, G):
    S = p.S
    sL = -S / 2 - 40
    rxo = 175
    ycH = ASC - 150 - 0.5 * p.g
    ryo = ASC + OS - ycH
    hook = band(sL + rxo, ycH, rxo, ryo, rxo - S, ryo - p.Ct, ('a', PI + 0.06), ('a', 0.5))
    G.add(rect(sL, 0, sL + S, ycH), hook, rect(-215, XH - p.H, 215, XH))


@mono_glyph('t', 0x74)
def m_t(p, G):
    S = p.S
    sL = -S / 2 - 50
    G.add(*orbit_foot(p, sL, 680, ry=190, rx=200), rect(-215, XH - p.H, 210, XH))


@mono_glyph('r', 0x72)
def m_r(p, G):
    W = 2 * p.S + p.ncnt * 0.98
    G.add(arch(p, 0, W, XH, right=('a', 0.55)))


# =====================================================================
# wide letters: m w W M
# =====================================================================

def lighter(p, k):
    """A copy of P with lighter stems, for letters with three or four."""
    q = copy.copy(p)
    q.S = p.S * k
    q.Ct = p.Ct * (0.5 + 0.5 * k)
    q.rn = 0.27 * q.S
    return q


@mono_glyph('m', 0x6D)
def m_m(p, G):
    q = lighter(p, 0.8)
    Wt = 520
    cm = (Wt - 3 * q.S) / 2
    w1 = 2 * q.S + cm
    G.add(arch(q, 0, w1, XH), arch(q, q.S + cm, q.S + cm + w1, XH, left='tangent'))


def mono_w(top, W, w, f, ymid):
    cs, _ = zigzag([(0, top, 0), (W * 0.25, 0, f), (W * 0.5, ymid, f), (W * 0.75, 0, f), (W, top, 0)], w)
    return cs


@mono_glyph('w', 0x77)
def m_w(p, G):
    G.add(*mono_w(XH, 560, p.wd * (0.82 - 0.12 * p.t), 0.26 * p.S, XH * 0.82))


@mono_glyph('W', 0x57)
def m_W(p, G):
    G.add(*mono_w(CAP, 560, p.wdC * (0.8 - 0.12 * p.t), 0.28 * p.SC, CAP * 0.72))


@mono_glyph('M', 0x4D)
def m_M(p, G):
    S = p.SC * 0.92
    W = p.w('M', 540)
    cs, _ = zigzag([(0, CAP, 0), (W / 2, CAP * 0.22, 0.42 * S), (W, CAP, 0)], p.wdC * 0.82)
    G.add(rect(0, 0, S, CAP), rect(W - S, 0, W, CAP), *cs)


@mono_glyph('S', 0x53)
def m_S(p, G):
    G.add(*s_shape(CAP + OSC, -OSC, 218, 236, p.CtC * 0.92, p.CsC * 0.92, share=0.47))


# =====================================================================
# symbols
# =====================================================================

@mono_glyph('asterisk', 0x2A)
def m_asterisk(p, G):
    # Heliopause's four-point star, grown to code size and lowered
    cx, cy = 0, 430
    Ro, Ri = 235, 52 + 0.4 * p.g
    pts = []
    for k in range(8):
        a = PI / 2 + k * PI / 4
        r = Ro if k % 2 == 0 else Ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    G.add(poly(pts))


@mono_glyph('ellipsis', 0x2026)
def m_ellipsis(p, G):
    r = min(p.rd, 52 + 0.35 * p.g)
    sp = (530 - 2 * r) / 2
    G.add(*[dot(i * sp, r - 4, r) for i in range(3)])


def arrow(p, L):
    """The up arrow with a shaft of length L (Heliopause's is the cap height)."""
    S = p.S
    head = 205 + 0.35 * p.g
    cs, _ = zigzag([(-head, L - head, 0), (0, L, 0.55 * S), (head, L - head, 0)], p.wd * 0.95)
    return [rect(-S / 2, 0, S / 2, L - 25)] + cs


@mono_glyph('arrowup', 0x2191)
def m_au(p, G):
    G.add(*arrow(p, CAP))


@mono_glyph('arrowdown', 0x2193)
def m_ad(p, G):
    G.add(*arrow(p, CAP))
    G.transform(rotate_fn(0, CAP / 2, 180))


@mono_glyph('arrowright', 0x2192)
def m_ar(p, G):
    G.add(*arrow(p, 520))
    G.transform(rotate_fn(0, 0, -90))
    G.transform(lambda q: (q[0], q[1] + AXIS))


@mono_glyph('arrowleft', 0x2190)
def m_al(p, G):
    G.add(*arrow(p, 520))
    G.transform(rotate_fn(0, 0, 90))
    G.transform(lambda q: (q[0], q[1] + AXIS))


@mono_glyph('at', 0x40)
def m_at(p, G):
    # the small a inside an elliptical orbit whose foot sweeps out of the stem
    S = p.S * (0.84 - 0.22 * p.t)            # lighter with weight: three rings in one cell
    th = S
    rx, ry = 268 - th / 2, 352 - th / 2       # outer ring centreline
    cy = 270
    rxo, ryo = 132, 168
    icx, icy = -14, cy
    rxi, ryi = rxo - S, ryo - S * 0.95
    sL = icx + max(rxi - 0.2 * S, rxo * 0.53)
    sR = sL + S
    G.add(ellipse(icx, icy, rxo, ryo)).hole(ellipse(icx, icy, rxi, ryi))
    foot_y = icy - ryo + 30
    G.add(rect(sL, foot_y, sR, icy + ryo - 10))
    xs = (sL + sR) / 2
    # solve the foot radius so its right end lands on the ring's centreline
    lo, hi = 5.0, 200.0
    for _ in range(50):
        rf = (lo + hi) / 2
        ex = xs + 2 * rf
        if (ex / rx) ** 2 + ((foot_y - cy) / ry) ** 2 > 1:
            hi = rf
        else:
            lo = rf
    fcx = xs + rf
    foot = band(fcx, foot_y, rf + th / 2, rf * 0.8 + th / 2, rf - th / 2, rf * 0.8 - th / 2,
                ('a', PI), ('a', TAU + 0.12))
    phi = math.atan2((foot_y - cy) / ry, (fcx + rf) / rx)
    outer = band(0, cy, rx + th / 2, ry + th / 2, rx - th / 2, ry - th / 2,
                 ('a', phi - 0.1), ('a', phi + TAU - 1.0))
    G.add(foot, outer)


# =====================================================================
# assembly
# =====================================================================

@mono_glyph('O', 0x4F)
def m_O(p, G):
    g_Oplain(p, G)


@mono_glyph('O.dot')
def m_Odot(p, G):
    g_O(p, G)


def build_mono_glyphs(S, extra=()):
    """Draw every glyph for stem S. `extra` is a list of (name, draw) for
    glyphs that keep their own advance and position (ligatures, spacers)."""
    p = PMono(S)
    out = []
    for name, (uni, sb, f) in glyph_table().items():
        name = RENAME.get(name, name)
        if name in MONO:
            uni, f = MONO[name][0] if MONO[name][0] is not None else uni, MONO[name][1]
        G = Glyph(name, [uni] if uni else [], sb)
        f(p, G)
        G.fixed = CELL
        G.empty_adv = CELL
        G.finalize(p.sb)
        if DX.get(name):
            dx = DX[name]
            G.transform(lambda q, dx=dx: (q[0] + dx, q[1]))
        out.append(G)
    for name, f in extra:
        G = Glyph(name, [], ('Z', 'Z'))
        f(p, G)
        G.raw = CELL
        G.finalize(p.sb)
        out.append(G)
    order = ['.notdef'] + [g.name for g in out if g.name != '.notdef']
    gd = {g.name: g for g in out}
    return [gd[n] for n in order], p
