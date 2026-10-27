# -*- coding: utf-8 -*-
"""
Design toolkit for the Bleach-inspired profile README of github.com/RejwanShafi25.

Look: ink-black ground, bone-white paper, Soul-Reaper orange. Heavy slanted
display type, torn paper strips, halftone, crescent slashes, rising reiatsu
sparks and big kanji. Every glyph is drawn as an outline path (no webfonts
and no system-font dependence), so the banners look identical on desktop,
phone and in dark or light mode. CSS animation only, reduced-motion honoured.

Glyph outlines come from the Noto CJK fonts (SIL OFL). When the font files are
not installed (for example on a CI runner) the Latin subset is read from
tools/glyph-cache.json, which is written whenever the full build runs.
"""
import html
import json
import math
import os
import random
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("NOTO_DIR", "/usr/share/fonts/opentype/noto")
CACHE = os.path.join(HERE, "glyph-cache.json")

# ── palette ────────────────────────────────────────────────────────────────
INK, INK2, INK3 = "#07070a", "#0d0d12", "#16161d"
BONE, WHITE, GREY, GREY2 = "#f4f1ea", "#ffffff", "#8b8680", "#5b5752"
ORANGE, ORANGE_DEEP, ORANGE_HOT, EMBER = "#ff6a00", "#b84400", "#ff9a3d", "#ffb066"

# ── fonts ──────────────────────────────────────────────────────────────────
# key: (file, family name as stored in the font, wants the Mono family?)
FONT_SPEC = {
    "black": ("NotoSansCJK-Black.ttc", "Noto Sans CJK JP Black", False),
    "bold": ("NotoSansCJK-Bold.ttc", "Noto Sans CJK JP", False),
    "med": ("NotoSansCJK-Medium.ttc", "Noto Sans CJK JP Medium", False),
    "mono": ("NotoSansCJK-Regular.ttc", "Noto Sans Mono CJK JP", True),
    "serif": ("NotoSerifCJK-Black.ttc", "Noto Serif CJK JP Black", False),
}
LATIN = [chr(c) for c in range(32, 127)] + list("·—–→×’“”…霊圧")  # + kanji used by the CI-rendered panel

try:
    from fontTools.ttLib import TTCollection
    from fontTools.pens.svgPathPen import SVGPathPen
    HAVE_FT = True
except Exception:  # pragma: no cover
    HAVE_FT = False

_cache_json = None


def _load_cache():
    global _cache_json
    if _cache_json is None:
        try:
            with open(CACHE, encoding="utf-8") as fh:
                _cache_json = json.load(fh)
        except OSError:
            _cache_json = {}
    return _cache_json


def _fmt(v):
    s = ("%.1f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Font:
    def __init__(self, key):
        self.key = key
        self.glyphs = {}  # ch -> (advance, path d in font units, y up)
        self.tt = None
        fname, family, mono = FONT_SPEC[key]
        fp = os.path.join(FONT_DIR, fname)
        if HAVE_FT and os.path.exists(fp):
            col = TTCollection(fp)
            pick = None
            for f in col.fonts:
                n = f["name"].getDebugName(1) or ""
                if "JP" in n and ("Mono" in n) == mono and (n == family or pick is None):
                    pick = f
                    if n == family:
                        break
            self.tt = pick
            self.upm = pick["head"].unitsPerEm
            self.cmap = pick.getBestCmap()
            self.gs = pick.getGlyphSet()
            self.hmtx = pick["hmtx"]
        else:
            c = _load_cache().get(key)
            if not c:
                raise RuntimeError("no font file and no glyph cache for %r" % key)
            self.upm = c["upm"]
            for ch, (adv, d) in c["glyphs"].items():
                self.glyphs[ch] = (adv, d)

    def glyph(self, ch):
        g = self.glyphs.get(ch)
        if g is not None:
            return g
        if self.tt is None:
            g = self.glyphs.get("?") or (self.upm * 0.5, "")
            return g
        name = self.cmap.get(ord(ch))
        if name is None:
            g = (self.upm * 0.5, "")
        else:
            pen = SVGPathPen(self.gs, ntos=_fmt)
            self.gs[name].draw(pen)
            g = (self.hmtx[name][0], pen.getCommands())
        self.glyphs[ch] = g
        return g


_fonts = {}


def font(key):
    if key not in _fonts:
        _fonts[key] = Font(key)
    return _fonts[key]


def dump_cache():
    """Write the Latin subset of every font so CI can render without fonts."""
    out = {}
    for key in FONT_SPEC:
        f = font(key)
        if f.tt is None:
            return
        out[key] = {"upm": f.upm, "glyphs": {ch: list(f.glyph(ch)) for ch in LATIN}}
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))


def measure(text, fkey, size, ls=0.0):
    f = font(fkey)
    s = size / f.upm
    return sum(f.glyph(c)[0] * s for c in text) + ls * max(len(text) - 1, 0)


def wrap(text, fkey, size, maxw, ls=0.0):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if cur and measure(t, fkey, size, ls) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def f1(v):
    return _fmt(v)


