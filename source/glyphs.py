"""Heliopause glyph designs.

Every glyph is a function of the weight parameters P, so Regular,
SemiBold and Bold are drawn by the same construction.
"""
import math
from geom import (Contour, PI, TAU, rect, poly, ellipse, ept, band, ell_speed,
                  notch, slot, diag, diag_hw, diag_fit, diag_pts, clip_half, isect,
                  rotate_fn, mirror_x, Glyph)

XH, CAP, ASC, DESC = 530, 700, 760, -230
OS, OSC = 12, 14
CY = XH / 2           # lowercase optical centre
RYO = XH / 2 + OS     # lowercase round outer half height


class P:
    def __init__(self, S):
        self.S = S
        t = (S - 86) / 60.0
        g = S - 86
        self.t, self.g = t, g
        self.H = S * 0.885
        self.Cs = S * 1.05
        self.Ct = self.H * 1.03
        self.rn = 0.27 * S
        self.rd = 0.56 * S + 9
        self.wd = S * 0.97
        self.SC = S * 1.06
        self.HC = self.H * 1.05
        self.CsC = self.SC * 1.05
        self.CtC = self.HC * 1.03
        self.wdC = self.SC * 0.97
        self.brx = 258 + 0.55 * g
        self.ncnt = 292 + 0.25 * g
        self.fig = 590 + 0.7 * g
        self.R = self.fig / 2 - 50 - 0.1 * g    # figure half width
        self.sb = {'S': 74 - 10 * t, 'R': 46 - 6 * t, 'D': 22 - 4 * t,
                   'T': 32 - 4 * t, 'Z': 0}


REG = []


def glyph(name, uni=None, sb=('S', 'S')):
    def deco(f):
        REG.append((name, uni, sb, f))
        return f
    return deco


# =====================================================================
# shared constructions
# =====================================================================

def dot_plan(crotch, u_edge, u_arc, r, push=0.45):
    """Round signal-gap dot cut into a crotch. u_edge / u_arc are unit
    directions pointing away from the crotch along the straight edge and
    along the curve. Returns (centre, dist along edge, dist along curve)."""
    b = (u_edge[0] + u_arc[0], u_edge[1] + u_arc[1])
    lb = math.hypot(*b)
    ink = (-b[0] / lb, -b[1] / lb)
    C = (crotch[0] + ink[0] * push * r, crotch[1] + ink[1] * push * r)
    v = (crotch[0] - C[0], crotch[1] - C[1])

    def hit(u):
        uv = u[0] * v[0] + u[1] * v[1]
        return -uv + math.sqrt(max(0.0, uv * uv - (v[0] ** 2 + v[1] ** 2) + r * r))
    return C, hit(u_edge), hit(u_arc), ink


def dot_arc(c, C, r, to_pt, ink):
    """From the current point, go round the dot circle through the ink side to to_pt."""
    f = c.cur()
    a0 = math.atan2(f[1] - C[1], f[0] - C[0])
    a1 = math.atan2(to_pt[1] - C[1], to_pt[0] - C[0])
    ai = math.atan2(ink[1], ink[0])
    d = (a1 - a0) % TAU
    if (ai - a0) % TAU < d:
        sweep = d
    else:
        sweep = d - TAU
    c.arc(C[0], C[1], r, r, a0, a0 + sweep)
    c.L(to_pt)
    return c


def _unit(x, y):
    l = math.hypot(x, y)
    return (x / l, y / l)


def bowl_stem(p, bot, top, rxo=None, notch_b=True, notch_t=True):
    """Round bowl with a stem on the right (a d g q). Bowl centre x=0.
    Round signal-gap dots sit in the two crotches. Returns (outer, hole, sL, sR)."""
    rxo = rxo or p.brx
    ryo, cy = RYO, CY
    rxi, ryi = rxo - p.Cs, ryo - p.Ct
    sL = max(rxi - 0.2 * p.S, rxo * math.cos(math.radians(58)))
    sR = sL + p.S
    al = math.acos(sL / rxo)
    yb = cy - ryo * math.sin(al)
    yt = cy + ryo * math.sin(al)
    tb, tt = -al, -(TAU - al)
    c = Contour((sL, top)).L((sR, top)).L((sR, bot)).L((sL, bot))
    # bottom crotch
    rb = min(p.rn, 0.85 * (yb - bot))
    if notch_b and rb >= 10:
        ua = _unit(rxo * math.sin(tb), -ryo * math.cos(tb))
        C, se, sa, ink = dot_plan((sL, yb), (0, -1), ua, rb)
        c.L((sL, yb - se))
        d = sa / ell_speed(rxo, ryo, tb)
        dot_arc(c, C, rb, ept(0, cy, rxo, ryo, tb - d), ink)
        ts = tb - d
    else:
        ts = tb
    rt = min(p.rn, 0.85 * (top - yt))
    if notch_t and rt >= 10:
        ua = _unit(-rxo * math.sin(tt), ryo * math.cos(tt))
        C, se, sa, ink = dot_plan((sL, yt), (0, 1), ua, rt)
        d = sa / ell_speed(rxo, ryo, tt)
        c.arc(0, cy, rxo, ryo, ts, tt + d)
        dot_arc(c, C, rt, (sL, yt + se), ink)
    else:
        c.arc(0, cy, rxo, ryo, ts, tt)
    c.L((sL, top)).close()
    if sL < rxi - 1:
        be = math.acos(sL / rxi)
        h = Contour(ept(0, cy, rxi, ryi, -be))
        h.arc(0, cy, rxi, ryi, -be, -(TAU - be)).close()
    else:
        h = ellipse(0, cy, rxi, ryi)
    return c, h, sL, sR


def arch(p, L0, R1, top_left, right='stem', left='stem', bottom=0, do_notch=True,
         yc=CY, ryo=RYO):
    """n-style arch: left stem, half-orbit arch, right stem (or a cut terminal)."""
    S = p.S
    L1, R0 = L0 + S, R1 - S
    cx = (L0 + R1) / 2
    rxo = (R1 - L0) / 2
    rxi, ryi = rxo - S, ryo - p.Ct
    c = Contour((L0, bottom))
    if left == 'stem':
        tc = PI - math.acos((rxo - S) / rxo)
        ycr = yc + ryo * math.sin(tc)
        c.L((L0, top_left)).L((L1, top_left))
        r = min(p.rn, 0.85 * (top_left - ycr))
        if do_notch and r >= 10:
            ua = _unit(rxo * math.sin(tc), -ryo * math.cos(tc))
            C, se, sa, ink = dot_plan((L1, ycr), (0, 1), ua, r)
            c.L((L1, ycr + se))
            d = sa / ell_speed(rxo, ryo, tc)
            dot_arc(c, C, r, ept(cx, yc, rxo, ryo, tc - d), ink)
            ts = tc - d
        else:
            c.L((L1, ycr))
            ts = tc
    else:
        c.L((L0, yc))
        ts = PI
    if right == 'stem':
        c.arc(cx, yc, rxo, ryo, ts, 0)
        c.L((R1, bottom)).L((R0, bottom)).L((R0, yc))
        c.arc(cx, yc, rxi, ryi, 0, PI)
    else:
        te = right[1]
        c.arc(cx, yc, rxo, ryo, ts, te)
        c.arc(cx, yc, rxi, ryi, te, PI)
    c.L((L1, bottom)).close()
    return c


