"""Sanity checks for the built Heliopause Mono fonts.

    python3 source/check_mono.py
"""
import os
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

sys.path.insert(0, os.path.dirname(__file__))
from mono import CELL
from ligatures import ORDER, lig_name

ROOT = os.path.join(os.path.dirname(__file__), '..')
STYLES = ['Regular', 'SemiBold', 'Bold']
# glyphs allowed to reach past the cell edges
OVERFLOW = {'underscore', 'emdash'}
MIN_SB = -2          # tolerance for everything else, in font units

errors = []


def err(msg):
    errors.append(msg)
    print('FAIL', msg)


for st in STYLES:
    for ext, folder in (('otf', 'otf'), ('ttf', 'ttf'), ('woff2', 'web')):
        path = os.path.join(ROOT, folder, f'HeliopauseMono-{st}.{ext}')
        f = TTFont(path)
        tag = f'{st}.{ext}'
        if f['post'].isFixedPitch != 1:
            err(f'{tag}: post.isFixedPitch is not set')
        if f['OS/2'].panose.bProportion != 9:
            err(f'{tag}: PANOSE proportion is not monospaced')
        if f['OS/2'].xAvgCharWidth != CELL:
            err(f'{tag}: xAvgCharWidth {f["OS/2"].xAvgCharWidth}')
        if 'kern' in f or ('GPOS' in f and any(fr.FeatureTag == 'kern' for fr in f['GPOS'].table.FeatureList.FeatureRecord)):
            err(f'{tag}: has kerning')
        hm = f['hmtx']
        gs = f.getGlyphSet()
        ligs = {lig_name(s) for s in ORDER}
        for name in f.getGlyphOrder():
            adv = hm[name][0]
            if adv != CELL:
                err(f'{tag}: {name} advance {adv}')
            if ext != 'ttf':
                continue
            bp = BoundsPen(gs)
            gs[name].draw(bp)
            if not bp.bounds or name in OVERFLOW:
                continue
            x0, _, x1, _ = bp.bounds
            if name in ligs:
                n = len(next(s for s in ORDER if lig_name(s) == name))
                lo = -(n - 1) * CELL
            else:
                lo = 0
            if x0 < lo + MIN_SB or x1 > CELL - MIN_SB:
                err(f'{tag}: {name} ink {x0:.0f}..{x1:.0f} leaves its cell(s)')
        missing = [lig_name(s) for s in ORDER if lig_name(s) not in f.getGlyphOrder()]
        if missing:
            err(f'{tag}: missing ligatures {missing}')
        if 'GSUB' not in f or not any(fr.FeatureTag == 'calt' for fr in f['GSUB'].table.FeatureList.FeatureRecord):
            err(f'{tag}: no calt feature')
    # same characters as Heliopause
    sans = set(TTFont(os.path.join(ROOT, 'ttf', f'Heliopause-{st}.ttf')).getBestCmap())
    mono = set(TTFont(os.path.join(ROOT, 'ttf', f'HeliopauseMono-{st}.ttf')).getBestCmap())
    if sans != mono:
        err(f'{st}: cmap differs from Heliopause: {sorted(sans ^ mono)}')

print('ok' if not errors else f'{len(errors)} problem(s)')
sys.exit(1 if errors else 0)