# ── scene ──────────────────────────────────────────────────────────────────
CSS = """
    .rise{animation:rise .85s cubic-bezier(.16,1,.3,1) both}
    .slam{animation:slam .55s cubic-bezier(.2,1.3,.3,1) both}
    .cut{animation:cut .6s cubic-bezier(.2,.9,.1,1) both}
    .d1{animation-delay:.04s}.d2{animation-delay:.12s}.d3{animation-delay:.2s}.d4{animation-delay:.3s}
    .d5{animation-delay:.4s}.d6{animation-delay:.5s}.d7{animation-delay:.6s}.d8{animation-delay:.7s}
    .draw{stroke-dasharray:1400;stroke-dashoffset:1400;animation:draw 1.3s cubic-bezier(.65,0,.35,1) .25s forwards}
    .flick{animation:flick 5s steps(1,end) infinite}
    .spark{animation-name:spark;animation-timing-function:ease-out;animation-iteration-count:infinite}
    .scan{animation:scan 21s linear infinite}
    .drift{animation:drift 26s ease-in-out infinite}
    .pulse{animation:pulse 3.6s ease-in-out infinite}
    .amb{pointer-events:none}
    @keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
    @keyframes slam{from{opacity:0;transform:translate(-34px,0) scale(1.06)}to{opacity:1;transform:none}}
    @keyframes cut{from{opacity:0;transform:translateX(-120px)}to{opacity:1;transform:none}}
    @keyframes draw{to{stroke-dashoffset:0}}
    @keyframes flick{0%,92%,96%{opacity:1}94%,98%{opacity:.5}}
    @keyframes spark{0%{opacity:0;transform:translateY(0)}14%{opacity:.8}66%{opacity:.4}100%{opacity:0;transform:translateY(-__RISE__px)}}
    @keyframes scan{0%{transform:translateY(-24px);opacity:0}7%{opacity:.5}93%{opacity:.5}100%{transform:translateY(__H__px);opacity:0}}
    @keyframes drift{0%,100%{transform:translateX(0)}50%{transform:translateX(22px)}}
    @keyframes pulse{0%,100%{opacity:.55}50%{opacity:1}}
    @media (prefers-reduced-motion:reduce){
      .rise,.slam,.cut,.flick,.spark,.scan,.drift,.pulse{animation:none}
      .draw{animation:none;stroke-dashoffset:0}
      .amb{display:none}
    }
"""


class Svg:
    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.defs, self.body = [], []
        self.ids = {}

    def add(self, s):
        self.body.append(s)

    def _gid(self, fkey, ch):
        k = (fkey, ch)
        if k not in self.ids:
            self.ids[k] = "g%d" % len(self.ids)
            self.defs.append('<path id="%s" d="%s"/>' % (self.ids[k], font(fkey).glyph(ch)[1]))
        return self.ids[k]

    def text(self, s, x, y, size, fkey="med", fill=BONE, ls=0.0, anchor="start",
             fit=None, skew=0.0, cls="", extra="", stroke=None, sw=0, opacity=None):
        """Outline-path text. y is the baseline. fit = exact target width."""
        f = font(fkey)
        sc = size / f.upm
        w = measure(s, fkey, size, ls)
        sx = (fit / w) if fit else 1.0
        wout = w * sx
        if anchor == "middle":
            x -= wout / 2
        elif anchor == "end":
            x -= wout
        pen, uses = 0.0, []
        for ch in s:
            adv = f.glyph(ch)[0]
            if ch != " " and f.glyph(ch)[1]:
                uses.append('<use xlink:href="#%s" transform="translate(%s 0) scale(%s -%s)"/>'
                            % (self._gid(fkey, ch), f1(pen), ("%.4f" % sc).rstrip("0"), ("%.4f" % sc).rstrip("0")))
            pen += adv * sc + ls
        tf = "translate(%s %s)" % (f1(x), f1(y))
        if skew:
            tf += " skewX(%s)" % f1(-skew)
        if sx != 1.0:
            tf += " scale(%s 1)" % ("%.4f" % sx)
        st = ""
        if stroke:
            st = ' stroke="%s" stroke-width="%s" stroke-linejoin="round" paint-order="stroke"' % (stroke, sw)
        op = ' opacity="%s"' % opacity if opacity is not None else ""
        g = '<g transform="%s" fill="%s"%s%s %s>%s</g>' % (tf, fill, st, op, extra, "".join(uses))
        if cls:  # CSS animation owns `transform`, so it must sit on a wrapper
            g = '<g class="%s">%s</g>' % (cls, g)
        self.add(g)
        return wout

    def render(self, particles=True, extra_defs=""):
        css = CSS.replace("__RISE__", str(self.h + 40)).replace("__H__", str(self.h + 10))
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">\n'
            '  <defs>%s%s\n  </defs>\n  <style>%s</style>\n  %s\n</svg>\n'
            % (self.w, self.h, self.w, self.h, html.escape(self.label, quote=True),
               extra_defs, "".join(self.defs), css, "\n  ".join(self.body))
        )


def write(path, svg):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)


# ── shared pieces ──────────────────────────────────────────────────────────
STD_DEFS = (
    '<linearGradient id="gd" x1="0" y1="0" x2=".6" y2="1"><stop offset="0" stop-color="#0f0f15"/>'
    '<stop offset="1" stop-color="#050507"/></linearGradient>'
    '<linearGradient id="og" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s"/>'
    '<stop offset="1" stop-color="%s"/></linearGradient>'
    '<linearGradient id="scanf" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/>'
    '<stop offset=".5" stop-color="%s" stop-opacity=".85"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
    '<pattern id="ht" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(20)">'
    '<circle cx="2" cy="2" r="1.5" fill="%s" fill-opacity=".26"/></pattern>'
    % (ORANGE_DEEP, ORANGE, ORANGE, ORANGE_HOT, ORANGE, ORANGE)
)


def sparks(s, n, seed, y0=None):
    r = random.Random(seed)
    y0 = s.h + 10 if y0 is None else y0
    out = []
    for _ in range(n):
        out.append('<circle class="spark" cx="%d" cy="%d" r="%.1f" fill="%s" style="animation-duration:%.1fs;animation-delay:-%.1fs"/>'
                   % (r.randint(10, s.w - 10), y0 + r.randint(-6, 24), r.uniform(1.1, 2.6),
                      r.choice([ORANGE, ORANGE_HOT, ORANGE]), r.uniform(7, 14), r.uniform(0, 12)))
    out.append('<rect class="scan" x="0" y="0" width="%d" height="2" fill="url(#scanf)"/>' % s.w)
    s.add('<g class="amb">%s</g>' % "".join(out))