def zigzag(verts, w):
    """Chain of straight strokes through vertices (x, y, flat).
    Each inner vertex ends in a flat of exactly the given width (outer edges
    meet its corners, strokes are trimmed by their neighbour's outer edge).
    The first and last vertex give the outer corner x of the free ends."""
    n = len(verts)

    def opening(k):            # +1: the white wedge at vertex k opens upward
        ref = verts[k - 1][1] if k > 0 else verts[k + 1][1]
        return 1 if ref > verts[k][1] else -1

    S = []
    for k in range(n - 1):
        A, B = verts[k], verts[k + 1]
        dirx = 1 if B[0] > A[0] else -1
        PA = (A[0], A[1]) if k == 0 else (A[0] + dirx * A[2] / 2, A[1])
        PB = (B[0], B[1]) if k == n - 2 else (B[0] - dirx * B[2] / 2, B[1])
        v = (PB[0] - PA[0], PB[1] - PA[1])
        L = math.hypot(*v)
        if k == 0 or k == n - 2:
            d = v
            nl = _unit(-d[1], d[0])
            op = opening(k + 1) if k == 0 else opening(k)
            if nl[1] * op < 0:
                nl = (-nl[0], -nl[1])
            E1 = (PA, d)
            E2 = ((PA[0] + nl[0] * w, PA[1] + nl[1] * w), d)
            eA, eB = E1, E1
        else:
            phi = math.asin(min(1.0, w / L))
            best = None
            for s in (1, -1):
                ca, sa = math.cos(s * phi), math.sin(s * phi)
                d = (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)
                nl = _unit(-d[1], d[0])
                side = 1 if (d[0] * v[1] - d[1] * v[0]) > 0 else -1
                nn = (nl[0] * side, nl[1] * side)
                if nn[1] * opening(k) > 0:
                    best = (d, nn)
            d, nn = best
            E1 = (PA, d)
            E2 = ((PA[0] + nn[0] * w, PA[1] + nn[1] * w), d)
            eA, eB = E1, E2
        hA, hB = ((0, A[1]), (1, 0)), ((0, B[1]), (1, 0))
        quad = [isect(E1[0], E1[1], *hA), isect(E2[0], E2[1], *hA),
                isect(E2[0], E2[1], *hB), isect(E1[0], E1[1], *hB)]
        cl = (((quad[0][0] + quad[1][0]) / 2, A[1]), ((quad[2][0] + quad[3][0]) / 2, B[1]))
        S.append({'quad': quad, 'eA': eA, 'eB': eB, 'cl': cl})
    for k in range(1, n - 1):
        prev, nxt = S[k - 1], S[k]
        kp = ((prev['quad'][0][0] + prev['quad'][1][0]) / 2, verts[k - 1][1])
        kn = ((nxt['quad'][2][0] + nxt['quad'][3][0]) / 2, verts[k + 1][1])
        prev['quad'] = clip_half(prev['quad'], nxt['eA'][0], nxt['eA'][1], kp)
        nxt['quad'] = clip_half(nxt['quad'], prev['eB'][0], prev['eB'][1], kn)
    cs = [poly(s['quad']) for s in S]
    lines = [s['cl'] for s in S]
    return cs, lines


def edges_of(cl, w):
    (x0, y0), (x1, y1) = cl
    d = (x1 - x0, y1 - y0)
    l = math.hypot(*d)
    n = (-d[1] / l * w / 2, d[0] / l * w / 2)
    return [((x0 + n[0], y0 + n[1]), d), ((x0 - n[0], y0 - n[1]), d)]


def near_edge(edges, hint):
    def dist(e):
        p, d = e
        return abs(d[0] * (hint[1] - p[1]) - d[1] * (hint[0] - p[0])) / math.hypot(*d)
    return min(edges, key=dist)


def fillet(LA, LB, hint, r, max_t=None):
    """Round off the sharp inside corner where two edges meet. The hint
    point sits inside the white wedge. Returns a small fill contour."""
    Vi = isect(LA[0], LA[1], LB[0], LB[1])
    dA, dB = _unit(*LA[1]), _unit(*LB[1])
    h = (hint[0] - Vi[0], hint[1] - Vi[1])
    uA = uB = None
    for sA in (1, -1):
        for sB in (1, -1):
            a_ = (sA * dA[0], sA * dA[1])
            b_ = (sB * dB[0], sB * dB[1])
            det = a_[0] * b_[1] - a_[1] * b_[0]
            if abs(det) < 1e-9:
                continue
            ka = (h[0] * b_[1] - h[1] * b_[0]) / det
            kb = (a_[0] * h[1] - a_[1] * h[0]) / det
            if ka > 0 and kb > 0:
                uA, uB = a_, b_
    th = math.acos(max(-1, min(1, uA[0] * uB[0] + uA[1] * uB[1]))) / 2
    if max_t:
        r = min(r, max_t * math.tan(th))
    t = r / math.tan(th)
    bis = _unit(uA[0] + uB[0], uA[1] + uB[1])
    C = (Vi[0] + bis[0] * r / math.sin(th), Vi[1] + bis[1] * r / math.sin(th))
    TA = (Vi[0] + uA[0] * t, Vi[1] + uA[1] * t)
    TB = (Vi[0] + uB[0] * t, Vi[1] + uB[1] * t)
    e = 6.0

    def into_ink(u):
        nrm = (-u[1], u[0])
        if nrm[0] * bis[0] + nrm[1] * bis[1] > 0:
            nrm = (-nrm[0], -nrm[1])
        return nrm
    nA, nB = into_ink(uA), into_ink(uB)
    TAi = (TA[0] + nA[0] * e, TA[1] + nA[1] * e)
    TBi = (TB[0] + nB[0] * e, TB[1] + nB[1] * e)
    Vf = (Vi[0] - bis[0] * e / math.sin(th), Vi[1] - bis[1] * e / math.sin(th))
    c = Contour(TA).L(TAi).L(Vf).L(TBi).L(TB)
    dot_arc(c, C, r, TA, (-bis[0], -bis[1]))
    return c.close()


def zz_fillets(lines, verts, w, r, max_t=None):
    out = []
    for k in range(1, len(verts) - 1):
        vx, vy = verts[k][0], verts[k][1]
        ny = verts[k - 1][1]
        hint = (vx, vy + 0.3 * (ny - vy))
        eA = near_edge(edges_of(lines[k - 1], w), hint)
        eB = near_edge(edges_of(lines[k], w), hint)
        out.append(fillet(eA, eB, hint, r, max_t))
    return out


def crotch_fillet(L, cl, w, choose, offset, r, max_t=None):
    """Fillet between a straight edge L and one edge of stroke cl.
    choose picks (point, edge) from the two candidate intersections."""
    cands = [(isect(L[0], L[1], e[0], e[1]), e) for e in edges_of(cl, w)]
    Vi, e = choose(cands)
    hint = (Vi[0] + offset[0], Vi[1] + offset[1])
    return fillet(L, e, hint, r, max_t)


def cap_bowl(xs, ybot, ytop, rxo, Cs, Ht, r):
    """Round-shouldered bowl that swings straight out of a stem at x=xs,
    with signal dots in the two inner corners. Returns (fill, hole)."""
    cy = (ytop + ybot) / 2
    ryo = (ytop - ybot) / 2
    rxi, ryi = rxo - Cs, ryo - Ht
    r = min(r, 0.3 * ryi)
    disk = Contour((xs - 4, ytop)).L((xs, ytop))
    disk.arc(xs, cy, rxo, ryo, PI / 2, -PI / 2)
    disk.L((xs - 4, ybot)).close()
    tc, bc = (xs, cy + ryi), (xs, cy - ryi)
    C1, se1, sa1, ink1 = dot_plan(tc, (0, -1), (1, 0), r)
    C2, se2, sa2, ink2 = dot_plan(bc, (0, 1), (1, 0), r)
    d1 = sa1 / ell_speed(rxi, ryi, PI / 2)
    d2 = sa2 / ell_speed(rxi, ryi, -PI / 2)
    h = Contour((xs, tc[1] - se1))
    dot_arc(h, C1, r, ept(xs, cy, rxi, ryi, PI / 2 - d1), ink1)
    h.arc(xs, cy, rxi, ryi, PI / 2 - d1, -PI / 2 + d2)
    dot_arc(h, C2, r, (xs, bc[1] + se2), ink2)
    return disk, h.close()


