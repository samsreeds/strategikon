"""全ページの <head> に OGP タグとファビコンを入れる（何度実行しても同じ結果）。

- og:title は <title>、og:description は <meta name="description"> から取る
- og:type はトップページだけ website、ほかは article
- og:url は公開先の URL（https://samsreeds.github.io/strategikon/ からの相対パス）
- ファビコンは assets/favicon.svg
- 前回入れたもの（<!-- head-meta:start --> 〜 <!-- head-meta:end -->）は書き直す

順番：update_nav.py → make_coverage.py → autolink.py → head_meta.py

使い方：python tools/head_meta.py
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://samsreeds.github.io/strategikon/"
START, END = "<!-- head-meta:start -->", "<!-- head-meta:end -->"


def block(rel, title, desc, prefix):
    url = BASE if rel == "index.html" else BASE + rel
    typ = "website" if rel == "index.html" else "article"
    a = lambda s: html.escape(html.unescape(s), quote=True)
    return "\n".join([
        START,
        f'<meta property="og:title" content="{a(title)}">',
        f'<meta property="og:description" content="{a(desc)}">',
        f'<meta property="og:type" content="{typ}">',
        f'<meta property="og:url" content="{url}">',
        '<meta property="og:site_name" content="ストラテギコン図解">',
        '<meta property="og:locale" content="ja_JP">',
        f'<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">',
        END,
    ])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pages = sorted(ROOT.glob("*.html")) + sorted((ROOT / "books").glob("*.html"))
    for p in pages:
        if p.name.startswith("_"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        prefix = "../" if p.parent.name == "books" else ""
        s = p.read_text(encoding="utf-8")
        s = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
        title = re.search(r"<title>(.*?)</title>", s, re.S).group(1).strip()
        m = re.search(r'<meta name="description" content="([^"]*)"[^>]*>', s)
        desc = m.group(1) if m else title
        b = block(rel, title, desc, prefix)
        anchor = m.group(0) if m else re.search(r"<title>.*?</title>", s, re.S).group(0)
        i = s.index(anchor) + len(anchor)
        s = s[:i] + "\n" + b + s[i:]
        p.write_text(s, encoding="utf-8", newline="\n")
        print(rel)


if __name__ == "__main__":
    main()