def base(s, particles=24, seed=7, halftone=True):
    s.add('<rect width="%d" height="%d" fill="url(#gd)"/>' % (s.w, s.h))
    if halftone:
        s.add('<rect width="%d" height="%d" fill="url(#ht)" opacity=".45"/>' % (s.w, s.h))
    if particles:
        sparks(s, particles, seed)


def torn(x1, y1, x2, y2, seed, amp=3.0, step=24):
    r = random.Random(seed)
    top, bot = [], []
    n = max(int((x2 - x1) / step), 2)
    for i in range(n + 1):
        x = x1 + (x2 - x1) * i / n
        top.append("%.1f,%.1f" % (x, y1 + r.uniform(-amp, amp)))
        bot.append("%.1f,%.1f" % (x, y2 + r.uniform(-amp, amp)))
    return " ".join(top + bot[::-1])


def crescent(cx, cy, r, dx, dy, r2, rot, fill, uid, blur=0, opacity=1.0, scale=1.0):
    """A crescent from two circles; rot in degrees."""
    mid = "m" + uid
    flt = ' filter="url(#b%s)"' % uid if blur else ""
    defs = ""
    if blur:
        defs = '<filter id="b%s" x="-30%%" y="-30%%" width="160%%" height="160%%"><feGaussianBlur stdDeviation="%s"/></filter>' % (uid, blur)
    mask = ('<mask id="%s" maskUnits="userSpaceOnUse" x="-600" y="-600" width="2400" height="1800">'
            '<circle cx="%s" cy="%s" r="%s" fill="#fff"/><circle cx="%s" cy="%s" r="%s" fill="#000"/></mask>'
            % (mid, f1(cx), f1(cy), f1(r), f1(cx + dx), f1(cy + dy), f1(r2)))
    body = ('<g transform="translate(%s %s) rotate(%s) scale(%s) translate(%s %s)" opacity="%s"%s>'
            '<rect x="-600" y="-600" width="2400" height="1800" fill="%s" mask="url(#%s)"/></g>'
            % (f1(cx), f1(cy), f1(rot), scale, f1(-cx), f1(-cy), opacity, flt, fill, mid))
    return defs + mask, body


def chip(s, label, x, y, h=34, size=14.5, fkey="bold", pad=18, fill=None, edge=ORANGE, color=BONE, skew=10):
    w = measure(label, fkey, size, 0.6) + pad * 2
    sk = math.tan(math.radians(skew)) * h
    pts = "%s,%s %s,%s %s,%s %s,%s" % (f1(x + sk), f1(y), f1(x + w + sk), f1(y), f1(x + w), f1(y + h), f1(x), f1(y + h))
    s.add('<polygon points="%s" fill="%s" fill-opacity="%s" stroke="%s" stroke-width="1.6" stroke-opacity=".85"/>'
          % (pts, fill or INK3, "1" if not fill else ".92", edge))
    s.text(label, x + pad + sk / 2, y + h / 2 + size * 0.36, size, fkey, color, 0.6)
    return w + sk


# ── assets ─────────────────────────────────────────────────────────────────
def hero(out):
    W, H = 1200, 540
    s = Svg(W, H, "Rejwan Shafi. Computer vision, deep learning and digital portrait artist. "
                  "Seeing the unseen: in scans, in code, in faces. BRAC University CSE graduate, CGPA 3.72 out of 4.00. "
                  "Next chapter: MS in computer science, fall 2027.")
    base(s, 26, 11)
    # ghost kanji + crescent
    s.text("死神", 1180, 470, 360, "serif", BONE, anchor="end", opacity=0.045)
    d1, b1 = crescent(905, 262, 232, 112, -36, 206, -16, ORANGE, "a", blur=22, opacity=.8, scale=1.06)
    d2, b2 = crescent(905, 262, 232, 112, -36, 206, -16, BONE, "b")
    s.add('<g class="rise d3"><g class="pulse">%s</g>%s</g>' % (b1, b2))
    s.add('<g class="cut d1 drift" opacity=".9">'
          '<polygon points="760,-10 872,-10 612,548 500,548" fill="%s" fill-opacity=".10"/>'
          '<polygon points="900,-10 936,-10 676,548 640,548" fill="%s" fill-opacity=".22"/></g>' % (ORANGE, ORANGE))
    # top bar
    s.add('<g class="rise d1"><polygon points="56,30 70,30 66,46 52,46" fill="%s"/></g>' % ORANGE)
    s.text("REJWANSHAFI25", 82, 44, 13, "black", BONE, 5, cls="rise d1")
    s.text("DIGITAL ARTIST // CS GRADUATE", 1144, 44, 11.5, "mono", GREY, 3, anchor="end", cls="rise d1")
    s.add('<line class="draw" x1="56" y1="62" x2="1144" y2="62" stroke="%s" stroke-opacity=".4" stroke-width="2"/>' % BONE)
    # name
    for word, x, y, fit, d in (("REJWAN", 56, 206, 560, "d2"), ("SHAFI", 104, 330, 430, "d3")):
        s.add('<g class="slam %s">' % d)
        s.text(word, x + 9, y + 9, 152, "black", ORANGE, fit=fit, skew=9)
        s.text(word, x, y, 152, "black", BONE, fit=fit, skew=9, stroke=INK, sw=7)
        s.add("</g>")
    # strip
    s.add('<g class="rise d5"><polygon points="%s" fill="%s"/></g>' % (torn(50, 358, 760, 404, 5, 2.6), BONE))
    s.text("COMPUTER VISION / DEEP LEARNING / DIGITAL PORTRAITS", 70, 388, 15.5, "black", INK, 2.2, fit=660, cls="rise d5")
    s.text("Seeing the unseen: in scans, in code, in faces.", 56, 440, 20, "med", "#e8e4dc", skew=10, cls="rise d6")
    # stats
    s.add('<line x1="56" y1="462" x2="1144" y2="462" stroke="%s" stroke-opacity=".2" stroke-width="1.5"/>' % BONE)
    cols = [(56, "EDUCATION", "BRAC UNIVERSITY / CSE"), (328, "CGPA", "3.72 / 4.00"),
            (600, "FOCUS", "CV / DEEP LEARNING"), (872, "NEXT CHAPTER", "MS / FALL 2027")]
    for i, (x, lab, val) in enumerate(cols):
        s.text(lab, x, 488, 10.5, "mono", GREY, 2.8, cls="rise d7")
        s.text(val, x, 512, 14.5, "black", BONE, 1.3, cls="rise d7")
        if i:
            s.add('<polygon points="%d,478 %d,478 %d,516 %d,516" fill="%s" fill-opacity=".6"/>' % (x - 20, x - 14, x - 20, x - 26, ORANGE))
    write(os.path.join(out, "hero.svg"), s.render(extra_defs=STD_DEFS + d1 + d2))


