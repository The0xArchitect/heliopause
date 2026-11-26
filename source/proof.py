"""Render proof sheets with FreeType (via Pillow).

    python3 source/proof.py          # both families
    python3 source/proof.py mono     # Heliopause Mono only
    python3 source/proof.py sans     # Heliopause only
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

HERE = os.path.dirname(__file__)
FONTS = os.path.join(HERE, '..', 'ttf')
OUT = os.path.join(HERE, '..', 'proofs')
BG, FG, MUTED = (6, 7, 14), (233, 236, 245), (120, 126, 150)
CELLC = (24, 27, 42)
STYLES = ['Regular', 'SemiBold', 'Bold']


def glyph_grid(style, ps='Heliopause', size=110, cols=12, mono=False):
    path = os.path.join(FONTS, f'{ps}-{style}.ttf')
    tt = TTFont(path)
    cmap = tt.getBestCmap()
    chars = [chr(u) for u in sorted(cmap) if u not in (0x20, 0xA0)]
    font = ImageFont.truetype(path, size)
    cw, ch = int(size * 1.15), int(size * 1.55)
    rows = (len(chars) + cols - 1) // cols
    img = Image.new('RGB', (cols * cw + 40, rows * ch + 40), BG)
    d = ImageDraw.Draw(img)
    for i, c in enumerate(chars):
        x = 20 + (i % cols) * cw
        y = 20 + (i // cols) * ch
        base = y + int(size * 1.05)
        if mono:      # the 600-unit cell
            d.rectangle([x + 8, base - int(size * 0.96), x + 8 + int(size * 0.6), base + int(size * 0.24)],
                        outline=CELLC)
        d.line([(x, base), (x + cw - 10, base)], fill=(40, 44, 64))
        d.text((x + 8, base), c, font=font, fill=FG, anchor='ls')
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, f'grid-{ps}-{style}.png'))


def text_sheet(lines, name, ps='Heliopause', sizes=(96, 48, 24, 16), features=None, W=1800):
    blocks = []
    for st in STYLES:
        path = os.path.join(FONTS, f'{ps}-{st}.ttf')
        for s, line in zip(sizes, lines):
            blocks.append((path, s, line))
    H = sum(int(s * 1.45) * (line.count('\n') + 1) for _, s, line in blocks) + 60
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 30
    for path, s, line in blocks:
        f = ImageFont.truetype(path, s, layout_engine=ImageFont.Layout.RAQM)
        for ln in line.split('\n'):
            d.text((30, y), ln, font=f, fill=FG, features=features)
            y += int(s * 1.45)
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, f'{name}.png'))


def code_sheet(style, name, features=None, size=30):
    path = os.path.join(FONTS, f'HeliopauseMono-{style}.ttf')
    f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    lines = CODE.strip('\n').split('\n')
    lh = int(size * 1.5)
    img = Image.new('RGB', (1500, lh * len(lines) + 60), BG)
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        d.text((30, 30 + i * lh), ln, font=f, fill=FG, features=features)
    img.save(os.path.join(OUT, f'{name}.png'))


CODE = r'''
# Heliopause Mono: il1I|! 0OoQ B8 rnm {}[]() ''""`` ,.;:
def burn(fuel: float, x: int = 0x1F) -> bool:
    """Scroll to initiate burn."""
    if fuel >= 0.5 and x != 42 or fuel <= -1:
        return orbit[x] == "lock" && !(a || b)
    while t < 9_000: t += 1  # ~ ^ * % @ $ & #
const v = (dist / dt) => { return v ?? null; };   // 4.06 AU
x |> map(f) <| y;  a::b  i++ j--  <-> <=> === !==  /* c */
ABCDEFGHIJKLMNOPQRSTUVWXYZ  abcdefghijklmnopqrstuvwxyz
0123456789 $€£₹ ← ↑ → ↓ ‘’ “” «» ‹› ¡¿ × ° · • … – —
'''


def sans():
    for st in STYLES:
        glyph_grid(st)
    text_sheet([
        'x kid. explorer',
        'Voyager is still talking. Event Horizon.',
        'x is a variable. kid is a constant. SCROLL TO INITIATE BURN ↑',
        'Past this point the sun is just another star, and the variable stops resolving. 0123456789',
    ], 'text')
    text_sheet([
        '{x} ~ ^ ` & $ € £ ₹',
        'Fuel & oxygen: $4,200 · €3,900 · £3,100 · ₹350,000',
        '¡Ya! ¿Listo? «go» ‹go› { x: ~0, y: x^2 } `orbit` (paren) [bracket]',
        'Rocket & fuel cost $12, €10, £9 or ₹999. { `burn` ~ x^2 } ¡¿ «» ‹› \'quote\' ‘quote’',
    ], 'symbols')


def mono():
    for st in STYLES:
        glyph_grid(st, 'HeliopauseMono', mono=True)
        code_sheet(st, f'code-HeliopauseMono-{st}')
        code_sheet(st, f'code-HeliopauseMono-{st}-noliga', features=['-calt'])
    text_sheet([
        'il1I|! 0O rnm',
        'Voyager is still talking. x = 0x1F;',
        'x is a variable. kid is a constant. SCROLL TO INITIATE BURN ↑',
        'Past this point the sun is just another star -> and the variable stops resolving. 0123456789',
    ], 'text-HeliopauseMono', ps='HeliopauseMono')


if __name__ == '__main__':
    pick = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if pick in ('all', 'sans'):
        sans()
    if pick in ('all', 'mono'):
        mono()
    print('ok')