def line_x(line, y):
    (x0, y0), (x1, y1) = line
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def dbowl(x0, xflat, ybot, ytop, rxo, Cs, Ht):
    """D-style bowl: flat bars from x0 to xflat, then a half ellipse."""
    cy = (ytop + ybot) / 2
    ryo = (ytop - ybot) / 2
    b = band(xflat, cy, rxo, ryo, rxo - Cs, ryo - Ht, ('a', PI / 2), ('a', -PI / 2))
    return [b, rect(x0, ytop - Ht, xflat + 2, ytop), rect(x0, ybot, xflat + 2, ybot + Ht)]


def s_shape(top, bot, rx_u, rx_l, T, Cs, share=0.465, t_up=0.5, t_lo=0.5):
    total = top - bot
    sumr = (total + T) / 2
    ryo_u = sumr * share
    ryo_l = sumr - ryo_u
    yu, yl = top - ryo_u, bot + ryo_l
    up = band(0, yu, rx_u, ryo_u, rx_u - Cs, ryo_u - T, ('a', t_up), ('a', 1.5 * PI))
    lo = band(0, yl, rx_l, ryo_l, rx_l - Cs, ryo_l - T, ('a', 0.5 * PI), ('a', -PI + t_lo))
    joint = rect(-6, yu - ryo_u, 6, yu - ryo_u + T)
    return [up, lo, joint]


def dot(cx, cy, r):
    return ellipse(cx, cy, r, r)


def crossed_x(p, W, top, w, gap):
    """x with the orbital cross: the back stroke breaks around the front one."""
    hw = diag_hw(w, (0, top), (W, 0))
    for _ in range(6):
        hw = diag_hw(w, (hw, top), (W - hw, 0))
    front_b, front_t = (hw, 0), (W - hw, top)        # "/" in front
    back_t, back_b = (hw, top), (W - hw, 0)          # "\" behind
    front = diag(front_b, front_t, w)
    if gap <= 0:
        return [front, diag(back_t, back_b, w)]
    pts = diag_pts(back_t, back_b, w)
    d = (front_t[0] - front_b[0], front_t[1] - front_b[1])
    ln = math.hypot(*d)
    n = (-d[1] / ln, d[0] / ln)           # points to the upper-left side
    off = w / 2 + gap
    tl = (back_t[0] - hw * 0.5, top - 1)
    br = (back_b[0] + hw * 0.5, 1)
    p1 = clip_half(pts, (front_b[0] + n[0] * off, front_b[1] + n[1] * off), d, tl)
    p2 = clip_half(pts, (front_b[0] - n[0] * off, front_b[1] - n[1] * off), d, br)
    return [front, poly(p1), poly(p2)]


# =====================================================================
# lowercase
# =====================================================================

@glyph('a', 0x61, ('R', 'S'))
def g_a(p, G):
    c, h, _, _ = bowl_stem(p, 0, XH)
    G.add(c).hole(h)


@glyph('d', 0x64, ('R', 'S'))
def g_d(p, G):
    c, h, _, _ = bowl_stem(p, 0, ASC)
    G.add(c).hole(h)


@glyph('q', 0x71, ('R', 'S'))
def g_q(p, G):
    c, h, _, _ = bowl_stem(p, DESC, XH)
    G.add(c).hole(h)


@glyph('b', 0x62, ('S', 'R'))
def g_b(p, G):
    c, h, _, _ = bowl_stem(p, 0, ASC)
    G.add(c).hole(h).transform(mirror_x)


@glyph('p', 0x70, ('S', 'R'))
def g_p(p, G):
    c, h, _, _ = bowl_stem(p, DESC, XH)
    G.add(c).hole(h).transform(mirror_x)


@glyph('g', 0x67, ('R', 'S'))
def g_g(p, G):
    ycT = -40
    c, h, sL, sR = bowl_stem(p, ycT, XH)
    ryo = ycT - (DESC - OS)
    ryi = ryo - p.Ct
    tail = band(0, ycT, sR, ryo, sL, ryi, ('a', 0.06), ('a', -2.5))
    G.add(c, tail).hole(h)


@glyph('o', 0x6F, ('R', 'R'))
def g_o(p, G):
    G.add(ellipse(0, CY, p.brx, RYO)).hole(ellipse(0, CY, p.brx - p.Cs, RYO - p.Ct))


@glyph('c', 0x63, ('R', 'T'))
def g_c(p, G):
    rxo = p.brx * 0.95
    rxi, ryi = rxo - p.Cs, RYO - p.Ct
    off = min(0.6 * RYO, ryi - 18)
    G.add(band(0, CY, rxo, RYO, rxi, ryi, ('h', CY + off, 0.7), ('h', CY - off, TAU - 0.7)))


@glyph('e', 0x65, ('R', 'R'))
def g_e(p, G):
    rxo = p.brx
    rxi, ryi = rxo - p.Cs, RYO - p.Ct
    ybar = CY + 8
    yb0 = ybar - p.H / 2
    yterm = CY - min(0.55 * RYO, ryi - 20)
    b = band(0, CY, rxo, RYO, rxi, ryi, ('h', yb0, -0.1), ('h', yterm, TAU - 0.8))
    ext = rxi + 0.35 * p.Cs
    G.add(b, rect(-ext, yb0, ext, yb0 + p.H))
    G.transform(rotate_fn(0, CY, 12))     # the tilted orbit


@glyph('n', 0x6E)
def g_n(p, G):
    G.add(arch(p, 0, 2 * p.S + p.ncnt, XH))


@glyph('h', 0x68)
def g_h(p, G):
    G.add(arch(p, 0, 2 * p.S + p.ncnt, ASC))


@glyph('m', 0x6D)
def g_m(p, G):
    cm = p.ncnt * 0.8
    w1 = 2 * p.S + cm
    G.add(arch(p, 0, w1, XH), arch(p, p.S + cm, p.S + cm + w1, XH, left='tangent'))


@glyph('u', 0x75)
def g_u(p, G):
    W = 2 * p.S + p.ncnt
    G.add(arch(p, 0, W, XH))
    G.transform(rotate_fn(W / 2, XH / 2, 180))


@glyph('r', 0x72, ('S', 'D'))
def g_r(p, G):
    W = 2 * p.S + p.ncnt * 0.82
    G.add(arch(p, 0, W, XH, right=('a', 0.62)))


@glyph('i', 0x69)
def g_i(p, G):
    G.add(rect(0, 0, p.S, XH), dot(p.S / 2, 770 - p.rd, p.rd))


@glyph('l', 0x6C)
def g_l(p, G):
    G.add(rect(0, 0, p.S, ASC))


@glyph('j', 0x6A, (-20, 'S'))
def g_j(p, G):
    S = p.S
    rxo = 175 + 0.5 * p.g
    sR = 0
    sL = -S
    cxT = sR - rxo
    ycT = -40
    ryo = ycT - (DESC - OS)
    ryi = ryo - p.Ct
    tail = band(cxT, ycT, rxo, ryo, rxo - S, ryi, ('a', 0.06), ('a', -2.45))
    G.add(rect(sL, ycT, sR, XH), tail, dot(-S / 2, 770 - p.rd, p.rd))


@glyph('f', 0x66, ('D', 'D'))
def g_f(p, G):
    S = p.S
    rxo = 150 + 0.9 * p.g
    ycH = ASC - 150 - 0.8 * p.g
    ryo = ASC + OS - ycH
    hook = band(rxo, ycH, rxo, ryo, rxo - S, ryo - p.Ct, ('a', PI + 0.06), ('a', 0.55))
    G.add(rect(0, 0, S, ycH), hook, rect(-95 - 0.2 * p.g, XH - p.H, S + 150 + 0.4 * p.g, XH))


@glyph('t', 0x74, ('D', 'D'))
def g_t(p, G):
    S = p.S
    G.add(rect(0, 0, S, 680), rect(-110 - 0.2 * p.g, XH - p.H, S + 150 + 0.4 * p.g, XH))