def title(out, fname, num, word, sub, kanji, alt):
    W, H = 1200, 150
    s = Svg(W, H, alt)
    base(s, 8, zlib.crc32(fname.encode()) % 97)
    ww = measure(word, "black", 62, 1)
    s.add('<g class="cut d1"><polygon points="44,28 150,28 134,112 28,112" fill="%s"/></g>' % ORANGE)
    s.text(num, 60, 90, 46, "black", INK, 1, skew=9, cls="rise d2")
    px = 160
    s.add('<g class="cut d2"><polygon points="%s" fill="%s"/></g>' % (torn(px, 28, px + ww + 72, 112, zlib.crc32(fname.encode()) % 50, 2.4, 28), BONE))
    s.text(word, px + 36, 92, 62, "black", INK, 1, skew=9, cls="slam d3")
    s.text(kanji, 1156, 104, 96, "serif", ORANGE, anchor="end", cls="rise d4")
    kw = measure(kanji, "serif", 96)
    x0 = px + ww + 72 + 22
    s.add('<line class="draw" x1="%d" y1="78" x2="%d" y2="78" stroke="%s" stroke-opacity=".45" stroke-width="2"/>' % (x0, 1156 - kw - 22, BONE))
    s.text(sub, 1156 - kw - 22, 68, 12.5, "mono", GREY, 2.6, anchor="end", cls="rise d5")
    write(os.path.join(out, fname), s.render(extra_defs=STD_DEFS))


def panel_frame(s, x, y, w, h, accent=True):
    s.add('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-opacity=".12" stroke-width="1.5"/>'
          % (x, y, w, h, INK2, BONE))
    if accent:
        s.add('<polygon points="%s,%s %s,%s %s,%s %s,%s" fill="%s"/>' % (x, y, x + 12, y, x + 4, y + h, x - 8, y + h, ORANGE))


def profile(out):
    W, H = 1200, 420
    alt = ("Profile. I teach machines to see. Computer science graduate from BRAC University, CGPA 3.72, with a deep learning "
           "and computer vision streak, and a digital portrait painter. Class: computer science graduate. Specialty: computer vision "
           "and deep learning. Zanpakuto: Python and PyTorch. Bankai: RejBoard. Second blade: digital portraits. Next: MS, fall 2027.")
    s = Svg(W, H, alt)
    base(s, 10, 3)
    panel_frame(s, 44, 20, 1112, 380)
    s.text("I TEACH MACHINES TO SEE.", 84, 82, 36, "black", BONE, 1, skew=8, cls="slam d1")
    paras = [
        "Computer Science graduate from BRAC University (CGPA 3.72) with a deep learning and computer vision streak. "
        "I build models that find structure in images, apps that stay out of your way and, when the screen goes dark, digital portraits of people.",
        "Current quest: graduate study in computer vision and medical imaging. Side quest: keep shipping RejBoard.",
    ]
    y = 128
    for i, p in enumerate(paras):
        for ln in wrap(p, "med", 17.5, 600):
            s.text(ln, 84, y, 17.5, "med", "#e6e2da", cls="rise d%d" % (2 + i))
            y += 28
        y += 12
    # accent bar under headline
    s.add('<polygon points="84,98 164,98 160,104 80,104" fill="%s"/>' % ORANGE)
    # status card
    cx, cy, cw, chh = 790, 38, 330, 334
    s.add('<g class="rise d3"><rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="2"/>' % (cx, cy, cw, chh, INK, ORANGE))
    s.add('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s"/></g>' % (cx, cy, cx + cw, cy, cx + cw - 8, cy + 30, cx, cy + 30, ORANGE))
    s.text("SOUL REAPER RECORD", cx + 16, cy + 21, 12, "black", INK, 3.2, cls="rise d3")
    rows = [("CLASS", "COMPUTER SCIENCE GRAD"), ("SPECIALTY", "COMPUTER VISION / DL"), ("ZANPAKUTO", "PYTHON / PYTORCH"),
            ("BANKAI", "REJBOARD"), ("SECOND BLADE", "DIGITAL PORTRAITS"), ("NEXT", "MS / FALL 2027")]
    ry = cy + 62
    for i, (a, b) in enumerate(rows):
        s.text(a, cx + 18, ry, 10, "mono", GREY, 3, cls="rise d%d" % (4 + min(i, 4)))
        s.text(b, cx + 18, ry + 21, 15.5, "black", BONE, 1.1, cls="rise d%d" % (4 + min(i, 4)))
        if i < len(rows) - 1:
            s.add('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-opacity=".12"/>' % (cx + 18, ry + 31, cx + cw - 18, ry + 31, BONE))
        ry += 44
    write(os.path.join(out, "profile-panel.svg"), s.render(extra_defs=STD_DEFS))


