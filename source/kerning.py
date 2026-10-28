"""Class kerning for Heliopause (values scale gently with weight)."""

CLASSES = {
    'UC_ROUND': ['O', 'Q', 'C', 'G'],
    'UC_A': ['A'],
    'UC_TOP': ['T'],
    'UC_V': ['V', 'W'],
    'UC_Y': ['Y'],
    'UC_L': ['L'],
    'UC_F': ['F', 'P'],
    'LC_ROUND': ['a', 'c', 'd', 'e', 'g', 'o', 'q'],
    'LC_DIAG': ['v', 'w', 'y'],
    'LC_ALL': ['a', 'c', 'd', 'e', 'g', 'm', 'n', 'o', 'p', 'q', 'r', 's', 'u', 'v', 'w', 'x', 'y', 'z'],
    'PUNCT_LOW': ['period', 'comma', 'ellipsis'],
}

PAIRS = [
    ('UC_TOP', 'LC_ALL', -70),
    ('UC_TOP', 'UC_A', -50),
    ('UC_A', 'UC_TOP', -50),
    ('UC_TOP', 'PUNCT_LOW', -80),
    ('UC_V', 'LC_ROUND', -45),
    ('UC_V', 'UC_A', -45),
    ('UC_A', 'UC_V', -45),
    ('UC_V', 'PUNCT_LOW', -70),
    ('UC_Y', 'LC_ROUND', -60),
    ('UC_Y', 'UC_A', -50),
    ('UC_A', 'UC_Y', -50),
    ('UC_Y', 'PUNCT_LOW', -80),
    ('UC_L', 'UC_TOP', -70),
    ('UC_L', 'UC_V', -60),
    ('UC_L', 'UC_Y', -70),
    ('UC_F', 'PUNCT_LOW', -80),
    ('UC_F', 'UC_A', -35),
    ('UC_A', 'UC_ROUND', -15),
    ('UC_ROUND', 'UC_A', -15),
    ('LC_DIAG', 'PUNCT_LOW', -45),
    ('r', 'PUNCT_LOW', -50),
    ('f', 'PUNCT_LOW', -30),
]


def kern_fea(glyphs, p):
    names = {g.name for g in glyphs}
    lines = []
    for cname, members in CLASSES.items():
        m = [x for x in members if x in names]
        lines.append(f'@{cname} = [{" ".join(m)}];')
    lines.append('feature kern {')
    for a, b, v in PAIRS:
        left = f'@{a}' if a in CLASSES else a
        right = f'@{b}' if b in CLASSES else b
        val = round(v * (1 - 0.15 * p.t))
        kw = 'enum pos' if (a in CLASSES) != (b in CLASSES) else 'pos'
        lines.append(f'  {kw} {left} {right} {val};')
    lines.append('} kern;')
    return '\n'.join(lines) + '\n'