@glyph('k', 0x6B, ('S', 'D'))
def g_k(p, G):
    S, w = p.S, p.wd
    W = S + 370 + 0.5 * p.g
    xm = S / 2
    yj = 150
    hw = diag_hw(w, (W, XH), (xm, yj))
    for _ in range(5):
        hw = diag_hw(w, (W - hw, XH), (xm, yj))
    arm_t, arm_b = (W - hw, XH), (xm, yj)
    arm = diag(arm_t, arm_b, w, 'h', ('v', xm))
    yl = 0.5 * XH
    xl = line_x((arm_t, arm_b), yl)
    hl = diag_hw(w, (xl, yl), (W, 0))
    for _ in range(5):
        hl = diag_hw(w, (xl, yl), (W + 10 - hl, 0))
    leg = diag((xl, yl), (W + 10 - hl, 0), w)
    G.add(rect(0, 0, S, ASC), arm, leg)


@glyph('v', 0x76, ('D', 'D'))
def g_v(p, G):
    W = 480 + 0.7 * p.g
    cs, _ = zigzag([(0, XH, 0), (W / 2, 0, 0.32 * p.S), (W, XH, 0)], p.wd)
    G.add(*cs)


@glyph('w', 0x77, ('D', 'D'))
def g_w(p, G):
    W = 760 + 1.0 * p.g
    f = 0.3 * p.S
    cs, _ = zigzag([(0, XH, 0), (W * 0.25, 0, f), (W * 0.5, XH, f), (W * 0.75, 0, f), (W, XH, 0)], p.wd * 0.96)
    G.add(*cs)


@glyph('y', 0x79, ('D', 'D'))
def g_y(p, G):
    W = 490 + 0.7 * p.g
    w = p.wd
    xJ = W * 0.47
    hw = diag_hw(w, (W, XH), (xJ, 0))
    for _ in range(5):
        hw = diag_hw(w, (W - hw, XH), (xJ, 0))
    rt = (W - hw, XH)
    rb_x = xJ + (DESC - 0) * (rt[0] - xJ) / XH
    right = diag((rb_x, DESC), rt, w)
    hl = diag_hw(w, (0, XH), (xJ, 0))
    for _ in range(5):
        hl = diag_hw(w, (hl, XH), (xJ, 0))
    lt = (hl, XH)
    lb = (xJ + (xJ - hl) * 0.25, -XH * 0.25)
    pts = diag_pts(lt, lb, w)
    d = (rt[0] - rb_x, rt[1] - DESC)
    pts = clip_half(pts, (rb_x, DESC), d, (0, XH))
    G.add(right, poly(pts))


@glyph('x', 0x78, ('D', 'D'))
def g_x(p, G):
    W = 470 + 0.7 * p.g
    G.add(*crossed_x(p, W, XH, p.wd, 0.38 * p.S + 8))


@glyph('x.plain', None, ('D', 'D'))
def g_xplain(p, G):
    W = 470 + 0.7 * p.g
    G.add(*crossed_x(p, W, XH, p.wd, 0))


@glyph('z', 0x7A, ('D', 'D'))
def g_z(p, G):
    G.add(*z_shape(420 + 0.5 * p.g, XH, p.H, p.wd * 1.02))


@glyph('s', 0x73, ('R', 'R'))
def g_s(p, G):
    G.add(*s_shape(XH + OS, -OS, p.brx * 0.8, p.brx * 0.87, p.Ct * 0.9, p.Cs * 0.97))


# =====================================================================
# capitals
# =====================================================================

def Orx(p):
    return 362 + 0.5 * p.g


@glyph('H', 0x48)
def g_H(p, G):
    S = p.SC
    W = 2 * S + 410 + 0.3 * p.g
    G.add(rect(0, 0, S, CAP), rect(W - S, 0, W, CAP), rect(0, 365 - p.HC / 2, W, 365 + p.HC / 2))


@glyph('I', 0x49)
def g_I(p, G):
    G.add(rect(0, 0, p.SC, CAP))


@glyph('L', 0x4C, ('S', 'D'))
def g_L(p, G):
    G.add(rect(0, 0, p.SC, CAP), rect(0, 0, p.SC + 350 + 0.3 * p.g, p.HC))


@glyph('E', 0x45, ('S', 'D'))
def g_E(p, G):
    S, H, g = p.SC, p.HC, p.g
    G.add(rect(0, 0, S, CAP), rect(0, CAP - H, S + 350 + 0.3 * g, CAP),
          rect(0, 360 - H / 2, S + 310 + 0.3 * g, 360 + H / 2), rect(0, 0, S + 370 + 0.3 * g, H))


@glyph('F', 0x46, ('S', 'D'))
def g_F(p, G):
    S, H, g = p.SC, p.HC, p.g
    G.add(rect(0, 0, S, CAP), rect(0, CAP - H, S + 340 + 0.3 * g, CAP),
          rect(0, 340 - H / 2, S + 290 + 0.3 * g, 340 + H / 2))


@glyph('T', 0x54, ('D', 'D'))
def g_T(p, G):
    S, H = p.SC, p.HC
    W = 580 + 0.4 * p.g
    G.add(rect(0, CAP - H, W, CAP), rect(W / 2 - S / 2, 0, W / 2 + S / 2, CAP))


@glyph('O', 0x4F, ('R', 'R'))
def g_O(p, G):
    rx, ry = Orx(p), CAP / 2 + OSC
    G.add(ellipse(0, CAP / 2, rx, ry)).hole(ellipse(0, CAP / 2, rx - p.CsC, ry - p.CtC))


@glyph('O.dot', None, ('R', 'R'))
def g_Odot(p, G):
    g_O(p, G)
    G.add(dot(0, CAP / 2, p.rd * 0.95))


@glyph('Q', 0x51, ('R', 'R'))
def g_Q(p, G):
    rx, ry = Orx(p), CAP / 2 + OSC
    G.add(ellipse(0, CAP / 2, rx, ry)).hole(ellipse(0, CAP / 2, rx - p.CsC, ry - p.CtC))
    G.add(diag((rx * 0.32, 150), (rx * 1.02, -110), p.wdC))


@glyph('C', 0x43, ('R', 'T'))
def g_C(p, G):
    rx, ry = Orx(p) * 0.94, CAP / 2 + OSC
    rxi, ryi = rx - p.CsC, ry - p.CtC
    off = min(0.62 * ry, ryi - 25)
    G.add(band(0, CAP / 2, rx, ry, rxi, ryi, ('h', CAP / 2 + off, 0.7), ('h', CAP / 2 - off, TAU - 0.7)))


@glyph('G', 0x47, ('R', 'S'))
def g_G(p, G):
    rx, ry = Orx(p) * 0.96, CAP / 2 + OSC
    rxi, ryi = rx - p.CsC, ry - p.CtC
    off = min(0.62 * ry, ryi - 25)
    bar_top = CAP / 2 + 30
    b = band(0, CAP / 2, rx, ry, rxi, ryi, ('h', CAP / 2 + off, 0.7), ('h', bar_top, TAU + 0.08))
    G.add(b, rect(40, bar_top - p.HC, rxi + 0.4 * p.CsC, bar_top))


@glyph('D', 0x44, ('S', 'R'))
def g_D(p, G):
    S = p.SC
    xf = S + 90
    G.add(rect(0, 0, S, CAP), *dbowl(0, xf, 0, CAP, 300 + 0.5 * p.g, p.CsC, p.HC))


@glyph('B', 0x42, ('S', 'R'))
def g_B(p, G):
    S, H = p.SC, p.HC
    ym = 395
    xf = S + 70
    G.add(rect(0, 0, S, CAP),
          *dbowl(0, xf, ym - H / 2, CAP, 205 + 0.4 * p.g, p.CsC, H),
          *dbowl(0, xf, 0, ym + H / 2, 240 + 0.45 * p.g, p.CsC, H))