def bankai_card(out, fname, num, name, tags, desc, stats, kanji, alt, seed):
    W, H = 1200, 280
    s = Svg(W, H, alt)
    base(s, 10, seed)
    s.add('<rect x="44" y="10" width="1112" height="260" fill="%s" stroke="%s" stroke-opacity=".12" stroke-width="1.5"/>' % (INK2, BONE))
    s.text(kanji, 1140, 262, 250, "serif", ORANGE, anchor="end", opacity=0.10)
    s.add('<polygon points="44,10 60,10 50,270 34,270" fill="%s"/>' % ORANGE)
    s.text("BANKAI", 92, 46, 12, "mono", ORANGE, 4, cls="rise d1")
    s.text(num, 176, 46, 12, "mono", GREY, 4, cls="rise d1")
    nw = measure(name, "black", 54, 1)
    fit = min(nw, 700)
    s.add('<g class="slam d2">')
    s.text(name, 96 + 5, 106 + 5, 54, "black", ORANGE, 1, fit=fit, skew=8)
    s.text(name, 96, 106, 54, "black", BONE, 1, fit=fit, skew=8, stroke=INK2, sw=6)
    s.add("</g>")
    s.text(tags, 92, 140, 12.5, "mono", ORANGE, 2.4, cls="rise d3")
    y = 174
    for ln in wrap(desc, "med", 16.5, 640):
        s.text(ln, 92, y, 16.5, "med", "#dcd8d0", cls="rise d4")
        y += 25
    # stats
    sx = 1110
    for i, (val, lab) in enumerate(stats):
        yy = 74 + i * 66
        s.add('<g class="rise d%d">' % (4 + i))
        s.text(val, sx, yy + 30, 34, "black", BONE, 0.5, anchor="end", skew=6)
        s.text(lab, sx, yy + 50, 10.5, "mono", GREY, 2.6, anchor="end")
        s.add("</g>")
    s.add('<line x1="860" y1="40" x2="860" y2="240" stroke="%s" stroke-opacity=".18" stroke-width="1.5"/>' % BONE)
    write(os.path.join(out, fname), s.render(extra_defs=STD_DEFS))


def archive(out):
    W, H = 1200, 330
    cards = [
        ("I", "BRAIN STROKE", "CSE422 / SCIKIT-LEARN", "Classification on 43,400 records and 12 features, heavily imbalanced. Logistic regression, decision tree, KNN and random forest compared head to head.", ("96.79%", "RANDOM FOREST ACC")),
        ("II", "MOVIE PLATFORM", "CSE370 / PHP / MYSQL", "Stream classics online, book seats for new releases. Reserved seating that updates on admin approval, movie requests and a full admin panel.", ("2 HALLS", "2D + 3D PREMIERES")),
        ("III", "ROBORUMBLE", "CSE423 / PYTHON / OPENGL", "Turn-based 2D artillery duel with destructible terrain, four bullet types, health and energy meters and projectile physics.", ("4 SHELLS", "SIMPLE / EXPLOSIVE / SNIPER / BURST")),
    ]
    s = Svg(W, H, "The archive: Brain Stroke classification with 96.79 percent random forest accuracy, Movie Watching Platform "
                  "in PHP and MySQL, and RoboRumble, a 2D OpenGL artillery game.")
    base(s, 12, 21)
    cw, gap = 352, 28
    for i, (n, name, tag, desc, (val, lab)) in enumerate(cards):
        x = 56 + i * (cw + gap)
        s.add('<g class="rise d%d">' % (i + 1))
        s.add('<rect x="%d" y="14" width="%d" height="300" fill="%s" stroke="%s" stroke-opacity=".12" stroke-width="1.5"/>' % (x, cw, INK2, BONE))
        s.add('<polygon points="%d,14 %d,14 %d,40 %d,40" fill="%s"/>' % (x, x + cw, x + cw - 10, x, ORANGE))
        s.text("ARCHIVE " + n, x + 16, 33, 11.5, "black", INK, 3)
        s.text(name, x + 18, 88, 32, "black", BONE, 0.6, skew=7, fit=min(measure(name, "black", 32, .6), cw - 40))
        s.text(tag, x + 18, 114, 11, "mono", ORANGE, 2)
        yy = 148
        for ln in wrap(desc, "med", 15, cw - 38)[:5]:
            s.text(ln, x + 18, yy, 15, "med", "#dcd8d0")
            yy += 23
        s.add('<line x1="%d" y1="250" x2="%d" y2="250" stroke="%s" stroke-opacity=".18"/>' % (x + 18, x + cw - 18, BONE))
        s.text(val, x + 18, 286, 28, "black", BONE, 0.5, skew=6)
        s.text(lab, x + 18, 304, 9.5, "mono", GREY, 2.2)
        s.add("</g>")
    write(os.path.join(out, "archive-grid.svg"), s.render(extra_defs=STD_DEFS))


