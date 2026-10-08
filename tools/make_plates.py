"""巻末の陣形図（Scheffer 1664, MDZ 画像 #668–#675）を SVG で描き直す。

- 出力先：assets/plates/*.svg（サイトはこの出力をそのまま使う。ビルド工程ではない）
- 記号の並び（行数・列数）は notes/plates.md の台帳どおり。位置は等間隔の格子にそろえた
- 色は currentColor と CSS 変数 --plate-ink。SVG はインラインで使う（notes/plates.md §4.1）

使い方：python tools/make_plates.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "plates"

DX, DY = 22, 26          # 1マスの幅と高さ
FONT = 17                # 記号の字の大きさ

STYLE = """<style>
  svg.plate { color: var(--plate-ink, #1f1d1a); }
  @media (prefers-color-scheme: dark) { svg.plate { color: var(--plate-ink, #ece8e1); } }
  .plate text { fill: currentColor; font-family: "Times New Roman", "Noto Serif", serif; }
  .plate .g { font-size: %dpx; }
  .plate .head { font-size: 15px; letter-spacing: 0.06em; }
  .plate .pag { font-size: 12px; opacity: 0.7; }
  .plate .lab { font-size: 13px; font-style: italic; }
  .plate .mk { font-size: 12px; }
  .plate .rule, .plate .frame { stroke: currentColor; stroke-width: 2.4; fill: none; stroke-linecap: square; }
  .plate .dash { stroke: currentColor; stroke-width: 1.6; stroke-dasharray: 3 4; fill: none; }
  .plate .ring { stroke: currentColor; stroke-width: 1.2; fill: none; }
  .plate .dot { fill: currentColor; stroke: none; }
</style>""" % FONT


class Plate:
    def __init__(self, title, desc):
        self.title, self.desc = title, desc
        self.parts = []
        self.maxx = self.maxy = 0

    def _ext(self, x, y):
        self.maxx, self.maxy = max(self.maxx, x), max(self.maxy, y)

    def glyph(self, x, y, ch, rot=0, cls="g"):
        t = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        self.parts.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
                          f'dominant-baseline="central"{t}>{ch}</text>')
        self._ext(x + DX, y + DY)

    def mark(self, x, y, kind):
        """記号の上の小さな印。kind: '*'（星）、'o'（白丸 °）、'.'（黒丸 •）"""
        my = y - DY * 0.62
        if kind == "*":
            self.parts.append(f'<text class="mk" x="{x:.1f}" y="{my + 3:.1f}" text-anchor="middle" '
                              f'dominant-baseline="central">*</text>')
        elif kind == "o":
            self.parts.append(f'<circle class="ring" cx="{x:.1f}" cy="{my:.1f}" r="2.6"/>')
        elif kind == ".":
            self.parts.append(f'<circle class="dot" cx="{x:.1f}" cy="{my:.1f}" r="2.3"/>')

    def text(self, x, y, s, cls="lab", anchor="middle", rot=0):
        t = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        self.parts.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
                          f'dominant-baseline="central"{t}>{s}</text>')
        self._ext(x + 10, y + 12)

    def head(self, x, y, name, pag=None):
        p = f'<tspan class="pag">Pag.{pag}. </tspan>' if pag else ""
        self.parts.append(f'<text class="head" x="{x:.1f}" y="{y:.1f}" text-anchor="middle">{p}Acies {name}.</text>')
        self._ext(x, y + 8)

    def raw(self, s, x=0, y=0):
        self.parts.append(s)
        self._ext(x, y)

    def grid(self, x0, y0, rows, row0=0.0, col0=0.0):
        """rows：1行1文字列。空白は空きマス。x0, y0 は左上のマスの中心"""
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch != " ":
                    self.glyph(x0 + (col0 + c) * DX, y0 + (row0 + r) * DY, ch)

    def spread(self, x0, x1, y, items):
        """見出し行：列の数と合わない記号の並びを、x0〜x1 に等間隔で置く。items は (字, 印) の列"""
        n = len(items)
        for i, (ch, mk) in enumerate(items):
            x = x0 + (x1 - x0) * i / (n - 1) if n > 1 else (x0 + x1) / 2
            self.glyph(x, y, ch)
            if mk:
                self.mark(x, y, mk)

    def save(self, name, pad=16):
        w, h = self.maxx + pad, self.maxy + pad
        # id は、ページに複数の図を埋め込んでも重ならないよう、ファイル名から作る
        stem = name.rsplit(".", 1)[0]
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="plate" viewBox="0 0 {w:.0f} {h:.0f}" '
               f'role="img" aria-labelledby="{stem}-title {stem}-desc">\n<title id="{stem}-title">{self.title}</title>\n'
               f'<desc id="{stem}-desc">{self.desc}</desc>\n{STYLE}\n' + "\n".join(self.parts) + "\n</svg>\n")
        (OUT / name).write_text(svg, encoding="utf-8")
        print("wrote", name, f"{w:.0f}x{h:.0f}")


SRC = "BSB urn:nbn:de:bvb:12-bsb11088428-7"
NOTE = "記号の数と並びは原典どおり。位置は等間隔の格子にそろえた。記号の意味は notes/plates.md の凡例の照合を参照。"


def items(s):
    """'p μo b V b* μ p' → [('p',None),('μ','o'),...]。末尾の * o . は字の上の印"""
    out = []
    for tok in s.split():
        if len(tok) > 1 and tok[-1] in "*o.":
            out.append((tok[:-1], tok[-1]))
        else:
            out.append((tok, None))
    return out


# ---------------------------------------------------------------- 原典の座標で置く図（第3巻）
class SrcPlate(Plate):
    """原典の画像（60 dpi に換算した画素）の座標で記号を置く。S で縮め、M だけ余白をとる"""
    def __init__(self, title, desc, S, ox, oy, M=20):
        super().__init__(title, desc)
        self.S, self.ox, self.oy, self.M = S, ox, oy, M

    def X(self, x):
        return (x - self.ox) * self.S + self.M

    def Y(self, y):
        return (y - self.oy) * self.S + self.M

    def g(self, x, y, ch, mk=None, rot=0, cls="g"):
        self.glyph(self.X(x), self.Y(y), ch, rot=rot, cls=cls)
        if mk:
            self.mark(self.X(x), self.Y(y), mk)

    def row(self, y, xs, chars, marks=None):
        marks = marks or {}
        for i, (x, ch) in enumerate(zip(xs, chars)):
            self.g(x, y, ch, marks.get(i))

    def t(self, x, y, s, cls="lab", anchor="middle", rot=0):
        self.text(self.X(x), self.Y(y), s, cls=cls, anchor=anchor, rot=rot)


def cols(x0, pitch, n):
    return [x0 + pitch * i for i in range(n)]


def hdr(spec):
    """'p:230 μ:265:o ...' → (xs, chars, marks)。印は o（白丸）、.（黒丸）、*、a（アクセント ´）"""
    xs, chars, marks = [], [], {}
    for i, tok in enumerate(spec.split()):
        parts = tok.split(":")
        chars.append(parts[0])
        xs.append(float(parts[1]))
        if len(parts) > 2:
            marks[i] = parts[2]
    return xs, chars, marks


def sup(base, s):
    """上付きの字を持つ見出しの断片（tspan）"""
    return f'{base}<tspan dy="-8" font-size="9">{s}</tspan><tspan dy="8">'


B3 = ("記号の数と並びは原典どおり。位置は原典の画像から測った座標を縮めたもの（等間隔にはそろえていない）。"
      "第3巻の図の記号の多くは、写本に凡例がなく意味が決められない（notes/plates.md §2）。")


def b3_acies_05():
    pl = SrcPlate("第3巻第6章 メロスの配置（Acies V）",
                  f"Scheffer 1664, 巻末の図 Acies pertinens ad pag. 89.（MDZ 画像 #668 下半分、{SRC}）をもとに作図。"
                  f"本文は第3巻第6章（p.89、画像 #220。欄外の標識 Acies V）。図に V の番号はない。"
                  f"k の行の上の小さな s 形の印は、原典の小活字（ς か ε か不明）を小さく描いた。{B3}",
                  S=0.66, ox=180, oy=850)
    pl.t(430, 852, "Acies pertinens ad pag. 89.", cls="head")
    xs, ch, mk = hdr("p:230 μ:265:o τ:294:o b:329 b:350 b:373 b:395 ∞:425:. b:454 b:476 b:498 b:520 p:599 μ:629:o p:660")
    pl.row(924, xs, ch, mk)
    L, R = cols(202, 33.4, 11), [603, 637, 671]
    seq = [(971, "s", True), (1000, "k", True), (1049, "Γ", True), (1080, "k", True), (1133, "s", True),
           (1163, "k", True), (1211, "k", False), (1265, "φ", True), (1295, "k", True), (1341, "k", True),
           (1393, "Δ", True), (1423, "k", True)]
    for y, c, right in seq:
        for x in L + (R if right else []):
            pl.g(x, y, c, cls="mk" if c == "s" else "g")
    pl.save("b03-p089-acies-05.svg")


def b3_header(pl, y, spec):
    xs, ch, mk = hdr(spec)
    for i, (x, c) in enumerate(zip(xs, ch)):
        m = mk.get(i)
        pl.g(x, y, c, None if m == "a" else m)
        if m == "a":
            pl.t(x + 3, y - 26, "´", cls="mk")


def b3_acies_06_07():
    pl = SrcPlate("第3巻第8章 第一線のメロス（Acies VI）",
                  f"Scheffer 1664, 巻末の図 Pag.90 Acies VI（MDZ 画像 #669 上、{SRC}）をもとに作図。本文は第3巻第8章（p.90、画像 #221）。"
                  f"本文の「長さ17、深さ8」と、3＋7＋7＝17列、見出し行＋7行＝8行で合う。見出しのギリシア語は小さく、上付きの字の読みに自信がない。"
                  f"最下行の字は原典では ∂ に似た形（δ の別の字形か）。{B3}",
                  S=0.82, ox=200, oy=150)
    pl.t(500, 150, "Pag.90. Acies VI.", cls="head")
    pl.raw(f'<text class="lab" x="{pl.X(500):.1f}" y="{pl.Y(197):.1f}" text-anchor="middle">Μέρος ἀρι. καὶ ἐκλεκτῶν ἀνδρ. '
           + sup("μ", "χ") + '. ' + sup("ε", "´") + ' μ. Φοιδερ. ταγμάτων</tspan></tspan></text>', pl.X(820), pl.Y(200))
    pl.raw(f'<text class="lab" x="{pl.X(500):.1f}" y="{pl.Y(240):.1f}" text-anchor="middle">ἀνδρῶν '
           + sup("μ", "χ") + '.</tspan></text>')
    b3_header(pl, 297, "k:244 k:271 k:298 μ:363:o p:383 b:406 b:421 b:449:. b:465 U:494:. b:521 b:536 p:557 "
                       "U:590:. p:616 b:641 b:657 U:686:. b:714 b:731 p:751 μ:771:. p:800")
    B1, B2, B3_ = cols(245, 27.6, 3), cols(359, 26.0, 7), cols(575, 27.6, 7)
    for r in range(7):
        pl.row(350 + 53.7 * r, B1 + B2 + B3_, "k" * 17)
    pl.row(727, [B1[1]] + B2[1:5] + B3_[2:6], "∂" * 9)
    pl.save("b03-p090-acies-06.svg")

    pl = SrcPlate("第3巻第8章 イッリュリキアノイのメロス（Acies VII）",
                  f"Scheffer 1664, 巻末の図 Acies VII（MDZ 画像 #669 下、{SRC}）をもとに作図。本文は第3巻第8章（p.90、画像 #221）。"
                  f"見出しは「イッリュリキアノイのメロス。包囲兵の旗1つか2つ」と読める（上付きの字の読みに自信がない）。"
                  f"右の2列は包囲兵か（推測）。最下行の字は原典では ∂ に似た形。{B3}",
                  S=0.82, ox=250, oy=830)
    pl.t(500, 835, "Acies VII.", cls="head")
    pl.raw(f'<text class="lab" x="{pl.X(500):.1f}" y="{pl.Y(892):.1f}" text-anchor="middle">Μέρος Ἰλλυρικιανῶν ἀν. '
           + sup("μ", "χ") + ', ε ὑπερκερ. βάνδ. ά ἢ β.</tspan></text>', pl.X(760), pl.Y(895))
    b3_header(pl, 960, "p:310 μ:334:o p:357 b:378 b:395 b:412 M:445:. b:481 b:497 b:516:a p:544 μ:576:. p:599 k:670 k:697")
    M, R = cols(311, 27.3, 12), [669, 697]
    for r in range(7):
        pl.row(1014 + 53.8 * r, M + R, "k" * 14)
    pl.row(1390, M[5:9], "∂" * 4)
    pl.save("b03-p090-acies-07.svg")


def b3_acies_08():
    pl = SrcPlate("第3巻第8章 第二線と輜重（Acies VIII）",
                  f"Scheffer 1664, 巻末の図 Pag.91 Acies VIII（MDZ 画像 #670 上、{SRC}）をもとに作図。本文は第3巻第8章（p.91、画像 #222）。"
                  f"λ は荷駄（ラベル ἀδέστρατα による）。見出し行の p・b・U・K と印の意味は不明（notes/plates.md）。{B3}",
                  S=0.96, ox=30, oy=40)
    pl.t(420, 60, "Pag.91. Acies VIII.", cls="head")
    b3_header(pl, 145, "p:50 μ:80:. p:103 b:122 b:137 U:165:. p:200 μ:225:. p:249 K:284 K:310 p:345 μ:377:o p:400 "
                       "b:432 b:450 U:486 b:512 b:530 p:561 μ:588:. p:609 p:641 μ:665:o p:688 b:712 b:727 μ:750:. b:774 b:789")
    pl.t(545, 211, "(", cls="g")
    b3_header(pl, 211, "p:561 μ:585:o p:608 μ:631:o p:655 b:677 b:693 U:720:. p:746 μ:770:. p:793")
    pl.row(254, cols(230, 22.8, 18), "k" * 18)
    blocks = cols(167, 22.8, 5) + cols(306, 23.2, 5) + cols(447, 23.0, 5) + cols(588, 22.0, 5)
    for r in range(5):
        pl.row(298 + 33.5 * r, blocks, "k" * 20)
    pl.t(255, 480, "ὁ τοῦλδος")
    pl.t(533, 480, "ἀδεστρ. ά τάξις")
    pl.t(220, 530, "νωτοφύλακες")
    pl.t(640, 530, "νωτοφύλακες")
    xs = [209, 232, 255] + cols(303, 23.4, 5) + cols(445, 22.4, 6) + [606, 628, 650]
    for r in range(5):
        mid = "b" if r == 0 else "k"
        pl.row(572 + 33.3 * r, xs, "k" + mid + "k" + "kkkkk" + "λλλλλλ" + "k" + mid + "k")
    pl.t(426, 755, "ἀδέστρατα β τάξις")
    for r in range(4):
        pl.row(801 + 34.7 * r, cols(315, 22.2, 11), "λ" * 11)
    pl.save("b03-p091-acies-08.svg")


def b3_grids():
    def simple(name, title, src, page, body, head_name, pag, rows):
        pl = Plate(title, f"Scheffer 1664, 巻末の図 {src}（MDZ 画像 {page}、{SRC}）をもとに作図。本文は{body}。{NOTE}")
        w = max(len(r) for r in rows)
        x0 = DX / 2 + 4
        pl.head(x0 + (w - 1) * DX / 2, 16, head_name, pag)
        pl.grid(x0, 44, rows)
        pl.save(name)

    simple("b03-p092-acies-09.svg", "第3巻第9章 メロス1つ（Acies IX）", "Pag.92 Acies IX", "#670",
           "第3巻第9章（p.92、画像 #223）。本文の「長さ23、深さ7」と、図の12列×5行は合わない（原典どおりに描いた）",
           "IX", 92, ["k" * 12] * 5)
    simple("b03-p092-acies-10.svg", "第3巻第9章 第二線（Acies X）", "Acies X", "#670",
           "第3巻第9章（p.92、画像 #223）。下の6列×2行は、2つのメロスの間のすき間に置くタグマか（推測。第3巻第8章「中くらいの軍なら深さ2で足りる」）",
           "X", None, ["kkkk" + " " * 6 + "kkkk"] * 3 + ["    " + "k" * 6] * 2)
    simple("b03-p093-acies-11.svg", "第3巻第10章 中くらいの軍の第一線（Acies XI）", "Pag.93 Acies XI", "#671",
           "第3巻第10章（p.93、画像 #224）。見出しの「深さ8（ラテン語訳7）、長さ9」と、図の15列×5行は合わない（原典どおりに描いた）",
           "XI", 93, ["kkkkk kkkkk kkkkk"] * 5)
    simple("b03-p093-acies-12.svg", "第3巻第10章 中くらいの軍の第二線（Acies XII）", "Acies XII", "#671",
           "第3巻第10章（p.93、画像 #224）", "XII", None, ["k" * 12] * 5)


def b3_acies_13_17():
    pl = Plate("第3巻第10章 側面防護兵と包囲兵の図（Acies XIII–XVII）",
               f"Scheffer 1664, 巻末の図 Pag.94 Acies XIII–XV, Pag.95 Acies XVI–XVII（MDZ 画像 #671 下、{SRC}）をもとに作図。"
               f"本文は第3巻第10章の5つの小見出し（p.94–95、画像 #225–#226）。原典は線と文字だけの模式図で、見出しと図の切れ目があいまいなため"
               f"（notes/plates.md §3.8）、版面の並びのまま1枚に描いた。ΣΙΨΟ（逆並び）は敵の正面、ΟΨΙΣ は味方の正面か（推測）。"
               f"縦書きのラベルの向きは原典どおり。位置と線の長さはおおよそ。")
    W = 520
    c = W / 2

    def letters(y, s, x0=c - 66, step=44):
        for i, ch in enumerate(s):
            pl.text(x0 + i * step, y, ch, cls="lab-up")

    def rule(x1, x2, y):
        pl.raw(f'<line class="rule" x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}"/>', x2, y)

    labs5 = ["πλαγιοφυλ.", "μέρος.", "μέρος.", "μέρος.", "ὑπερκεραστ."]
    xs5 = [60, 160, 245, 330, 440]

    def line5(y, segs):
        for lab, x in zip(labs5, xs5):
            pl.text(x, y, lab)
        for x1, x2 in segs:
            rule(x1, x2, y + 16)

    y = 20
    pl.head(c, y, "XIII", 94)
    rule(10, W - 10, y + 14)
    letters(y + 40, "ΣΙΨΟ")
    pl.text(c + 66 + 70, y + 40, "/", cls="lab-up")
    pl.head(c, y + 78, "XIV")
    letters(y + 104, "ΟΨΙΣ")
    line5(y + 136, [(10, 110), (135, 185), (220, 270), (305, 355), (390, 490)])
    pl.text(c - 20, y + 182, "ἡ τῶν ἐχθρῶν τάξις")
    rule(30, W - 70, y + 210)
    for i, s in enumerate(["δροῦγγος", "λανθά-", "νων"]):
        pl.text(W - 10 - i * 18, y + 196 + (0 if i == 0 else -16 if i == 1 else -32), s, rot=90)
    y += 236
    letters(y, "ΣΙΨΟ")
    pl.head(c, y + 34, "XV")
    letters(y + 60, "ΟΨΙΣ")
    line5(y + 92, [(10, 110), (135, 158), (162, 185), (220, 243), (247, 270), (305, 328), (332, 355), (395, 450)])
    y += 140
    pl.head(c, y, "XVI", 95)
    rule(50, W - 90, y + 14)
    letters(y + 38, "ΣΙΨΟ")
    letters(y + 62, "ΟΨΙΣ")
    for x in (110, 250, 390):
        pl.text(x, y + 92, "μέρος")
        rule(x - 50, x + 50, y + 108)
    pl.raw(f'<path class="frame" d="M 40 {y + 4} Q 32 {y + 60} 40 {y + 114}"/>', 40, y + 114)
    pl.text(20, y + 60, "πλαγιοφυλ.", rot=-90)
    pl.raw(f'<path class="frame" d="M {W - 84} {y + 4} Q {W - 74} {y + 60} {W - 84} {y + 114}"/>', W - 74, y + 114)
    pl.text(W - 62, y + 60, "ὑπερκεραστ.", rot=-90)
    pl.text(W - 30, y + 46, "δροῦγγος ά", rot=90)
    for r, n in enumerate([4, 3, 2, 1]):
        for k in range(n):
            pl.raw(f'<circle class="ring" cx="{W - 52 + k * 11:.1f}" cy="{y + 104 + r * 12:.1f}" r="4"/>', W - 10, y + 150)
    y += 170
    pl.head(c, y, "XVII")
    pl.text(c - 60, y + 24, "ἡ τῶν ἐχθρῶν")
    pl.text(W - 100, y + 24, "δροῦγγος Γ")
    rule(20, 140, y + 38)
    rule(250, W - 60, y + 38)
    letters(y + 62, "ΣΙΨΟ")
    letters(y + 86, "ΟΨΙΣ")
    for lab, x in zip(["πλαγιοφύλ.", "μέρος.", "μέρος.", "μέρος."], [110, 210, 290, 370]):
        pl.text(x, y + 116, lab)
    for x1, x2 in [(20, 120), (124, 220), (226, 320), (326, 420), (426, W - 64)]:
        rule(x1, x2, y + 140)
    pl.raw(f'<path class="frame" d="M {W - 58} {y + 44} Q {W - 42} {y + 92} {W - 56} {y + 140}"/>', W - 42, y + 140)
    pl.text(W - 24, y + 92, "ὑπερκεραστ.", rot=-90)
    pl.maxx = W - 16
    pl.save("b03-p094-acies-13-17.svg")


# ---------------------------------------------------------------- 第12巻 #672 Acies A
def acies_a():
    pl = Plate("第12巻第3章 混成戦列（Acies A）",
               f"Scheffer 1664, 巻末の図 Pag.291 Acies A（MDZ 画像 #672、90度回転して組まれた図、{SRC}）をもとに作図。"
               f"本文は第12巻第3章（p.291、画像 #422）。版面の見出しの数字は Pag.291。{NOTE}")
    pl.head(0, 0, "A", 291)  # 位置はあとで中央に直す
    blocks = [
        ("μέρος πεζ.", "inf"), ("μέρος Καβαλ.", ("p μo b V b* μ p", 6)),
        ("μέρ. πεζ.", "inf"), ("μέρ. Καβαλ.", ("p μ. b ∞* b μ. p", 6)),
        ("μέρος πεζ.", "inf"), ("μέρ. Καβαλ", ("p μ. b V b μo p", 6)),
        ("μέρος πεζ.", "inf"),
    ]
    x = DX / 2 + 4
    y_lab, y_hdr = 40, 74
    for lab, kind in blocks:
        if kind == "inf":
            cols = 5
            pl.text(x + (cols - 1) * DX / 2, y_lab, lab)
            for c, ch in enumerate("TTNTT"):
                pl.glyph(x + c * DX, y_hdr, ch)
            pl.mark(x + 2 * DX, y_hdr, "*")
            pl.grid(x, y_hdr + DY, ["TTTTT"] * 4)
        else:
            hdr, cols = kind
            pl.text(x + (cols - 1) * DX / 2, y_lab, lab)
            pl.spread(x - 3, x + (cols - 1) * DX + 3, y_hdr, items(hdr))
            pl.grid(x, y_hdr + DY, ["k" * cols] * 4)
        x += cols * DX + DX
    pl.parts[0] = pl.parts[0].replace('x="0.0" y="0.0"', f'x="{(x - DX) / 2:.1f}" y="16"')
    pl.save("b12-p291-acies-a.svg")


# ---------------------------------------------------------------- 第12巻 #672 Acies B prima / secunda
def acies_b():
    pl = Plate("第12巻第4章 騎兵の第一の戦列と第二の戦列（Acies B prima, B secunda）",
               f"Scheffer 1664, 巻末の図 Pag.291 Acies B prima と Acies B secunda（MDZ 画像 #672、90度回転して組まれた図、{SRC}）をもとに作図。"
               f"本文は第12巻第4章（p.291、画像 #422）。左右の φαλαγγίαι で軽装兵 ι の行数が違う（1行と2行）のは原典どおり。{NOTE}")
    y_lab, y0 = 44, 74
    x = DX / 2 + 4
    # B prima
    pl.text(x + 2 * DX, y_lab, "φαλαγγίαι")
    pl.grid(x, y0, ["TTTTT"] * 5 + ["ίίίίί"])
    x += 6 * DX
    pl.text(x + 3 * DX, y_lab, "τάξις ά καβαλλ.")
    pl.grid(x, y0, ["kkkkkkk"] * 10)
    x += 8 * DX
    pl.text(x + 2 * DX, y_lab, "φαλαγγίαι.")
    pl.grid(x, y0, ["TTTTT"] * 5 + ["ίίίίί"] * 2)
    x += 6 * DX
    pl.grid(x, y0, ["kkk"] * 7, row0=3)
    x_end_prima = x + 2 * DX
    # 見出し B prima（左の4ブロックの中央）
    pl.parts.insert(0, f'<text class="head" x="{(DX / 2 + 4 + x_end_prima) / 2:.1f}" y="16" text-anchor="middle">Acies B. prima.</text>')
    # B secunda
    x += 5 * DX
    xs = x
    pl.grid(x, y0, ["TTTTTT"] * 7 + ["ίίίίίί"], row0=-0.5)
    x += 7 * DX
    pl.grid(x, y0, ["kkk"] * 7, row0=3)
    pl.parts.insert(0, f'<text class="head" x="{(xs + x + 2 * DX) / 2:.1f}" y="16" text-anchor="middle">Acies B. Secunda.</text>')
    pl.save("b12-p291-acies-b.svg")


# ---------------------------------------------------------------- 第12巻 #673 Acies C / D / E
def acies_c():
    pl = Plate("第12巻第5章 もう一つの戦列（Acies C）",
               f"Scheffer 1664, 巻末の図 Acies C（MDZ 画像 #673、{SRC}）をもとに作図。本文は第12巻第5章（p.291、画像 #422）。"
               f"原典は中央を小さい活字の τ で組む。ここでは T で描いた。{NOTE}")
    pl.head(0, 0, "C")
    y0 = 52
    x = DX / 2 + 4
    pl.text(x + 2 * DX, y0 + 1 * DY, "νωτοφύλ.")
    pl.grid(x, y0, ["TTTTT"] * 6 + ["ίίίίί"], row0=2)
    x += 7 * DX
    pl.grid(x, y0, ["TTTTTT"] * 7)
    x += 8 * DX
    pl.text(x + 2 * DX, y0 + 1 * DY, "νωτοφύλ.")
    pl.grid(x, y0, ["TTTTT"] * 6 + ["ίίίίί"], row0=2)
    w = x + 5 * DX
    pl.parts[0] = pl.parts[0].replace('x="0.0" y="0.0"', f'x="{w / 2:.1f}" y="16"')
    pl.save("b12-p291-acies-c.svg")


def acies_d():
    pl = Plate("第12巻第6章 横の戦列（Acies D）",
               f"Scheffer 1664, 巻末の図 Pag.239 Acies D（MDZ 画像 #673、{SRC}）をもとに作図。"
               f"見出しの「Pag.239」は p.292 の誤植（本文は第12巻第6章、p.292、画像 #423）。{NOTE}")
    pl.head(0, 0, "D", "239 [=292]")
    y0 = 44
    x = DX / 2 + 4
    for _ in range(4):
        pl.grid(x, y0, ["TTTT"] * 5 + ["ίίίί"] * 2)
        x += 5 * DX
    w = x - DX
    pl.parts[0] = pl.parts[0].replace('x="0.0" y="0.0"', f'x="{w / 2:.1f}" y="16"')
    pl.save("b12-p292-acies-d.svg")


def acies_e():
    pl = Plate("第12巻第7章 縦の戦列（Acies E）",
               f"Scheffer 1664, 巻末の図 Acies E（MDZ 画像 #673、{SRC}）をもとに作図。本文は第12巻第7章（p.292、画像 #423）。{NOTE}")
    pl.head(0, 0, "E")
    pl.grid(DX / 2 + 4 + 2 * DX, 44, ["TTTTT", "ooooo", "ooooo"] * 6)
    pl.parts[0] = pl.parts[0].replace('x="0.0" y="0.0"', f'x="{DX / 2 + 4 + 4 * DX:.1f}" y="16"')
    pl.save("b12-p292-acies-e.svg")


# ---------------------------------------------------------------- 第12巻 #674 Pag.299
def epikampios():
    pl = Plate("第12巻第1章 後ろへ曲がった混成戦列（Pag.299 の図）",
               f"Scheffer 1664, 巻末の図 Pag.299（名前なし。MDZ 画像 #674、{SRC}）をもとに作図。本文は第12巻第1章の終わりの図の見出し"
               f"「歩兵と騎兵を持つ、後ろへ曲がった混成戦列の図」（p.299、画像 #430）。原典は前列の兵の記号 b を回転させて組み、"
               f"字の上が向く方向を示す（上の列は前、左翼の外の列は左、右翼の外の列は右、れんがの下辺は後ろ）。ここでも同じように回した。"
               f"両翼の後ろ半分の短い線の意味は不明で、原典どおり破線で描いた。左翼（o 5つが8行）と右翼（o 6つが6行）が左右対称でないのも原典どおり。{NOTE}")
    pl.text(0, 0, "Pag.299.", cls="head")
    y0 = 52
    xL = DX / 2 + 4
    # 左翼：b×6、横倒しの b ＋ o5 ×8、横倒しの b ＋ o3 ＋ 線 ×12
    for c in range(6):
        pl.glyph(xL + c * DX, y0, "b")
    for r in range(1, 21):
        y = y0 + r * DY
        pl.glyph(xL, y, "b", rot=-90)
        n = 5 if r <= 8 else 3
        for c in range(1, n + 1):
            pl.glyph(xL + c * DX, y, "o")
        if r > 8:
            pl.raw(f'<line class="dash" x1="{xL + 3.6 * DX:.1f}" y1="{y:.1f}" x2="{xL + 5.4 * DX:.1f}" y2="{y:.1f}"/>')
    # 中央：b×13、o13×4、ι13×2
    xC = xL + 8 * DX
    pl.grid(xC, y0, ["b" * 13, "o" * 13, "o" * 13, "o" * 13, "o" * 13, "ί" * 13, "ί" * 13])
    # 右翼：b×6、o6 ＋ 横倒しの b ×6、線 ＋ o3 ＋ 横倒しの b ×14
    xR = xC + 15 * DX
    for c in range(6):
        pl.glyph(xR + c * DX, y0, "b")
    for r in range(1, 21):
        y = y0 + r * DY
        pl.glyph(xR + 6 * DX, y, "b", rot=90)
        if r <= 6:
            for c in range(6):
                pl.glyph(xR + c * DX, y, "o")
        else:
            for c in range(3, 6):
                pl.glyph(xR + c * DX, y, "o")
            pl.raw(f'<line class="dash" x1="{xR - 0.4 * DX:.1f}" y1="{y:.1f}" x2="{xR + 2.4 * DX:.1f}" y2="{y:.1f}"/>')
    # 下：K 7×5 を左右に、その下に πλινθίον
    yK = y0 + 23 * DY
    xKL, xKR = xL, xR + 6 * DX - 6 * DX
    pl.grid(xKL, yK, ["KKKKKKK"] * 5)
    pl.grid(xKR, yK, ["KKKKKKK"] * 5)
    yP = yK + 7 * DY

    def plinth(x):
        for c in range(4):
            pl.glyph(x + c * DX, yP, "b")              # 前
            pl.glyph(x + c * DX, yP + 3 * DY, "b", rot=180)  # 後ろ（版面は q）
        for r in (1, 2):
            pl.glyph(x, yP + r * DY, "b", rot=-90)     # 左
            pl.glyph(x + 3 * DX, yP + r * DY, "b", rot=90)  # 右
            pl.glyph(x + DX, yP + r * DY, "o")
            pl.glyph(x + 2 * DX, yP + r * DY, "o")
        for i, s in enumerate(["πλινθ. ἤτοι", "νωτοφύ-", "λακες."]):
            pl.text(x + 1.5 * DX, yP + 4.2 * DY + i * 16, s)

    plinth(xKL)
    plinth(xKR + 3 * DX)
    w = xR + 7 * DX
    pl.parts[0] = pl.parts[0].replace('x="0.0" y="0.0"', f'x="{w / 2:.1f}" y="18"')
    pl.save("b12-p299-epikampios.svg")


# ---------------------------------------------------------------- 第12巻 #675 Pag.344–345 Acies A–D
def p344():
    L = list("ΜΕΤΟΠΟΝ")  # 版面の綴り（Ο はオミクロン）
    pl = Plate("第12巻第8章第20節の図 A–D（横の戦列と、一重・二重・四重の縦の密集隊）",
               f"Scheffer 1664, 巻末の図 Pag.344 Acies A–C, Pag.345 Acies D（MDZ 画像 #675 上半分、{SRC}）をもとに作図。"
               "本文は第12巻第8章第20節（p.344–345、画像 #475–#476）。ΜΕΤΟΠΟΝ（正面）は版面の綴りのまま。"
               "B の枠にはラベルがない（原典どおり）。原典では枠の辺ごとに線の太さが違うが、ここでは同じ太さで描いた。")
    W = 420
    pl.head(W / 2, 26, "A", 344)
    for i, ch in enumerate(L):
        cx = 36 + i * 58
        pl.raw(f'<line class="rule" x1="{cx - 16}" y1="70" x2="{cx + 16}" y2="70"/>', cx + 16, 70)
        pl.text(cx, 52, ch, cls="lab-up", rot=90)

    def frame(x, y, w, h):
        pl.raw(f'<rect class="frame" x="{x}" y="{y}" width="{w}" height="{h}"/>', x + w, y + h)

    def vlabel(x, y0, y1, mode):
        seq = L if mode in ("upright", "cw") else L[::-1]
        rot = {"upright": 0, "inverted": 180, "cw": 90, "ccw": -90}[mode]
        for i, ch in enumerate(seq):
            pl.text(x, y0 + (y1 - y0) * (i + 0.5) / len(L), ch, cls="lab-up", rot=rot)

    pl.head(80, 112, "B")
    frame(60, 126, 40, 190)
    pl.head(300, 112, "C")
    vlabel(232, 130, 312, "inverted")
    frame(246, 126, 40, 190)
    frame(314, 126, 40, 190)
    vlabel(368, 130, 312, "upright")
    pl.head(W / 2, 362, "D", 345)
    for x in (54, 132):
        vlabel(x - 14, 380, 576, "ccw")
        frame(x, 376, 36, 204)
    for x in (252, 330):
        frame(x, 376, 36, 204)
        vlabel(x + 50, 380, 576, "cw")
    pl.maxx = W - 16
    pl.save("b12-p344-acies-a-d.svg")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    STYLE = STYLE.replace(".plate .lab {", ".plate .lab-up { font-size: 15px; }\n  .plate .lab {")
    b3_acies_05()
    b3_acies_06_07()
    b3_acies_08()
    b3_grids()
    b3_acies_13_17()
    acies_a()
    acies_b()
    acies_c()
    acies_d()
    acies_e()
    epikampios()
    p344()
