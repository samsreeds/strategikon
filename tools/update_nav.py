"""巻ページの「前後の巻」リンクと、index.html の巻の一覧を書き直す。

- books/book-NN.html があるかどうかを見て、ある巻はリンクに、ない巻は「準備中」にする
- 書き直すのは次の部分だけ（ほかには触らない）
  - 各巻ページの <nav class="pager" …>…</nav>（上と下の2か所）
  - index.html の <!-- books:start --> と <!-- books:end --> の間
- 巻ページを足したら `python tools/update_nav.py` を実行する。サイトのビルド工程ではなく、
  書き出した HTML をそのまま公開する

使い方：python tools/update_nav.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (番号, 短い題, 一覧の説明)
BOOKS = [
    (1, "序論", "騎兵の武装と訓練、部隊の編成、指揮官、軍の規律"),
    (2, "騎兵の戦列", "第一線と第二線、クルソレスとデフェンソレス、列の深さ"),
    (3, "タグマの配置", "陣形図と記号、騎兵の号令、側面防護兵と包囲兵"),
    (4, "伏兵", "待ち伏せ、偽りの敗走、隠し壕や鉄菱のわな"),
    (5, "輜重", "荷車と荷駄、従者、戦いのときの輜重の置き方"),
    (6, "さまざまな戦列と訓練", "スキタイ式・アラン式・アフリカ式・イタリア式の戦列"),
    (7, "将の心得", "戦いの前と戦いの日に将が気を配ること"),
    (8, "心得と格言", "将のための心得と、短い格言の数々"),
    (9, "奇襲と偵察", "夜襲、敵地への侵入、隘路、偵察"),
    (10, "攻城と籠城", "攻城兵器と防御、水の貯え方、急造の砦"),
    (11, "諸民族の戦い方", "ペルシア人、アヴァール人・トルコ人、フランク人・ランゴバルド人、スラヴ人"),
    (12, "歩兵と混成戦列、陣営、狩り", "歩兵の装備と編成、ラテン語の号令、陣営、動く砦、巻き狩り"),
]


def page(n):
    return ROOT / "books" / f"book-{n:02d}.html"


def pager(n):
    def side(m, cls, arrow_left):
        if m < 1 or m > 12:
            return "<span></span>"
        title = BOOKS[m - 1][1]
        name = f"第{m}巻 {title}"
        if page(m).exists():
            label = f"← {name}" if arrow_left else f"{name} →"
            return f'<a href="book-{m:02d}.html" class="{cls}">{label}</a>'
        label = f"← {name}（準備中）" if arrow_left else f"{name}（準備中） →"
        return f'<span class="{cls} soon">{label}</span>'
    return ('<nav class="pager" aria-label="前後の巻">\n  ' + side(n - 1, "prev", True)
            + "\n  " + side(n + 1, "next", False) + "\n</nav>")


def book_list():
    rows = []
    for n, title, desc in BOOKS:
        head = f'<span class="n">第{n}巻</span><span class="t">{title}</span>'
        if page(n).exists():
            rows.append(f'  <li><a href="books/book-{n:02d}.html">{head}</a><span class="d">{desc}</span></li>')
        else:
            rows.append(f'  <li>{head}<span class="soon">準備中</span><span class="d">{desc}</span></li>')
    return "<!-- books:start -->\n" + "\n".join(rows) + "\n  <!-- books:end -->"


def main():
    for n, *_ in BOOKS:
        p = page(n)
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        s2, k = re.subn(r'<nav class="pager"[^>]*>.*?</nav>', pager(n), s, flags=re.S)
        if k:
            p.write_text(s2, encoding="utf-8")
        print(p.name, "pager x", k)
    idx = ROOT / "index.html"
    s = idx.read_text(encoding="utf-8")
    s2, k = re.subn(r"<!-- books:start -->.*?<!-- books:end -->", book_list(), s, flags=re.S)
    idx.write_text(s2, encoding="utf-8")
    print("index.html list x", k)


if __name__ == "__main__":
    main()
