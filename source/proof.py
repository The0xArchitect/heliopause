"""Render proof sheets with FreeType (via Pillow)."""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

HERE = os.path.dirname(__file__)
FONTS = os.path.join(HERE, '..', 'ttf')
OUT = os.path.join(HERE, '..', 'proofs')
BG, FG, MUTED = (6, 7, 14), (233, 236, 245), (120, 126, 150)


def glyph_grid(style, size=110, cols=12):
    path = os.path.join(FONTS, f'Heliopause-{style}.ttf')
    tt = TTFont(path)
    cmap = tt.getBestCmap()
    chars = [chr(u) for u in sorted(cmap) if u not in (0x20, 0xA0)]
    font = ImageFont.truetype(path, size)
    label = ImageFont.truetype(path, 16)
    cw, ch = int(size * 1.15), int(size * 1.55)
    rows = (len(chars) + cols - 1) // cols
    img = Image.new('RGB', (cols * cw + 40, rows * ch + 40), BG)
    d = ImageDraw.Draw(img)
    for i, c in enumerate(chars):
        x = 20 + (i % cols) * cw
        y = 20 + (i // cols) * ch
        base = y + int(size * 1.05)
        d.line([(x, base), (x + cw - 10, base)], fill=(40, 44, 64))
        d.text((x + 8, base), c, font=font, fill=FG, anchor='ls')
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, f'grid-{style}.png'))


def text_sheet(lines, name, sizes=(96, 48, 24, 16)):
    styles = ['Regular', 'SemiBold', 'Bold']
    W = 1800
    blocks = []
    for st in styles:
        path = os.path.join(FONTS, f'Heliopause-{st}.ttf')
        for s, line in zip(sizes, lines):
            blocks.append((path, s, line))
    H = sum(int(s * 1.45) for _, s, _ in blocks) + 60
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 30
    for path, s, line in blocks:
        f = ImageFont.truetype(path, s)
        d.text((30, y), line, font=f, fill=FG)
        y += int(s * 1.45)
    img.save(os.path.join(OUT, f'{name}.png'))


if __name__ == '__main__':
    for st in ['Regular', 'SemiBold', 'Bold']:
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
    print('ok')
