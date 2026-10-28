"""Geometry kernel for Heliopause.

Everything is drawn in font units (UPM 1000, y up). A glyph is a set of
closed contours: 'fills' (ink) and 'holes' (counters). Overlapping fills
are allowed and render as a union under the nonzero rule; holes are
oriented opposite to fills and only ever sit inside their own shape.
"""
import math

PI = math.pi
TAU = 2 * math.pi


def _same(a, b, eps=1e-6):
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


class Contour:
    def __init__(self, start):
        self.start = (float(start[0]), float(start[1]))
        self.segs = []  # ('L', p) | ('C', c1, c2, p)

    # ---- building -------------------------------------------------
    def cur(self):
        return self.segs[-1][-1] if self.segs else self.start

    def L(self, p):
        p = (float(p[0]), float(p[1]))
        if not _same(p, self.cur()):
            self.segs.append(('L', p))
        return self

    def C(self, c1, c2, p):
        self.segs.append(('C', tuple(map(float, c1)), tuple(map(float, c2)), tuple(map(float, p))))
        return self

    def arc(self, cx, cy, rx, ry, t0, t1):
        """Elliptical arc from param angle t0 to t1 (draws a line to the arc start first)."""
        self.L((cx + rx * math.cos(t0), cy + ry * math.sin(t0)))
        span = t1 - t0
        if abs(span) < 1e-9:
            return self
        n = max(1, math.ceil(abs(span) / (PI / 2) - 1e-6))
        d = span / n
        k = 4.0 / 3.0 * math.tan(d / 4)
        for i in range(n):
            a = t0 + i * d
            b = a + d
            pa = (cx + rx * math.cos(a), cy + ry * math.sin(a))
            pb = (cx + rx * math.cos(b), cy + ry * math.sin(b))
            c1 = (pa[0] - k * rx * math.sin(a), pa[1] + k * ry * math.cos(a))
            c2 = (pb[0] + k * rx * math.sin(b), pb[1] - k * ry * math.cos(b))
            self.C(c1, c2, pb)
        return self

    def close(self):
        if not _same(self.cur(), self.start):
            self.L(self.start)
        return self

    # ---- transforms -----------------------------------------------
    def map(self, f):
        c = Contour(f(self.start))
        for s in self.segs:
            if s[0] == 'L':
                c.segs.append(('L', f(s[1])))
            else:
                c.segs.append(('C', f(s[1]), f(s[2]), f(s[3])))
        return c

    def reversed(self):
        pts = [self.start] + [s[-1] for s in self.segs]
        c = Contour(pts[-1])
        for i in range(len(self.segs) - 1, -1, -1):
            s = self.segs[i]
            prev = pts[i]
            if s[0] == 'L':
                c.segs.append(('L', prev))
            else:
                c.segs.append(('C', s[2], s[1], prev))
        return c

    # ---- measuring ------------------------------------------------
    def flatten(self, n=12):
        out = [self.start]
        p = self.start
        for s in self.segs:
            if s[0] == 'L':
                out.append(s[1])
            else:
                c1, c2, p3 = s[1], s[2], s[3]
                for i in range(1, n + 1):
                    t = i / n
                    mt = 1 - t
                    x = mt**3 * p[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t**3 * p3[0]
                    y = mt**3 * p[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t**3 * p3[1]
                    out.append((x, y))
            p = s[-1]
        return out

    def area(self):
        pts = self.flatten()
        a = 0.0
        for i in range(len(pts) - 1):
            a += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
        return a / 2

    def draw(self, pen):
        pen.moveTo(self.start)
        segs = list(self.segs)
        if segs and segs[-1][0] == 'L' and _same(segs[-1][1], self.start):
            segs = segs[:-1]
        for s in segs:
            if s[0] == 'L':
                pen.lineTo(s[1])
            else:
                pen.curveTo(s[1], s[2], s[3])
        pen.closePath()


# ---------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------

def rect(x0, y0, x1, y1):
    return Contour((x0, y0)).L((x1, y0)).L((x1, y1)).L((x0, y1)).close()


def poly(pts):
    c = Contour(pts[0])
    for p in pts[1:]:
        c.L(p)
    return c.close()


def ellipse(cx, cy, rx, ry):
    c = Contour((cx + rx, cy))
    c.arc(cx, cy, rx, ry, 0, TAU)
    return c.close()


def ept(cx, cy, rx, ry, t):
    return (cx + rx * math.cos(t), cy + ry * math.sin(t))


def _nearest(cands, near):
    best = None
    for c in cands:
        k = round((near - c) / TAU)
        v = c + TAU * k
        if best is None or abs(v - near) < abs(best - near):
            best = v
    return best


def solve_h(cy, ry, y, near):
    s = max(-1.0, min(1.0, (y - cy) / ry))
    a = math.asin(s)
    return _nearest([a, PI - a], near)


def solve_v(cx, rx, x, near):
    c = max(-1.0, min(1.0, (x - cx) / rx))
    a = math.acos(c)
    return _nearest([a, -a], near)


def band(cx, cy, rxo, ryo, rxi, ryi, e0, e1):
    """A stroke following an elliptical ring between two end cuts.

    An end is ('a', t) radial cut at param angle t, ('h', y, near) a
    horizontal cut, or ('v', x, near) a vertical cut. The band runs from
    e0 to e1 in the direction of increasing or decreasing angle as given.
    """
    def ang(e, rx, ry):
        if e[0] == 'a':
            return e[1]
        if e[0] == 'h':
            return solve_h(cy, ry, e[1], e[2])
        if e[0] == 'v':
            return solve_v(cx, rx, e[1], e[2])
        raise ValueError(e)

    to0, to1 = ang(e0, rxo, ryo), ang(e1, rxo, ryo)
    ti0, ti1 = ang(e0, rxi, ryi), ang(e1, rxi, ryi)
    c = Contour(ept(cx, cy, rxo, ryo, to0))
    c.arc(cx, cy, rxo, ryo, to0, to1)
    c.arc(cx, cy, rxi, ryi, ti1, ti0)
    return c.close()


def ring(cx, cy, rxo, ryo, rxi, ryi):
    return ellipse(cx, cy, rxo, ryo), ellipse(cx, cy, rxi, ryi)


def ell_speed(rx, ry, t):
    return math.hypot(rx * math.sin(t), ry * math.cos(t))


def slot(c, crotch, e1, e2, depth, rr=0):
    """V-shaped ink trap: the white crotch wedge is cut a little deeper into
    the joint, ending in a point. Current point must be e1; ends at e2."""
    u1 = (e1[0] - crotch[0], e1[1] - crotch[1])
    u2 = (e2[0] - crotch[0], e2[1] - crotch[1])
    l1, l2 = math.hypot(*u1), math.hypot(*u2)
    b = (u1[0] / l1 + u2[0] / l2, u1[1] / l1 + u2[1] / l2)
    lb = math.hypot(*b)
    ink = (-b[0] / lb, -b[1] / lb)
    tip = (crotch[0] + ink[0] * depth, crotch[1] + ink[1] * depth)
    c.L(tip)
    c.L(e2)
    return c


def notch(c, center, exit_pt, r):
    """Round signal-gap bite: from the current point (r away from center)
    go the long way round a circle of radius r to exit_pt."""
    e = c.cur()
    a0 = math.atan2(e[1] - center[1], e[0] - center[0])
    a1 = math.atan2(exit_pt[1] - center[1], exit_pt[0] - center[0])
    d = (a1 - a0) % TAU
    sweep = d if d > PI else d - TAU
    c.arc(center[0], center[1], r, r, a0, a0 + sweep)
    c.L(exit_pt)
    return c


# ---------------------------------------------------------------------
# straight-line helpers
# ---------------------------------------------------------------------

def isect(p, d, q, e):
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-12:
        raise ValueError('parallel lines')
    s = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + s * d[0], p[1] + s * d[1])


def _cutline(cut, endpoint):
    if cut is None or cut == 'h':
        return (endpoint, (1.0, 0.0))
    kind = cut[0]
    if kind == 'h':
        return ((0.0, cut[1]), (1.0, 0.0))
    if kind == 'v':
        return ((cut[1], 0.0), (0.0, 1.0))
    if kind == 'line':
        return (cut[1], cut[2])
    if kind == 'perp':
        return None
    raise ValueError(cut)


def diag(top, bot, w, top_cut='h', bot_cut='h'):
    """Straight stroke of perpendicular width w along top->bot.
    Each end is cut by a horizontal line through its endpoint (default),
    ('h', y), ('v', x), ('line', point, dir) or ('perp',)."""
    d = (bot[0] - top[0], bot[1] - top[1])
    ln = math.hypot(*d)
    n = (-d[1] / ln * w / 2, d[0] / ln * w / 2)
    ea = (top[0] + n[0], top[1] + n[1])
    eb = (top[0] - n[0], top[1] - n[1])

    def end(cut, endpoint):
        cl = _cutline(cut, endpoint)
        if cl is None:
            perp = (-d[1], d[0])
            cl = (endpoint, perp)
        return isect(ea, d, cl[0], cl[1]), isect(eb, d, cl[0], cl[1])

    ta, tb = end(top_cut, top)
    ba, bb = end(bot_cut, bot)
    return poly([ta, tb, bb, ba])


def diag_hw(w, top, bot):
    """Half of the horizontal width of a stroke of width w along top->bot."""
    dx, dy = bot[0] - top[0], bot[1] - top[1]
    s = abs(dy) / math.hypot(dx, dy)
    return (w / 2) / max(s, 1e-6)


def diag_fit(x_top_edge, y_top, x_bot_edge, y_bot, w, top_side, bot_side):
    """Solve a stroke so that a chosen corner lands exactly on an x position.
    top_side/bot_side: +1 means the given x is the right corner, -1 the left."""
    xt, xb = x_top_edge, x_bot_edge
    for _ in range(8):
        hw = diag_hw(w, (xt, y_top), (xb, y_bot))
        xt = x_top_edge - top_side * hw
        xb = x_bot_edge - bot_side * hw
    return (xt, y_top), (xb, y_bot)


def vshape(xl, xr, ywide, ypoint, w, flat):
    """A V (or an inverted V when ypoint is above ywide). Returns (contour, info)."""
    xm = (xl + xr) / 2
    A = (xl, ywide)
    B = (xm - flat / 2, ypoint)
    Bp = (xm + flat / 2, ypoint)
    Cc = (xr, ywide)

    def inward(p, q, sign):
        d = (q[0] - p[0], q[1] - p[1])
        ln = math.hypot(*d)
        n = (-d[1] / ln, d[0] / ln)
        if n[0] * sign < 0:
            n = (-n[0], -n[1])
        return d, n

    dl, nl = inward(A, B, +1)
    dr, nr = inward(Cc, Bp, -1)
    Al = (A[0] + nl[0] * w, A[1] + nl[1] * w)
    Cr = (Cc[0] + nr[0] * w, Cc[1] + nr[1] * w)
    Vi = isect(Al, dl, Cr, dr)
    Ai = isect(Al, dl, (0, ywide), (1, 0))
    Ci = isect(Cr, dr, (0, ywide), (1, 0))
    c = poly([A, B, Bp, Cc, Ci, Vi, Ai])

    def at(y, p, d):
        return isect(p, d, (0, y), (1, 0))[0]

    info = {
        'left_mid': lambda y: (at(y, A, dl) + at(y, Al, dl)) / 2,
        'right_mid': lambda y: (at(y, Cc, dr) + at(y, Cr, dr)) / 2,
        'inner_vertex': Vi,
    }
    return c, info


def clip_half(pts, p0, d, keep_point):
    """Clip a convex polygon (list of points) by the line p0 + s*d, keeping
    the side that contains keep_point."""
    def side(p):
        return d[0] * (p[1] - p0[1]) - d[1] * (p[0] - p0[0])

    sk = side(keep_point)
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        sa, sb = side(a) * sk, side(b) * sk
        if sa >= 0:
            out.append(a)
        if (sa >= 0) != (sb >= 0):
            t = sa / (sa - sb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def diag_pts(top, bot, w):
    """Corner points of a horizontally cut stroke (for clipping)."""
    c = diag(top, bot, w)
    pts = [c.start] + [s[1] for s in c.segs]
    if _same(pts[-1], pts[0]):
        pts = pts[:-1]
    return pts


def rotate_fn(cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)

    def f(p):
        x, y = p[0] - cx, p[1] - cy
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    return f


def mirror_x(p):
    return (-p[0], p[1])


# ---------------------------------------------------------------------
# glyph container
# ---------------------------------------------------------------------

class Glyph:
    def __init__(self, name, unicodes=(), sb=('S', 'S')):
        self.name = name
        self.unicodes = list(unicodes)
        self.fills = []
        self.holes = []
        self.sb = sb          # side bearing kinds or numbers
        self.fixed = None     # fixed advance (centred) e.g. tabular figures
        self.adv = 0
        self.empty_adv = None

    def add(self, *cs):
        self.fills.extend(cs)
        return self

    def hole(self, *cs):
        self.holes.extend(cs)
        return self

    def transform(self, f):
        self.fills = [c.map(f) for c in self.fills]
        self.holes = [c.map(f) for c in self.holes]
        return self

    def contours(self):
        out = []
        for c in self.fills:
            out.append(c if c.area() > 0 else c.reversed())
        for c in self.holes:
            out.append(c if c.area() < 0 else c.reversed())
        return out

    def bounds(self):
        xs, ys = [], []
        for c in self.fills + self.holes:
            for p in c.flatten(24):
                xs.append(p[0]); ys.append(p[1])
        return min(xs), min(ys), max(xs), max(ys)

    def finalize(self, sbmap):
        if not self.fills:
            self.adv = self.empty_adv
            return self
        x0, _, x1, _ = self.bounds()

        def val(k):
            return sbmap[k] if isinstance(k, str) else k

        if self.fixed is not None:
            shift = (self.fixed - (x1 - x0)) / 2 - x0
            self.adv = self.fixed
        else:
            lsb, rsb = val(self.sb[0]), val(self.sb[1])
            shift = lsb - x0
            self.adv = round(x1 - x0 + lsb + rsb)
        self.transform(lambda p: (p[0] + shift, p[1]))
        return self