def abilities(out):
    groups = [
        ("LANGUAGES", "言", ["Python", "C", "PHP", "JavaScript", "SQL", "HTML / CSS", "LaTeX"]),
        ("VISION + ML", "眼", ["PyTorch", "TensorFlow", "Keras", "scikit-learn", "OpenCV", "YOLOv8", "Hugging Face", "NumPy", "Pandas", "SciPy", "Matplotlib"]),
        ("WEB + APPS", "網", ["Laravel", "Tailwind CSS", "Bootstrap", "MySQL", "Electron", "Vite"]),
        ("TOOLING", "具", ["Git", "GitHub Actions", "Jupyter", "Google Colab", "Anaconda", "VS Code", "PyCharm"]),
        ("THE OTHER BLADE", "絵", ["Digital portraits", "Krita", "Photoshop"]),
    ]
    maxx, x0 = 1144, 330
    layout, y = [], 0
    for lab, k, items in groups:
        rows, cx, row = [], x0, []
        for it in items:
            w = measure(it, "bold", 14.5, 0.6) + 36 + 8
            if cx + w > maxx and row:
                rows.append(row)
                row, cx = [], x0
            row.append(it)
            cx += w + 12
        rows.append(row)
        h = max(len(rows) * 46 + 18, 74)
        layout.append((lab, k, rows, y, h))
        y += h
    H = y + 28
    s = Svg(1200, H, "Abilities. Languages: Python, C, PHP, JavaScript, SQL, HTML and CSS, LaTeX. Vision and ML: PyTorch, TensorFlow, Keras, "
                     "scikit-learn, OpenCV, YOLOv8, Hugging Face, NumPy, Pandas, SciPy, Matplotlib. Web and apps: Laravel, Tailwind CSS, Bootstrap, "
                     "MySQL, Electron, Vite. Tooling: Git, GitHub Actions, Jupyter, Google Colab, Anaconda, VS Code, PyCharm. "
                     "The other blade: digital portraits, Krita, Photoshop.")
    base(s, 8, 5)
    for gi, (lab, k, rows, gy, h) in enumerate(layout):
        gy += 14
        s.add('<g class="rise d%d">' % (gi + 1))
        s.add('<rect x="44" y="%d" width="1112" height="%d" fill="%s" stroke="%s" stroke-opacity=".10" stroke-width="1.5"/>' % (gy, h - 8, INK2, BONE))
        s.add('<polygon points="44,%d 58,%d 52,%d 38,%d" fill="%s"/>' % (gy, gy, gy + h - 8, gy + h - 8, ORANGE))
        s.text(k, 318, gy + h / 2 + 30, 80, "serif", ORANGE, anchor="end", opacity=0.16)
        s.text(lab, 80, gy + h / 2 - 8 + 6, 17, "black", BONE, 1.4, skew=7)
        s.text("%02d" % (gi + 1), 80, gy + h / 2 + 18, 10.5, "mono", GREY, 3)
        cy = gy + 14
        for row in rows:
            cx = x0
            for it in row:
                w = chip(s, it, cx, cy, 34, 14.5, "bold")
                cx += w + 12
            cy += 46
        s.add("</g>")
    write(os.path.join(out, "abilities-grid.svg"), s.render(extra_defs=STD_DEFS))


def art(out):
    W, H = 1200, 330
    s = Svg(W, H, "Brush. The other blade. Beyond the code, Rejwan paints digital portraits of people in Krita and Photoshop. "
                  "Portraits teach the same habit as computer vision: reading structure, light and detail. Find the work on Instagram, Behance and ArtStation.")
    base(s, 12, 17)
    panel_frame(s, 44, 20, 1112, 290)
    s.text("絵", 790, 300, 240, "serif", ORANGE, anchor="end", opacity=0.07)
    s.text("FACES ARE", 84, 92, 40, "black", BONE, 1, skew=8, cls="slam d1")
    s.text("THE HARDEST DATASET.", 84, 140, 40, "black", ORANGE, 1, skew=8, cls="slam d2")
    para = ("Outside the terminal I paint digital portraits of people, in Krita and Photoshop. Getting a likeness means reading structure, "
            "light and tiny details, the same habit I am bringing to computer vision.")
    y = 184
    for ln in wrap(para, "med", 17, 640):
        s.text(ln, 84, y, 17, "med", "#e6e2da", cls="rise d3")
        y += 27
    for i, (lab, h) in enumerate((("INSTAGRAM", "@bd_sketch25"), ("BEHANCE", "bd_sketch25"), ("ARTSTATION", "bdsketch25"))):
        x, yy = 820, 66 + i * 76
        s.add('<g class="cut d%d"><polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" stroke="%s" stroke-width="1.6"/></g>'
              % (3 + i, x + 14, yy, x + 306, yy, x + 292, yy + 58, x, yy + 58, INK, ORANGE))
        s.text(lab, x + 32, yy + 24, 11, "mono", ORANGE, 3.4, cls="rise d%d" % (4 + i))
        s.text(h, x + 32, yy + 46, 18, "black", BONE, 1, cls="rise d%d" % (4 + i))
    write(os.path.join(out, "art-panel.svg"), s.render(extra_defs=STD_DEFS))