@glyph('P', 0x50, ('S', 'R'))
def g_P(p, G):
    S = p.SC
    G.add(rect(0, 0, S, CAP), *dbowl(0, S + 80, 290, CAP, 250 + 0.45 * p.g, p.CsC, p.HC))


@glyph('R', 0x52, ('S', 'D'))
def g_R(p, G):
    S, H = p.SC, p.HC
    xf = S + 80
    rx = 250 + 0.45 * p.g
    yb = 290
    Wr = xf + rx + 25
    top = (xf + 30, yb + H / 2)
    hl = diag_hw(p.wdC, top, (Wr, 0))
    for _ in range(5):
        hl = diag_hw(p.wdC, top, (Wr - hl, 0))
    G.add(rect(0, 0, S, CAP), *dbowl(0, xf, yb, CAP, rx, p.CsC, H), diag(top, (Wr - hl, 0), p.wdC))


@glyph('S', 0x53, ('R', 'R'))
def g_S(p, G):
    G.add(*s_shape(CAP + OSC, -OSC, Orx(p) * 0.74, Orx(p) * 0.8, p.CtC * 0.92, p.CsC * 0.97, share=0.47))


@glyph('U', 0x55)
def g_U(p, G):
    S = p.SC
    W = 2 * S + 400 + 0.3 * p.g
    yc = 300
    ryo = yc + OSC
    b = band(W / 2, yc, W / 2, ryo, W / 2 - S, ryo - p.CtC, ('a', PI - 0.03), ('a', TAU + 0.03))
    G.add(rect(0, yc, S, CAP), rect(W - S, yc, W, CAP), b)


@glyph('J', 0x4A, ('D', 'S'))
def g_J(p, G):
    S = p.SC
    rxo = 200 + 0.4 * p.g
    sR, sL = 0, -S
    cx = sR - rxo
    yc = 240
    ryo = yc + OSC
    b = band(cx, yc, rxo, ryo, rxo - S, ryo - p.CtC, ('a', 0.04), ('a', -2.5))
    G.add(rect(sL, yc, sR, CAP), b)


@glyph('A', 0x41, ('D', 'D'))
def g_A(p, G):
    W = 660 + 0.6 * p.g
    cs, lines = zigzag([(0, 0, 0), (W / 2, CAP, 0.4 * p.SC), (W, 0, 0)], p.wdC)
    yb = 215
    x0 = line_x(lines[0], yb + p.HC / 2)
    x1 = line_x(lines[1], yb + p.HC / 2)
    G.add(*cs, rect(x0, yb, x1, yb + p.HC))


@glyph('V', 0x56, ('D', 'D'))
def g_V(p, G):
    W = 650 + 0.6 * p.g
    cs, _ = zigzag([(0, CAP, 0), (W / 2, 0, 0.4 * p.SC), (W, CAP, 0)], p.wdC)
    G.add(*cs)


@glyph('W', 0x57, ('D', 'D'))
def g_W(p, G):
    W = 1010 + 0.9 * p.g
    f = 0.35 * p.SC
    cs, _ = zigzag([(0, CAP, 0), (W * 0.25, 0, f), (W * 0.5, CAP, f), (W * 0.75, 0, f), (W, CAP, 0)], p.wdC * 0.95)
    G.add(*cs)


@glyph('M', 0x4D)
def g_M(p, G):
    S = p.SC
    W = 2 * S + 540 + 0.5 * p.g
    cs, _ = zigzag([(0, CAP, 0), (W / 2, 0, 0.4 * S), (W, CAP, 0)], p.wdC * 0.95)
    G.add(rect(0, 0, S, CAP), rect(W - S, 0, W, CAP), *cs)


@glyph('N', 0x4E)
def g_N(p, G):
    S = p.SC
    W = 2 * S + 400 + 0.3 * p.g
    t, b = diag_fit(0, CAP, W, 0, p.wdC, -1, +1)
    G.add(rect(0, 0, S, CAP), rect(W - S, 0, W, CAP), diag(t, b, p.wdC))


@glyph('X', 0x58, ('D', 'D'))
def g_X(p, G):
    W = 620 + 0.6 * p.g
    t1, b1 = diag_fit(0, CAP, W, 0, p.wdC, -1, +1)
    t2, b2 = diag_fit(W, CAP, 0, 0, p.wdC, +1, -1)
    G.add(diag(t1, b1, p.wdC), diag(t2, b2, p.wdC))


@glyph('Y', 0x59, ('D', 'D'))
def g_Y(p, G):
    S = p.SC
    W = 640 + 0.6 * p.g
    yj = 300
    cs, _ = zigzag([(0, CAP, 0), (W / 2, yj, S), (W, CAP, 0)], p.wdC)
    G.add(*cs, rect(W / 2 - S / 2, 0, W / 2 + S / 2, yj + 2))



def z_shape(W, top, H, w):
    """Z: two equal bars; the diagonal's outer edges run exactly into the
    inner corners of the bars (W, top-H) and (0, H), clipped to the bar ends."""
    t, b = diag_fit(W, top - H, 0, H, w, +1, -1)
    d = (t[0] - b[0], t[1] - b[1])
    k = 30 / d[1]
    t2 = (t[0] + d[0] * k, t[1] + 30)
    b2 = (b[0] - d[0] * k, b[1] - 30)
    pts = diag_pts(t2, b2, w)
    pts = clip_half(pts, (W, 0), (0, 1), (0, top / 2))
    pts = clip_half(pts, (0, 0), (0, 1), (W, top / 2))
    pts = clip_half(pts, (0, top), (1, 0), (W / 2, top / 2))
    pts = clip_half(pts, (0, 0), (1, 0), (W / 2, top / 2))
    return [rect(0, top - H, W, top), rect(0, 0, W, H), poly(pts)]


@glyph('Z', 0x5A, ('D', 'D'))
def g_Z(p, G):
    G.add(*z_shape(560 + 0.5 * p.g, CAP, p.HC, p.wdC * 1.02))


@glyph('K', 0x4B, ('S', 'D'))
def g_K(p, G):
    S, w = p.SC, p.wdC
    W = S + 470 + 0.5 * p.g
    xm = S / 2
    yj = 200
    hw = diag_hw(w, (W, CAP), (xm, yj))
    for _ in range(5):
        hw = diag_hw(w, (W - hw, CAP), (xm, yj))
    arm_t, arm_b = (W - hw, CAP), (xm, yj)
    arm = diag(arm_t, arm_b, w, 'h', ('v', xm))
    yl = 0.52 * CAP
    xl = line_x((arm_t, arm_b), yl)
    hl = diag_hw(w, (xl, yl), (W, 0))
    for _ in range(5):
        hl = diag_hw(w, (xl, yl), (W + 15 - hl, 0))
    G.add(rect(0, 0, S, CAP), arm, diag((xl, yl), (W + 15 - hl, 0), w))


# =====================================================================
# figures (tabular)
# =====================================================================

def fig_glyph(name, uni):
    def deco(f):
        def wrapped(p, G):
            f(p, G)
            G.fixed = p.fig
        REG.append((name, uni, ('Z', 'Z'), wrapped))
        return f
    return deco



def bar_diag(top_pt, top_side, bot_pt, bot_side, w, clips):
    """A straight stroke whose outer edges pass exactly through two given
    bar corners; extended past them and clipped flush by the given lines.
    clips: list of (point, dir, keep_point)."""
    t, b = diag_fit(top_pt[0], top_pt[1], bot_pt[0], bot_pt[1], w, top_side, bot_side)
    d = (t[0] - b[0], t[1] - b[1])
    k = 40 / d[1]
    pts = diag_pts((t[0] + d[0] * k, t[1] + 40), (b[0] - d[0] * k, b[1] - 40), w)
    for p0, dd, keep in clips:
        pts = clip_half(pts, p0, dd, keep)
    return poly(pts)


