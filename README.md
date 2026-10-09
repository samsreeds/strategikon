# ストラテギコン図解

東ローマ帝国の軍事教本、マウリキオス帝（在位582–602）に帰せられる『ストラテギコン』全12巻を、前提知識のない読者向けに図解・解説する静的サイトです。

**公開先：** https://samsreeds.github.io/strategikon/

## 原典

- Joannes Schefferus (ed.), *Arriani Tactica & Mauricii Artis militaris libri duodecim*, Upsaliae 1664（シェファー版。ギリシア語とラテン語の対訳）
- 所蔵：Regensburg, Staatliche Bibliothek, 999/Class.170
- URN：urn:nbn:de:bvb:12-bsb11088428-7
- デジタル版：バイエルン州立図書館 MDZ — https://www.digitale-sammlungen.de/en/view/bsb11088428
- 権利表示：NoC-NC（[No Copyright – Non-Commercial Use Only](https://rightsstatements.org/vocab/NoC-NC/1.0/)）

サイトでは原典の画像は使わず、巻末の陣形図も SVG で描き直しています。本文中の「#NNN」は、MDZ から入手した PDF の画像番号です（MDZ のビューアーの番号より 1 大きい）。解説の文章はすべてこのサイトの独自のもので、現代の翻訳は引用していません。

## 構成

```
index.html, intro.html, peoples.html, compare.html, glossary.html, coverage.html
books/book-01.html … book-12.html   巻ごとのページ
assets/                             style.css、nav.js、favicon.svg、plates/（描き直した陣形図）
notes/                              読解メモ
tools/                              作業用のスクリプト
```

- **notes/ の読解メモからページを作っています。** 原典は1巻ずつ読み、`notes/book-NN.md`（章台帳、章ごとの要約、用語、不確かな箇所）にまとめました。ほかに、ページ地図（`page-map.md`）、前付け（`preface.md`）、陣形図（`plates.md`）、ギリシア語との照合の記録（`collation.md`）、作業の記録（`progress.md`）があります
- ラテン語訳を主に読み、数字・用語・解釈が分かれる箇所はギリシア語で確かめています。ギリシア語とラテン語訳の食い違いは、各ページに「不確か」として書いています
- ビルドの工程はありません。HTML・CSS・最小限の JavaScript をそのまま GitHub Pages で公開しています（地図だけ D3 を CDN から読み込みます）

## tools/ のスクリプト

ページを足したり本文を直したりしたら、この順に実行します。どれも書き出した HTML をそのまま上書きするもので、何度実行しても同じ結果になります。

1. `python tools/update_nav.py` — 巻ページの前後のリンクと、トップページの巻の一覧を書き直す
2. `python tools/make_coverage.py` — 各巻ページの「照合の状況」の表から `coverage.html` を作る
3. `python tools/autolink.py` — 本文の用語の最初の1回を用語集へ、「#NNN」を MDZ のビューアーへリンクする
4. `python tools/head_meta.py` — 全ページに OGP タグとファビコンを入れる

陣形図を直すときは `python tools/make_plates.py`（`assets/plates/` の SVG を書き出す）。

原典の PDF（`source/`）はリポジトリに含めていません。
