"""全章の「解説／図解／照合」の状況一覧（coverage.html）を書き出す。

- 各巻ページ（books/book-NN.html）の「照合の状況」（<h2 id="status">の下の表）を読み、
  巻ごとの集計と、行ごとの一覧を1ページにまとめる
- 巻ページの表を直したら `python tools/make_coverage.py` を実行する。サイトのビルド工程ではなく、
  書き出した HTML をそのまま公開する

使い方：python tools/make_coverage.py
"""
import html
import re
from pathlib import Path

from update_nav import BOOKS, ROOT, page

# 巻ごとの章の数（notes/book-NN.md の章台帳による）
CHAPTERS = {
    1: "9章", 2: "19章", 3: "16章", 4: "5章", 5: "5章", 6: "6章",
    7: "33章（前半16・後半17）", 8: "2章（心得44・格言99）", 9: "5章", 10: "4章", 11: "5章",
    12: "総目次10項目＋番号なしの部分",
}

ROW = re.compile(r'<tr><td>(.*?)</td><td class="status (\w+)">(.*?)</td>'
                 r'<td class="status (\w+)">(.*?)</td><td class="status (\w+)">(.*?)</td></tr>')


def rows_of(n):
    s = page(n).read_text(encoding="utf-8")
    i = s.index('id="status"')
    j = s.index("</table>", i)
    return ROW.findall(s[i:j])


def fix_links(cell, n):
    # 巻ページの中のリンクを、サイトの最上位から見たリンクに直す
    cell = re.sub(r'href="#', f'href="books/book-{n:02d}.html#', cell)
    cell = cell.replace('href="../', 'href="')
    return cell


def main():
    summary = []
    detail = []
    tot = {"rows": 0, "fig": 0, "done": 0, "part": 0, "todo": 0}
    for n, title, _ in BOOKS:
        if not page(n).exists():
            continue
        rows = rows_of(n)
        fig = sum(1 for r in rows if r[3] == "done")
        chk = {k: sum(1 for r in rows if r[5] == k) for k in ("done", "part", "todo")}
        tot["rows"] += len(rows)
        tot["fig"] += fig
        for k in chk:
            tot[k] += chk[k]
        link = f'<a href="books/book-{n:02d}.html">第{n}巻 {html.escape(title)}</a>'
        summary.append(
            f'    <tr><td>{link}</td><td>{CHAPTERS[n]}</td><td>{len(rows)}</td><td>{fig}</td>'
            f'<td class="status done">{chk["done"]}</td><td class="status part">{chk["part"]}</td>'
            f'<td class="status todo">{chk["todo"]}</td></tr>')
        body = "\n".join(
            f'    <tr><td>{fix_links(r[0], n)}</td><td class="status {r[1]}">{fix_links(r[2], n)}</td>'
            f'<td class="status {r[3]}">{fix_links(r[4], n)}</td><td class="status {r[5]}">{fix_links(r[6], n)}</td></tr>'
            for r in rows)
        detail.append(f'''<section id="b{n:02d}">
<h3>{link}</h3>
<div class="table-wrap">
<table>
  <thead><tr><th>章</th><th>解説</th><th>図解</th><th>照合</th></tr></thead>
  <tbody>
{body}
  </tbody>
</table>
</div>
</section>''')
    summary.append(
        f'    <tr><th>合計</th><td></td><td>{tot["rows"]}</td><td>{tot["fig"]}</td>'
        f'<td class="status done">{tot["done"]}</td><td class="status part">{tot["part"]}</td>'
        f'<td class="status todo">{tot["todo"]}</td></tr>')
    out = TEMPLATE.replace("{{SUMMARY}}", "\n".join(summary)).replace("{{DETAIL}}", "\n\n".join(detail))
    (ROOT / "coverage.html").write_text(out, encoding="utf-8", newline="\n")
    print("coverage.html", tot)


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>状況一覧 — ストラテギコン図解</title>
<meta name="description" content="『ストラテギコン』全12巻の全章について、このサイトの解説・図解・ギリシア語との照合がどこまで済んでいるかの一覧です。">
<link rel="stylesheet" href="assets/style.css">
<script src="assets/nav.js"></script>
</head>
<body>