@fig_glyph('zero', 0x30)
def f0(p, G):
    # default zero carries the planet dot
    f0plain(p, G)
    G.add(dot(0, CAP / 2, min(p.rd * 0.95, 0.55 * (p.R * 0.93 - p.Cs))))


@fig_glyph('zero.plain', None)
def f0plain(p, G):
    rx, ry = p.R * 0.93, CAP / 2 + 10
    G.add(ellipse(0, CAP / 2, rx, ry)).hole(ellipse(0, CAP / 2, rx - p.Cs, ry - p.Ct))


@fig_glyph('one', 0x31)
def f1(p, G):
    S = p.S
    sL = -S / 2 + 40
    sR = sL + S
    w = S * 0.95
    top = (sR, CAP)
    fb = (sL - 170, CAP - 175)
    hw = diag_hw(w, top, fb)
    for _ in range(5):
        hw = diag_hw(w, (sR - hw, CAP), fb)
    G.add(rect(sL, 0, sR, CAP), diag((sR - hw, CAP), fb, w, 'h', ('perp',)))


@fig_glyph('two', 0x32)
def f2(p, G):
    R, H = p.R, p.H
    rxo, ryo = R * 0.95, 210
    yu = CAP + 10 - ryo
    rxi, ryi = rxo - p.Cs, ryo - p.Ct
    te = -0.62
    G.add(band(0, yu, rxo, ryo, rxi, ryi, ('a', 2.55), ('a', te)))
    tt = te + 0.1
    O = ept(0, yu, rxo, ryo, tt)
    I = ept(0, yu, rxi, ryi, tt)
    mid = ((O[0] + I[0]) / 2, (O[1] + I[1]) / 2)
    w = p.Cs * 0.95
    xL, xR = -rxo, rxo
    # diagonal: lower-left edge runs exactly into the base bar's top-left corner
    bx = xL + 60
    for _ in range(8):
        hw = diag_hw(w, mid, (bx, H))
        bx = xL + hw
    d = (mid[0] - bx, mid[1] - H)
    k = 40 / d[1]
    c = diag(mid, (bx - d[0] * k, H - 40), w, ('line', O, (I[0] - O[0], I[1] - O[1])), 'h')
    pts = [c.start] + [s[1] for s in c.segs]
    pts = clip_half(pts, (xL, 0), (0, 1), (0, CAP / 2))
    pts = clip_half(pts, (0, 0), (1, 0), (0, CAP / 2))
    G.add(poly(pts))
    G.add(rect(xL, 0, xR, H))


@fig_glyph('three', 0x33)
def f3(p, G):
    R = p.R
    T = p.Ct
    top, bot = CAP + 10, -10
    sumr = (top - bot + T) / 2
    ru = sumr * 0.46
    rl = sumr - ru
    yu, yl = top - ru, bot + rl
    rxu, rxl = R * 0.84, R * 0.95
    up = band(0, yu, rxu, ru, rxu - p.Cs, ru - T, ('a', 2.6), ('a', -PI / 2))
    lo = band(0, yl, rxl, rl, rxl - p.Cs, rl - T, ('a', PI / 2), ('a', -2.6))
    G.add(up, lo, rect(-0.3 * R, yu - ru, 6, yu - ru + T))


@fig_glyph('four', 0x34)
def f4(p, G):
    S, H, R = p.S, p.H, p.R
    sR = R * 0.62
    sL = sR - S
    xL = -R
    yb = 165
    w = p.wd
    diag_ = bar_diag((sR, CAP), +1, (xL, yb + H), -1, w,
                     [((0, CAP), (1, 0), (0, 0)), ((xL, 0), (0, 1), (0, CAP / 2)),
                      ((0, yb), (1, 0), (0, CAP / 2))])
    G.add(rect(sL, 0, sR, CAP), rect(xL, yb, sR + 0.6 * S, yb + H), diag_)


@fig_glyph('five', 0x35)
def f5(p, G):
    S, H, R = p.S, p.H, p.R
    rxo, ryo = R * 0.97, 252
    yl = ryo - 10
    rxi, ryi = rxo - p.Cs, ryo - p.Ct
    xr = -0.6 * rxi                 # right edge of the vertical stroke
    xv = xr - S
    yb = yl + ryi * math.sqrt(1 - (xr / rxi) ** 2)
    G.add(band(0, yl, rxo, ryo, rxi, ryi, ('v', xr, 2.0), ('a', -2.55)))
    G.add(rect(xv, yb, xr, CAP), rect(xv, CAP - H, R * 0.88, CAP))


@fig_glyph('six', 0x36)
def f6(p, G):
    six(p, G)


def six(p, G):
    R = p.R
    rxo, ryo = R * 0.97, 258
    yc = ryo - 10
    rxi, ryi = rxo - p.Cs, ryo - p.Ct
    G.add(ellipse(0, yc, rxo, ryo)).hole(ellipse(0, yc, rxi, ryi))
    # a straight stroke leaves the bowl's outer edge on a tangent and rises
    # to a flat top; pick the tangent point so the top lands near centre
    w = p.Cs * 0.97
    target = R * 0.12
    lo, hi = PI / 2 + 0.05, PI - 0.05
    for _ in range(40):
        t0 = (lo + hi) / 2
        P0 = ept(0, yc, rxo, ryo, t0)
        tg = _unit(rxo * math.sin(t0), -ryo * math.cos(t0))   # direction going up
        x_top = P0[0] + tg[0] * (CAP - P0[1]) / tg[1]
        if x_top > target:
            lo = t0
        else:
            hi = t0
    nrm = _unit(-math.cos(t0) * ryo, -math.sin(t0) * rxo)      # inward normal
    nrm = (-nrm[0], -nrm[1]) if nrm[0] < 0 else nrm
    A = P0
    B = (P0[0] + nrm[0] * w, P0[1] + nrm[1] * w)
    At = (A[0] + tg[0] * (CAP - A[1]) / tg[1], CAP)
    Bt = (B[0] + tg[0] * (CAP - B[1]) / tg[1], CAP)
    G.add(poly([A, B, Bt, At]))


@fig_glyph('nine', 0x39)
def f9(p, G):
    six(p, G)
    G.transform(rotate_fn(0, CAP / 2, 180))


@fig_glyph('seven', 0x37)
def f7(p, G):
    R, H = p.R, p.H
    w = p.wd
    xb = -R * 0.3
    hw = diag_hw(w, (R, CAP - H), (xb, 0))
    for _ in range(8):
        hw = diag_hw(w, (R - hw, CAP - H), (xb, 0))
    t = (R - hw, CAP - H)
    d = (t[0] - xb, t[1])
    k = 60 / d[1]
    pts = diag_pts((t[0] + d[0] * k, t[1] + 60), (xb, 0), w)
    pts = clip_half(pts, (R, 0), (0, 1), (0, CAP / 2))
    pts = clip_half(pts, (0, CAP), (1, 0), (0, 0))
    G.add(rect(-R, CAP - H, R, CAP), poly(pts))


@fig_glyph('eight', 0x38)
def f8(p, G):
    R, T = p.R, p.Ct
    top, bot = CAP + 10, -10
    sumr = (top - bot + T) / 2
    ru = sumr * 0.465
    rl = sumr - ru
    yu, yl = top - ru, bot + rl
    rxu, rxl = R * 0.82, R * 0.95
    G.add(ellipse(0, yu, rxu, ru), ellipse(0, yl, rxl, rl))
    G.hole(ellipse(0, yu, rxu - p.Cs, ru - T), ellipse(0, yl, rxl - p.Cs, rl - T))


# =====================================================================
# punctuation and symbols
# =====================================================================

@glyph('space', 0x20)
def g_space(p, G):
    G.empty_adv = round(255 + 0.15 * p.g)


@glyph('nbspace', 0xA0)
def g_nbsp(p, G):
    G.empty_adv = round(255 + 0.15 * p.g)


