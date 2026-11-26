"""Compile Heliopause and Heliopause Mono (Regular / SemiBold / Bold) into
OTF, TTF and WOFF2."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shim'))
sys.path.insert(0, os.path.dirname(__file__))

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.O_S_2f_2 import Panose

from glyphs import build_glyphs, XH, CAP, ASC, DESC
from kerning import kern_fea
from mono import build_mono_glyphs, CELL
from ligatures import LIGATURES, calt_fea

FAMILY = 'Heliopause'
VERSION = '0.9'
ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = {'otf': os.path.join(ROOT, 'otf'),
       'ttf': os.path.join(ROOT, 'ttf'),
       'woff2': os.path.join(ROOT, 'web')}

WEIGHTS = [
    # style, stem, usWeightClass
    ('Regular', 86, 400),
    ('SemiBold', 118, 600),
    ('Bold', 146, 700),
]

FEA_BASE = """
languagesystem DFLT dflt;
languagesystem latn dflt;

feature ss02 {
  featureNames { name "Plain zero"; };
  sub zero by zero.plain;
} ss02;

feature ss03 {
  featureNames { name "Plain x"; };
  sub x by x.plain;
} ss03;
"""

# Heliopause's O carries the planet dot; the mono keeps a plain O so the dot
# only ever means zero in code. ss04 swaps to the other one in each family.
SS04_SANS = """
feature ss04 {
  featureNames { name "Plain O"; };
  sub O by O.plain;
} ss04;
"""

SS04_MONO = """
feature ss04 {
  featureNames { name "Orbit O"; };
  sub O by O.dot;
} ss04;
"""


FAMILIES = {
    'Heliopause': {
        'ps': 'Heliopause',
        'glyphs': build_glyphs,
        'features': lambda glyphs, p: FEA_BASE + SS04_SANS + kern_fea(glyphs, p),
        'description': 'A geometric sans with a cosmic twist, made for xkid.org.',
        'mono': False,
    },
    'Heliopause Mono': {
        'ps': 'HeliopauseMono',
        'glyphs': lambda S: build_mono_glyphs(S, LIGATURES),
        'features': lambda glyphs, p: FEA_BASE + SS04_MONO + calt_fea(glyphs),
        'description': 'The monospaced Heliopause, for code and terminals, made for xkid.org.',
        'mono': True,
    },
}


def names(style, family=FAMILY):
    spec = FAMILIES[family]
    if style in ('Regular', 'Bold'):
        fam, sub = family, style
    else:
        fam, sub = f'{family} {style}', 'Regular'
    ps = f'{spec["ps"]}-{style}'
    n = {
        'copyright': 'Copyright 2026 xKid (https://github.com/The0xArchitect/heliopause)',
        'familyName': fam,
        'styleName': sub,
        'uniqueFontIdentifier': f'{VERSION};XKID;{ps}',
        'fullName': f'{family} {style}',
        'version': f'Version {VERSION}',
        'psName': ps,
        'manufacturer': 'xkid.org',
        'designer': 'xKid',
        'description': spec['description'],
        'vendorURL': 'https://xkid.org',
        'designerURL': 'https://xkid.org',
        'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, '
                              'Version 1.1. This license is available with a FAQ at: '
                              'https://openfontlicense.org',
        'licenseInfoURL': 'https://openfontlicense.org',
    }
    if style not in ('Regular', 'Bold'):
        n['typographicFamily'] = family
        n['typographicSubfamily'] = style
    return n


def build(style, stem, wclass, flavor, family=FAMILY):
    spec = FAMILIES[family]
    glyphs, p = spec['glyphs'](stem)
    order = [g.name for g in glyphs]
    cmap = {}
    for g in glyphs:
        for u in g.unicodes:
            cmap[u] = g.name

    is_ttf = flavor == 'ttf'
    fb = FontBuilder(1000, isTTF=is_ttf)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)

    metrics = {}
    if is_ttf:
        ttglyphs = {}
        for g in glyphs:
            pen = TTGlyphPen(None)
            qpen = Cu2QuPen(pen, max_err=0.6, reverse_direction=True)
            for c in g.contours():
                c.draw(qpen)
            tg = pen.glyph()
            if tg.numberOfContours > 0:
                tg.flags[0] |= 0x40          # OVERLAP_SIMPLE
            ttglyphs[g.name] = tg
        fb.setupGlyf(ttglyphs)
    else:
        charstrings = {}
        for g in glyphs:
            pen = T2CharStringPen(int(g.adv), None)
            for c in g.contours():
                c.draw(pen)
            charstrings[g.name] = pen.getCharString()
        n = names(style, family)
        fb.setupCFF(n['psName'], {'FullName': n['fullName'], 'FamilyName': family,
                                  'Weight': style, 'version': VERSION,
                                  'Notice': n['copyright']}, charstrings, {})
    for g in glyphs:
        bp = BoundsPen(None)
        for c in g.contours():
            c.draw(bp)
        lsb = round(bp.bounds[0]) if bp.bounds else 0
        metrics[g.name] = (int(g.adv), lsb)

    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=960, descent=-240, lineGap=0)
    fb.setupNameTable(names(style, family))
    fsSel = 0x80 | (0x20 if style == 'Bold' else 0x40)
    extra = {}
    if spec['mono']:
        pan = Panose()
        for k in ('bFamilyType', 'bSerifStyle', 'bWeight', 'bProportion', 'bContrast',
                  'bStrokeVariation', 'bArmStyle', 'bLetterForm', 'bMidline', 'bXHeight'):
            setattr(pan, k, 0)
        pan.bFamilyType, pan.bProportion = 2, 9          # Latin text, monospaced
        extra = {'panose': pan, 'xAvgCharWidth': CELL}
    fb.setupOS2(sTypoAscender=960, sTypoDescender=-240, sTypoLineGap=0,
                usWinAscent=1000, usWinDescent=280, sxHeight=XH, sCapHeight=CAP,
                usWeightClass=wclass, fsSelection=fsSel, achVendID='XKID',
                fsType=0, ulCodePageRange1=1, version=4,
                yStrikeoutPosition=round(XH / 2 + 8), yStrikeoutSize=round(p.H), **extra)
    fb.setupPost(underlinePosition=-120, underlineThickness=round(p.H * 0.7),
                 isFixedPitch=1 if spec['mono'] else 0)
    fb.font['head'].macStyle = 1 if style == 'Bold' else 0
    fb.font['head'].fontRevision = float(VERSION)

    addOpenTypeFeaturesFromString(fb.font, spec['features'](glyphs, p))
    return fb.font


def main(families=None):
    for d in OUT.values():
        os.makedirs(d, exist_ok=True)
    for family in families or FAMILIES:
        ps = FAMILIES[family]['ps']
        for style, stem, wclass in WEIGHTS:
            otf = build(style, stem, wclass, 'otf', family)
            otf.save(os.path.join(OUT['otf'], f'{ps}-{style}.otf'))
            ttf = build(style, stem, wclass, 'ttf', family)
            ttf.save(os.path.join(OUT['ttf'], f'{ps}-{style}.ttf'))
            w = TTFont(os.path.join(OUT['ttf'], f'{ps}-{style}.ttf'))
            w.flavor = 'woff2'
            w.save(os.path.join(OUT['woff2'], f'{ps}-{style}.woff2'))
            print('built', family, style)


if __name__ == '__main__':
    # optional: build one family only, e.g. `build.py mono`
    pick = {'mono': ['Heliopause Mono'], 'sans': ['Heliopause']}.get(sys.argv[1] if len(sys.argv) > 1 else '')
    main(pick)