<header class="site-header">
  <div class="inner">
    <a class="site-title" href="index.html">ストラテギコン図解</a>
    <nav class="site-nav" aria-label="サイト内">
      <a href="index.html">全体像</a>
      <a href="intro.html">導入</a>
      <a href="index.html#books">巻の一覧</a>
      <a href="glossary.html">用語集</a>
    </nav>
    <button class="theme-toggle" type="button">暗い表示へ</button>
  </div>
</header>

<main>

<p class="meta">ストラテギコン図解 状況一覧</p>
<h1>全章の状況一覧
  <span class="sub">解説・図解・照合が、どの章でどこまで済んでいるか</span>
</h1>

<p>このサイトは、シェファー版（1664年）のラテン語訳を主に読み、数字・用語・解釈が分かれそうな箇所をギリシア語の本文で確かめて書いています。このページは、各巻ページの末尾にある「照合の状況」の表を集めたものです。いくつかの章をまとめて1行にしている所があります。</p>

<h2 id="legend">表の見方</h2>
<ul>
  <li><strong>解説</strong>：<span class="status done">済</span> は、その章の内容を巻ページで説明済みという意味です。全12巻の全章について、解説は済んでいます。</li>
  <li><strong>図解</strong>：図や表の名前が書いてある行は、その章について図や表があること。<span class="status todo">—</span> は、図がないこと（図にする必要が薄い章も含みます）。</li>
  <li><strong>照合</strong>：ギリシア語の本文で確かめた程度です。<span class="status done">済</span> は、その章で問題になる数字や語をギリシア語で確認したもの。<span class="status part">一部</span> は、一部の語や数字だけを確認したもの。<span class="status todo">未</span> は、ラテン語訳だけで読んだもの。いずれも全文の逐語的な照合ではありません。</li>
</ul>

<h2 id="summary">巻ごとの集計</h2>
<div class="table-wrap wide">
<table>
  <thead><tr><th>巻</th><th>章の数</th><th>表の行</th><th>図のある行</th><th>照合 済</th><th>一部</th><th>未</th></tr></thead>
  <tbody>
{{SUMMARY}}
  </tbody>
</table>
</div>
<p class="meta">巻末の陣形図（16枚）は、<a href="books/book-03.html">第3巻</a>（9枚）と<a href="books/book-12.html">第12巻</a>（7枚）のページに入っています。読み取れなかった記号は、各図の注に書いています。</p>

<h2 id="detail">章ごとの一覧</h2>

{{DETAIL}}

<h2 id="others">巻ページ以外</h2>
<ul>
  <li><a href="intro.html">導入</a>：前付け（献辞、シェファーの序文、著者自身の序文、書名と作者の注）を読んで書きました。</li>
  <li><a href="peoples.html">諸民族の地図</a>、<a href="compare.html">他の兵法書との比較</a>：原典の内容と、一般的な知識（補足）を分けて書いています。</li>
  <li>アッリアノス『戦術論』（シェファー版の前半）は、このサイトの対象外で、まだ読んでいません。</li>
</ul>
<p class="meta">このページは <code>tools/make_coverage.py</code> で、各巻ページの表から作っています。読解メモは <a href="https://github.com/samsreeds/strategikon/tree/main/notes">notes/</a> にあります。</p>

</main>

<footer class="site-footer">
  <div class="inner">
    <p>原典：Joannes Schefferus (ed.), <i>Arriani Tactica &amp; Mauricii Artis militaris libri duodecim</i>, Upsaliae 1664. Regensburg, Staatliche Bibliothek, 999/Class.170, urn:nbn:de:bvb:12-bsb11088428-7（バイエルン州立図書館デジタル版 MDZ）。</p>
    <p>解説の文章はすべてこのサイトの独自のものです。</p>
  </div>
</footer>

</body>
</html>
"""

if __name__ == "__main__":
    main()