def journey(out):
    W, H = 1200, 372
    nodes = [
        ("2021 - 2025", "BRAC UNIVERSITY", "B.Sc. in Computer Science, Dhaka. CGPA 3.72 / 4.00. Vice Chancellor's List twice, Dean's List twice.", "学"),
        ("JAN - SEP 2024", "TEACHING ASSISTANT", "Undergraduate TA for Complex Variables and Laplace Transformation, 120+ students per semester.", "師"),
        ("2024 - NOW", "THE FORGE", "Course projects (YOLOv8 signboards, RSWNet, Nilam BD) plus RejBoard, a hobby project built on the side.", "鍛"),
        ("NEXT CHAPTER", "MS IN COMPUTER SCIENCE", "Applying for fall 2027. Focus: computer vision and medical imaging.", "道"),
    ]
    s = Svg(W, H, "Journey. 2021 to 2025: B.Sc. in Computer Science at BRAC University, CGPA 3.72, Vice Chancellor's List twice and Dean's List twice. "
                  "January to September 2024: undergraduate teaching assistant for Complex Variables and Laplace Transformation, 120 plus students per semester. "
                  "2024 to now: course projects (YOLOv8 signboards, RSWNet, Nilam BD) and RejBoard, a hobby project. Next chapter: MS in computer science, fall 2027, computer vision and medical imaging.")
    base(s, 12, 9)
    s.add('<line class="draw" x1="56" y1="70" x2="1144" y2="70" stroke="%s" stroke-width="3"/>' % ORANGE)
    cw, gap = 258, 26
    for i, (when, what, desc, k) in enumerate(nodes):
        x = 56 + i * (cw + gap)
        last = i == len(nodes) - 1
        s.add('<g class="rise d%d">' % (i + 1))
        s.add('<polygon points="%d,56 %d,56 %d,84 %d,84" fill="%s"/>' % (x + 8, x + 40, x + 32, x, ORANGE if not last else BONE))
        s.add('<rect x="%d" y="104" width="%d" height="244" fill="%s" stroke="%s" stroke-opacity="%s" stroke-width="%s"/>'
              % (x, cw, INK2, ORANGE if last else BONE, "1" if last else ".12", 2 if last else 1.5))
        s.text(k, x + cw - 10, 338, 130, "serif", ORANGE, anchor="end", opacity=0.13)
        s.text(when, x + 18, 138, 11.5, "mono", ORANGE, 2.4)
        yy = 172
        for ln in wrap(what, "black", 19, cw - 36, 0.6):
            s.text(ln, x + 18, yy, 19, "black", BONE, 0.6, skew=6)
            yy += 25
        yy += 12
        for ln in wrap(desc, "med", 14.5, cw - 36):
            s.text(ln, x + 18, yy, 14.5, "med", "#d6d2ca")
            yy += 22
        s.add("</g>")
    write(os.path.join(out, "journey-timeline.svg"), s.render(extra_defs=STD_DEFS))


def contact(out):
    W, H = 1200, 206
    s = Svg(W, H, "Send a hell butterfly. Deep learning, computer vision, medical imaging, web, or just art: if you are building something "
                  "interesting, the inbox is open.")
    base(s, 12, 4)
    panel_frame(s, 44, 16, 1112, 174)
    s.text("蝶", 1130, 196, 220, "serif", ORANGE, anchor="end", opacity=0.10)
    s.text("SEND A HELL BUTTERFLY.", 84, 84, 40, "black", BONE, 1, skew=8, cls="slam d1")
    para = ("Deep learning, computer vision, medical imaging, web, or just art. If you are building something interesting, "
            "or want to talk faces and pixels, the inbox is open.")
    y = 128
    for ln in wrap(para, "med", 17.5, 700):
        s.text(ln, 84, y, 17.5, "med", "#e6e2da", cls="rise d2")
        y += 28
    write(os.path.join(out, "contact-panel.svg"), s.render(extra_defs=STD_DEFS))


def button(out, fname, label, handle):
    w = int(max(measure(label, "black", 17, 2.4), measure(handle, "mono", 12, 1.2)) + 76)
    H = 58
    s = Svg(w, H, "%s, %s." % (label.title(), handle))
    s.add('<polygon points="14,4 %d,4 %d,%d 0,%d" fill="%s"/>' % (w - 2, w - 16, H - 4, H - 4, ORANGE))
    s.add('<polygon points="22,10 %d,10 %d,%d 8,%d" fill="%s"/>' % (w - 8, w - 22, H - 10, H - 10, INK))
    s.text(label, 38, 28, 17, "black", BONE, 2.4)
    s.text(handle, 38, 45, 11.5, "mono", ORANGE, 1.2)
    write(os.path.join(out, fname), s.render(extra_defs=""))
    return w


def label(out, fname, text, sub):
    w = int(measure(text, "black", 16, 3) + 60)
    s = Svg(w, 40, "%s: %s." % (text.title(), sub))
    s.add('<polygon points="0,6 10,6 4,34 -6,34" fill="%s"/>' % ORANGE)
    s.text(text, 20, 26, 16, "black", BONE, 3)
    write(os.path.join(out, fname), s.render())
    return w


def footer(out):
    W, H = 1200, 296
    s = Svg(W, H, "See the unseen. Rejwan Shafi, RejwanShafi25. Admiration is the state furthest from understanding. Sosuke Aizen.")
    base(s, 22, 31)
    d1, b1 = crescent(150, 130, 150, 62, -22, 132, -16, ORANGE, "c", blur=18, opacity=.35)
    d2, b2 = crescent(150, 130, 150, 62, -22, 132, -16, BONE, "d", opacity=.16)
    d3, b3 = crescent(1050, 130, 150, -62, -22, 132, 16, ORANGE, "e", blur=18, opacity=.35)
    d4, b4 = crescent(1050, 130, 150, -62, -22, 132, 16, BONE, "f", opacity=.16)
    s.add(b1 + b2 + b3 + b4)
    s.add('<polygon points="%s" fill="%s"/>' % (torn(380, 60, 820, 120, 14, 2.6), BONE))
    s.text("SEE THE UNSEEN.", 600, 108, 46, "black", INK, 1.2, anchor="middle", skew=8)
    s.text("REJWAN SHAFI  /  REJWANSHAFI25", 600, 160, 14, "black", BONE, 6, anchor="middle")
    s.text("\u201cAdmiration is the state furthest from understanding.\u201d", 600, 214, 20, "med", "#e8e4dc", anchor="middle", skew=10)
    s.text("SOSUKE AIZEN", 600, 244, 11.5, "mono", ORANGE, 5, anchor="middle")
    s.add('<line x1="56" y1="270" x2="1144" y2="270" stroke="%s" stroke-opacity=".2" stroke-width="1.5"/>' % BONE)
    write(os.path.join(out, "footer-signature.svg"), s.render(extra_defs=STD_DEFS + d1 + d2 + d3 + d4))