@glyph('period', 0x2E, ('D', 'D'))
def g_period(p, G):
    G.add(dot(0, p.rd - 4, p.rd))


def comma_shape(p):
    r = p.rd
    cy = r - 4
    tail = poly([(r * 0.99, cy - r * 0.1), (r * 0.02, -132), (-r * 0.58, -118), (-r * 0.93, cy - r * 0.38)])
    return [dot(0, cy, r), tail]


def comet(head, r, tail_end, tail_w):
    """Round head with a straight tapering tail; the tail's edges are true
    tangents to the head, so the two flow together without a corner."""
    u = _unit(tail_end[0] - head[0], tail_end[1] - head[1])
    n = (-u[1], u[0])
    pts = []
    for s in (1, -1):
        E = (tail_end[0] + s * n[0] * tail_w / 2, tail_end[1] + s * n[1] * tail_w / 2)
        b = math.atan2(E[1] - head[1], E[0] - head[0])
        a = b + s * math.acos(r / math.hypot(E[0] - head[0], E[1] - head[1]))
        pts.append((ept(head[0], head[1], r, r, a), E))
    (T1, E1), (T2, E2) = pts
    return [dot(head[0], head[1], r), poly([T1, E1, E2, T2])]


@glyph('comma', 0x2C, ('D', 'D'))
def g_comma(p, G):
    G.add(*comma_shape(p))


@glyph('colon', 0x3A, ('D', 'D'))
def g_colon(p, G):
    G.add(dot(0, p.rd - 4, p.rd), dot(0, XH - p.rd + 4, p.rd))


@glyph('semicolon', 0x3B, ('D', 'D'))
def g_semicolon(p, G):
    G.add(*comma_shape(p), dot(0, XH - p.rd + 4, p.rd))


@glyph('ellipsis', 0x2026, ('D', 'D'))
def g_ellipsis(p, G):
    sp = p.rd * 2 + 70
    G.add(*[dot(i * sp, p.rd - 4, p.rd) for i in range(3)])


@glyph('exclam', 0x21, ('S', 'S'))
def g_exclam(p, G):
    S = p.S
    G.add(rect(-S / 2, 2 * p.rd + 70, S / 2, CAP), dot(0, p.rd - 4, p.rd))


@glyph('question', 0x3F, ('T', 'R'))
def g_question(p, G):
    S = p.S
    rxo, ryo = 195 + 0.5 * p.g, 195
    cy = CAP + 8 - ryo
    rxi, ryi = rxo - p.Cs, ryo - p.Ct
    b = band(0, cy, rxo, ryo, rxi, ryi, ('a', 2.75), ('a', -PI / 2))
    G.add(b, rect(0, 2 * p.rd + 70, S, cy - ryi), dot(S / 2, p.rd - 4, p.rd))


@glyph('quotesingle', 0x27)
def g_qs(p, G):
    G.add(rect(0, 480, p.S * 0.9, CAP + 30))


@glyph('quotedbl', 0x22)
def g_qd(p, G):
    w = p.S * 0.9
    G.add(rect(0, 480, w, CAP + 30), rect(w + 70, 480, 2 * w + 70, CAP + 30))


def qshape(p, dy):
    return [c.map(lambda q: (q[0], q[1] + dy)) for c in comma_shape(p)]


@glyph('quoteright', 0x2019, ('D', 'D'))
def g_qr(p, G):
    G.add(*qshape(p, CAP + 30 - 2 * p.rd))


@glyph('quoteleft', 0x2018, ('D', 'D'))
def g_ql(p, G):
    G.add(*qshape(p, CAP + 30 - 2 * p.rd))
    G.transform(rotate_fn(0, CAP + 30 - p.rd - 60, 180))


@glyph('quotedblright', 0x201D, ('D', 'D'))
def g_qdr(p, G):
    a = qshape(p, CAP + 30 - 2 * p.rd)
    sp = 2 * p.rd + 55
    G.add(*a, *[c.map(lambda q: (q[0] + sp, q[1])) for c in a])


@glyph('quotedblleft', 0x201C, ('D', 'D'))
def g_qdl(p, G):
    g_qdr(p, G)
    G.transform(rotate_fn(0, CAP + 30 - p.rd - 60, 180))


@glyph('grave', 0x60, ('D', 'D'))
def g_grave(p, G):
    # a comet streaking down to the right
    r = p.rd * 0.8
    a = math.radians(-38)
    head = (0, CAP + 30 - r)
    G.add(*comet(head, r, (head[0] + 210 * math.cos(a), head[1] + 210 * math.sin(a)), 0.22 * r))


@glyph('hyphen', 0x2D, ('D', 'D'))
def g_hyphen(p, G):
    G.add(rect(0, CY + 8 - p.H / 2, 290 + 0.3 * p.g, CY + 8 + p.H / 2))


@glyph('endash', 0x2013, ('Z', 'Z'))
def g_endash(p, G):
    G.add(rect(0, CY + 8 - p.H / 2, 500, CY + 8 + p.H / 2))


@glyph('emdash', 0x2014, ('Z', 'Z'))
def g_emdash(p, G):
    G.add(rect(0, CY + 8 - p.H / 2, 1000, CY + 8 + p.H / 2))


@glyph('underscore', 0x5F, ('Z', 'Z'))
def g_us(p, G):
    G.add(rect(0, -170, 520, -170 + p.H))


@glyph('slash', 0x2F, ('D', 'D'))
def g_slash(p, G):
    t, b = diag_fit(340, 770, 0, -150, p.wd * 0.92, +1, -1)
    G.add(diag(t, b, p.wd * 0.92))


@glyph('backslash', 0x5C, ('D', 'D'))
def g_backslash(p, G):
    t, b = diag_fit(0, 770, 340, -150, p.wd * 0.92, -1, +1)
    G.add(diag(t, b, p.wd * 0.92))


@glyph('bar', 0x7C)
def g_bar(p, G):
    G.add(rect(0, -200, p.S * 0.92, 800))


@glyph('parenleft', 0x28, ('R', 'D'))
def g_pl(p, G):
    rxo, ryo = 260 + 0.6 * p.g, 520
    cy = 300
    rxi, ryi = rxo - p.S, ryo - 0.3 * p.S
    G.add(band(0, cy, rxo, ryo, rxi, ryi, ('h', 770, 2.2), ('h', -170, 4.1)))


@glyph('parenright', 0x29, ('D', 'R'))
def g_pr(p, G):
    g_pl(p, G)
    G.transform(mirror_x)


@glyph('bracketleft', 0x5B, ('S', 'D'))
def g_bl(p, G):
    S, H = p.S, p.H
    G.add(rect(0, -170, S, 770), rect(0, 770 - H, S + 150, 770), rect(0, -170, S + 150, -170 + H))


@glyph('bracketright', 0x5D, ('D', 'S'))
def g_br(p, G):
    g_bl(p, G)
    G.transform(mirror_x)


AXIS = 330


@glyph('plus', 0x2B, ('D', 'D'))
def g_plus(p, G):
    W = 460 + 0.2 * p.g
    G.add(rect(0, AXIS - p.H / 2, W, AXIS + p.H / 2), rect(W / 2 - p.S / 2, AXIS - W / 2, W / 2 + p.S / 2, AXIS + W / 2))


@glyph('equal', 0x3D, ('D', 'D'))
def g_equal(p, G):
    W = 460 + 0.2 * p.g
    o = p.H / 2 + 50
    G.add(rect(0, AXIS + o - p.H / 2, W, AXIS + o + p.H / 2), rect(0, AXIS - o - p.H / 2, W, AXIS - o + p.H / 2))