def rejboard_card(out, version="1.3.3"):
    bankai_card(out, "bankai-rejboard.svg", "I", "REJBOARD",
                "ELECTRON / JAVASCRIPT / PWA / HOBBY PROJECT",
                "A handwriting-first whiteboard and note-taking app. Pressure-sensitive pens, LaTeX, shapes and connectors, PDF annotation "
                "and per-board voice recordings. No account, no cloud, no subscription. Runs on Windows, macOS, Linux and as an installable web app.",
                [("v" + version, "LATEST RELEASE"), ("3 + WEB", "DESKTOP PLATFORMS + PWA"), ("MIT", "OPEN SOURCE")], "板",
                "Bankai I. RejBoard: a local-first whiteboard and handwriting note-taking app with pressure-sensitive pens, LaTeX, PDF annotation and "
                "voice recordings. Electron, JavaScript, installable web app. A hobby project. Version " + version + ", MIT licensed.", 1)


def build_all(out):
    hero(out)
    t = [
        ("title-profile.svg", "01", "PROFILE", "WHO HOLDS THE BLADE", "魂", "01 Profile. Who holds the blade."),
        ("title-bankai.svg", "02", "BANKAI", "WHAT LEFT THE FORGE", "卍解", "02 Bankai. What left the forge."),
        ("title-abilities.svg", "03", "ZANPAKUTO", "THE TOOLS I DRAW", "斬魄刀", "03 Zanpakuto. The tools I draw."),
        ("title-brush.svg", "04", "BRUSH", "THE OTHER BLADE", "絵", "04 Brush. The other blade."),
        ("title-journey.svg", "05", "JOURNEY", "WHERE THE ROAD HAS GONE", "道", "05 Journey. Where the road has gone."),
        ("title-reiatsu.svg", "06", "REIATSU", "A YEAR OF COMMITS", "霊圧", "06 Reiatsu. A year of commits."),
        ("title-contact.svg", "07", "CONTACT", "SAY SOMETHING WORTH ANSWERING", "連絡", "07 Contact. Say something worth answering."),
    ]
    for a in t:
        title(out, *a)
    profile(out)
    rejboard_card(out)
    bankai_card(out, "bankai-rswnet.svg", "II", "RSWNET",
                "PYTORCH / RESNET50 / UNSUPERVISED LEARNING",
                "A deep self-organizing map network for unsupervised feature learning and clustering. A modified ResNet50 encoder and a custom decoder "
                "learn a latent space that clusters Fashion-MNIST far more cleanly than a plain SOM baseline.",
                [("0.88", "SILHOUETTE SCORE"), ("0.29", "SOM BASELINE"), ("0.16", "DAVIES-BOULDIN, LOWER IS BETTER")], "網",
                "Bankai II. RSWNet: a deep self-organizing map network for unsupervised feature learning and clustering with a modified ResNet50 encoder. "
                "Silhouette score 0.8801 against 0.2936 for the SOM baseline on Fashion-MNIST. PyTorch.", 2)
    bankai_card(out, "bankai-nilam.svg", "III", "NILAM BD",
                "LARAVEL / PHP / MYSQL / TAILWIND",
                "A full online auction platform with users, sellers and admins. Live bidding with outbid and ending-soon alerts, auctions that close "
                "themselves on a five minute schedule, cash on delivery with admin approval, and a report and moderation system.",
                [("3", "ROLES"), ("5 MIN", "AUTO-CLOSE CHECK"), ("10.x", "LARAVEL")], "競",
                "Bankai III. Nilam BD: an online auction management system built with Laravel. Three roles, real-time bidding with notifications, "
                "scheduled auction endings, cash on delivery with admin approval, and a report and moderation system.", 3)
    bankai_card(out, "bankai-signboard.svg", "IV", "SIGNBOARD VISION",
                "YOLOV8 / ULTRALYTICS / OBJECT DETECTION",
                "A custom YOLOv8 detector for signboards, trained on about 3,800 annotated street images captured in Bangladesh and split manually into "
                "train, validation and test sets. Also tried on scraped scenes from Bangladesh and India. Built with a team of four for CSE428.",
                [("64.8%", "TEST mAP@50"), ("67.0%", "TEST RECALL"), ("3,800", "TRAINING IMAGES")], "眼",
                "Bankai IV. Signboard Detection with YOLOv8: a custom object detector trained on about 3,800 street images from Bangladesh, "
                "64.8 percent mAP at 50 and 67 percent recall on the test set.", 4)
    archive(out)
    abilities(out)
    art(out)
    journey(out)
    contact(out)
    widths = {
        "btn-email.svg": button(out, "btn-email.svg", "EMAIL", "rejwanshafi.dev@gmail.com"),
        "btn-linkedin.svg": button(out, "btn-linkedin.svg", "LINKEDIN", "in/rejwanshafi"),
        "btn-instagram.svg": button(out, "btn-instagram.svg", "INSTAGRAM", "@bd_sketch25"),
        "btn-behance.svg": button(out, "btn-behance.svg", "BEHANCE", "bd_sketch25"),
        "btn-artstation.svg": button(out, "btn-artstation.svg", "ARTSTATION", "bdsketch25"),
    }
    footer(out)
    dump_cache()
    import sys
    sys.path.insert(0, HERE)
    import chronicle  # first-run placeholder; the daily workflow replaces it with live numbers
    chronicle.render(None, None, os.path.join(out, "chronicle-panel.svg"))
    return widths


if __name__ == "__main__":
    import sys
    o = sys.argv[1] if len(sys.argv) > 1 else "assets"
    print(json.dumps(build_all(o)))