@glyph('asciitilde', 0x7E, ('D', 'D'))
def g_tilde(p, G):
    # one period of a signal wave: two equal orbits meeting on a shared
    # tangent at the centre, ends cut square to the stroke
    Wc = 410 + 0.8 * p.g           # centreline end to end
    A = 48 + 0.15 * p.g            # centreline amplitude
    t = p.Ct
    phi = 2 * math.atan(A / (Wc / 4))
    rho = (Wc / 4) / math.sin(phi)
    s, c = math.sin(phi), math.cos(phi)
    ro, ri = rho + t / 2, rho - t / 2
    e = 0.03
    G.add(band(-rho * s, AXIS - rho * c, ro, ro, ri, ri, ('a', PI / 2 + phi), ('a', PI / 2 - phi - e)),
          band(rho * s, AXIS + rho * c, ro, ro, ri, ri, ('a', 1.5 * PI - phi - e), ('a', 1.5 * PI + phi)))
    center_on_axis(G)


def chevron(p, h, depth):
    cs, _ = zigzag([(0, 0, 0), (h, depth, 0.45 * p.S), (2 * h, 0, 0)], p.wd * 0.95)
    return cs


def center_on_axis(G):
    _, y0, _, y1 = G.bounds()
    dy = AXIS - (y0 + y1) / 2
    G.transform(lambda q: (q[0], q[1] + dy))


@glyph('less', 0x3C, ('D', 'D'))
def g_less(p, G):
    G.add(*chevron(p, 230, 420))
    G.transform(rotate_fn(230, 0, 90))
    center_on_axis(G)


@glyph('greater', 0x3E, ('D', 'D'))
def g_greater(p, G):
    G.add(*chevron(p, 230, 420))
    G.transform(rotate_fn(230, 0, -90))
    center_on_axis(G)


@glyph('multiply', 0xD7, ('D', 'D'))
def g_multiply(p, G):
    s = 380
    y0 = AXIS - s / 2
    t1, b1 = diag_fit(0, y0 + s, s, y0, p.wd * 0.9, -1, +1)
    t2, b2 = diag_fit(s, y0 + s, 0, y0, p.wd * 0.9, +1, -1)
    G.add(diag(t1, b1, p.wd * 0.9), diag(t2, b2, p.wd * 0.9))


@glyph('asterisk', 0x2A, ('D', 'D'))
def g_asterisk(p, G):
    cx, cy = 0, 560
    Ro, Ri = 200, 44 + 0.35 * p.g
    pts = []
    for k in range(8):
        a = PI / 2 + k * PI / 4
        r = Ro if k % 2 == 0 else Ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    G.add(poly(pts))


@glyph('numbersign', 0x23, ('D', 'D'))
def g_hash(p, G):
    w = p.wd * 0.9
    H = p.H * 0.92
    W = 560 + 0.2 * p.g
    G.add(diag((W * 0.38, CAP), (W * 0.25, 0), w), diag((W * 0.75, CAP), (W * 0.62, 0), w),
          rect(0, 450, W, 450 + H), rect(0, 220, W, 220 + H))


@glyph('percent', 0x25, ('D', 'D'))
def g_percent(p, G):
    ro = 125 + 0.3 * p.g
    th = p.S * 0.85
    W = 640 + 0.4 * p.g
    G.add(ellipse(ro, CAP - ro, ro, ro), ellipse(W - ro, ro, ro, ro))
    G.hole(ellipse(ro, CAP - ro, ro - th, ro - th), ellipse(W - ro, ro, ro - th, ro - th))
    t, b = diag_fit(W - 40, CAP, 40, 0, p.wd * 0.85, +1, -1)
    G.add(diag(t, b, p.wd * 0.85))


@glyph('degree', 0xB0, ('D', 'D'))
def g_degree(p, G):
    ro = 120 + 0.2 * p.g
    th = p.S * 0.8
    G.add(ellipse(0, CAP - ro, ro, ro)).hole(ellipse(0, CAP - ro, ro - th, ro - th))


@glyph('bullet', 0x2022, ('D', 'D'))
def g_bullet(p, G):
    G.add(dot(0, AXIS, p.rd * 1.7))


@glyph('periodcentered', 0xB7, ('D', 'D'))
def g_pc(p, G):
    G.add(dot(0, AXIS, p.rd))


def arrow_up(p):
    S = p.S
    head = 250 + 0.9 * p.g
    cs, _ = zigzag([(-head, CAP - head, 0), (0, CAP, 0.55 * S), (head, CAP - head, 0)], p.wd * 0.95)
    return [rect(-S / 2, 0, S / 2, CAP - 25)] + cs


@glyph('arrowup', 0x2191, ('D', 'D'))
def g_au(p, G):
    G.add(*arrow_up(p))


@glyph('arrowdown', 0x2193, ('D', 'D'))
def g_ad(p, G):
    G.add(*arrow_up(p))
    G.transform(rotate_fn(0, CAP / 2, 180))


@glyph('arrowright', 0x2192, ('D', 'D'))
def g_ar(p, G):
    G.add(*arrow_up(p))
    G.transform(rotate_fn(0, CAP / 2, -90))
    G.transform(lambda q: (q[0], q[1] - CAP / 2 + AXIS))


@glyph('arrowleft', 0x2190, ('D', 'D'))
def g_al(p, G):
    G.add(*arrow_up(p))
    G.transform(rotate_fn(0, CAP / 2, 90))
    G.transform(lambda q: (q[0], q[1] - CAP / 2 + AXIS))


@glyph('asciicircum', 0x5E, ('D', 'D'))
def g_circum(p, G):
    # lift-off: the arrowhead of the up arrow, steeper and without its shaft
    hw, dep = 210 + 0.5 * p.g, 290
    cs, _ = zigzag([(-hw, CAP - dep, 0), (0, CAP, 0.55 * p.S), (hw, CAP - dep, 0)], p.wd * 0.95)
    G.add(*cs)


@glyph('at', 0x40, ('R', 'R'))
def g_at(p, G):
    S = p.S * 0.86
    Rc = 385 + 0.7 * p.g          # outer ring centreline radius
    cy = 280
    th = S
    # inner bowl + stem (small a)
    rxo = 170 + 0.55 * p.g
    ryo = 180 + 0.3 * p.g
    icx, icy = -40, cy
    rxi, ryi = rxo - S, ryo - S * 0.95
    sL = icx + rxi - 0.2 * S
    sR = sL + S
    G.add(ellipse(icx, icy, rxo, ryo)).hole(ellipse(icx, icy, rxi, ryi))
    foot_y = icy - ryo + 30
    G.add(rect(sL, foot_y, sR, icy + ryo - 10))
    # foot curving right into the outer ring
    xs = (sL + sR) / 2
    # solve foot radius so its right end lies on the outer ring centreline
    rf = 60.0
    for _ in range(40):
        ex, ey = xs + 2 * rf, foot_y
        dist = math.hypot(ex, ey - cy)
        rf += (Rc - dist) * 0.5
    fcx = xs + rf
    foot = band(fcx, foot_y, rf + th / 2, rf * 0.8 + th / 2, rf - th / 2, rf * 0.8 - th / 2,
                ('a', PI), ('a', TAU + 0.12))
    phi = math.atan2(foot_y - cy, fcx + rf - 0)
    outer = band(0, cy, Rc + th / 2, Rc + th / 2, Rc - th / 2, Rc - th / 2,
                 ('a', phi - 0.1), ('a', phi + TAU - 1.05))
    G.add(foot, outer)


@glyph('.notdef', None, ('S', 'S'))
def g_notdef(p, G):
    G.add(rect(0, 0, 440, CAP)).hole(rect(p.S * 0.7, p.S * 0.7, 440 - p.S * 0.7, CAP - p.S * 0.7))


def build_glyphs(S):
    p = P(S)
    out = []
    for name, uni, sb, f in REG:
        G = Glyph(name, [uni] if uni else [], sb)
        f(p, G)
        G.finalize(p.sb)
        out.append(G)
    order = ['.notdef'] + [g.name for g in out if g.name != '.notdef']
    gd = {g.name: g for g in out}
    return [gd[n] for n in order], p
