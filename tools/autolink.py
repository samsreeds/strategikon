"""本文の中に自動でリンクを張る。

1. 用語集のリンク：各ページの <main> の本文で、用語集にある語の「最初の1回」を
   用語集（glossary.html#id）へのリンクにする
2. 画像番号のリンク：本文の「#NNN」（PDF の画像番号）を、MDZ のビューアーの該当ページへの
   リンクにする。MDZ のスキャン番号は「PDF の画像番号 − 1」

対象外
- 見出し（h1〜h6）、表の見出し（th）、既存のリンク（a）の中、SVG の中、nav、script、style
- 巻ページの「照合の状況」（<h2 id="status"> から次の <h2> まで。coverage.html に写されるため）
- index.html の巻の一覧（<!-- books:start -->〜<!-- books:end -->。update_nav.py が書き直すため）
- glossary.html 自体（用語の説明ページなので、用語集へのリンクは張らない。画像番号のリンクだけ張る）

すでにリンクがある語（本文で先に出てくる用語集へのリンク）は「済み」とみなし、二重に張らない。
何度実行しても結果は変わらない。

順番：python tools/update_nav.py → python tools/make_coverage.py → python tools/autolink.py

使い方：python tools/autolink.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MDZ = "https://www.digitale-sammlungen.de/en/view/bsb11088428?page={}"

# 用語集の id → 本文で探す語（長い語が優先される）
TERMS = {
    "strategos": ["ストラテゴス"],
    "hypostrategos": ["ヒュポストラテゴス"],
    "merarches": ["メラルケス"],
    "moirarches": ["モイラルケス"],
    "komes": ["コメス", "トリブヌス"],
    "ilarches": ["イラルケス", "ヘカトンタルコス"],
    "meros": ["メロス"],
    "moira": ["モイラ"],
    "tagma": ["タグマ"],
    "droungos": ["ドルンゴス"],
    "boethos": ["第一線", "第二線"],
    "akia": ["アキア"],
    "lochagos": ["ロカゴス"],
    "dekarchos": ["デカルコス"],
    "ouragos": ["ウーラゴス"],
    "kursores": ["クルソレス", "デフェンソレス"],
    "skoutatoi": ["盾兵"],
    "psiloi": ["軽装兵"],
    "plagiophylakes": ["側面防護兵"],
    "hyperkerastai": ["包囲兵"],
    "foideratoi": ["フォイデラトイ"],
    "boukellarioi": ["ブーケラリオイ"],
    "optimatoi": ["オプティマトイ"],
    "epikampios": ["後ろへ曲がった戦列", "曲がった背後の戦列"],
    "diphalangia": ["二重密集隊"],
    "phoulkon": ["フールコン"],
    "formation-types": ["アラン式", "アフリカ式", "イタリア式", "イッリュリア式"],
    "mandator": ["マンダトール"],
    "kampiductor": ["カンピドゥクトール"],
    "touldos": ["輜重"],
    "depotatoi": ["デポタトイ"],
    "skoulkatores": ["偵察兵"],
    "minsores": ["測量兵", "先遣兵"],
    "bandophoros": ["バンドフォロス"],
    "kantator": ["カンタトール"],
    "pallikes": ["従者"],
    "skala": ["鐙"],
    "martzobarboulon": ["マルツォバルブロン"],
    "solenarion": ["ソーレーナリオン"],
    "tribolos": ["鉄菱"],
    "dromon": ["ドロモン"],
    "zaba": ["鎧"],
    "adestrata": ["荷駄"],
    "sagittobolon": ["矢の届く距離"],
    "mile": ["マイル"],
    "litra": ["リトラ"],
    "nomisma": ["ノミスマ"],
    "chagan": ["カガン"],
    "nobiscum": ["ノビスクム"],
}
# 用語の一部に見えても、別の語として扱うもの（リンクしないが、短い語に食われないよう先に取る）
BLOCKERS = ["ストラテギコン", "スキタイ式"]

FORMS = sorted(((f, i) for i, fs in TERMS.items() for f in fs), key=lambda x: -len(x[0]))
FORMS += [(b, None) for b in BLOCKERS]
FORMS.sort(key=lambda x: -len(x[0]))
FORM_ID = dict(FORMS)
TERM_RE = re.compile("|".join(re.escape(f) for f, _ in FORMS))
IMG_RE = re.compile(r"(?<![&\w#])#(\d{1,3})(?!\d)")

TOKEN = re.compile(r"<!--.*?-->|<(script|style)\b.*?</\1\s*>|<[^>]+>", re.S)
SKIP = {"h1", "h2", "h3", "h4", "h5", "h6", "th", "a", "svg", "nav", "title"}
VOID = {"br", "img", "meta", "link", "input", "hr", "source", "wbr", "col"}
GLOSS_HREF = re.compile(r'href="(?:\.\./)?glossary\.html#([^"]+)"')


def excluded_ranges(s):
    r = []
    for m in re.finditer(r'<h2 id="status"', s):
        end = s.find("<h2", m.end())
        r.append((m.start(), end if end != -1 else len(s)))
    a, b = s.find("<!-- books:start -->"), s.find("<!-- books:end -->")
    if a != -1 and b != -1:
        r.append((a, b))
    return r


def process(path, prefix, do_terms):
    s = path.read_text(encoding="utf-8")
    mstart, mend = s.find("<main"), s.find("</main>")
    if mstart == -1:
        return 0, 0
    ranges = excluded_ranges(s)
    done = set()
    out, pos, stack = [], 0, []
    n_terms = n_imgs = 0

    def in_skip():
        return any(t in SKIP for t in stack)

    def text(chunk, at):
        nonlocal n_terms, n_imgs
        if at < mstart or at > mend or in_skip() or any(a <= at < b for a, b in ranges):
            return chunk
        # 画像番号
        def img(m):
            nonlocal n_imgs
            n = int(m.group(1))
            if not 1 <= n <= 675:
                return m.group(0)
            n_imgs += 1
            return f'<a class="img" href="{MDZ.format(n - 1)}">#{n}</a>'
        parts = []
        last = 0
        for m in TERM_RE.finditer(chunk):
            parts.append(IMG_RE.sub(img, chunk[last:m.start()]))
            word, tid = m.group(0), FORM_ID[m.group(0)]
            if do_terms and tid and tid not in done:
                done.add(tid)
                n_terms += 1
                parts.append(f'<a class="term" href="{prefix}glossary.html#{tid}">{word}</a>')
            else:
                parts.append(word)
            last = m.end()
        parts.append(IMG_RE.sub(img, chunk[last:]))
        return "".join(parts)

    for m in TOKEN.finditer(s):
        out.append(text(s[pos:m.start()], pos))
        tag = m.group(0)
        out.append(tag)
        pos = m.end()
        if m.group(1) or tag.startswith("<!--") or tag.startswith("<!"):
            continue
        tm = re.match(r"<(/?)([a-zA-Z0-9]+)", tag)
        if not tm:
            continue
        closing, name = tm.group(1) == "/", tm.group(2).lower()
        if closing:
            if name in stack:
                while stack and stack.pop() != name:
                    pass
        elif name not in VOID and not tag.endswith("/>"):
            stack.append(name)
            # 本文で先に出てくる既存の用語集リンクは「済み」
            if name == "a" and mstart < m.start() < mend:
                g = GLOSS_HREF.search(tag)
                if g and not any(a <= m.start() < b for a, b in ranges):
                    done.add(g.group(1))
    out.append(text(s[pos:], pos))
    new = "".join(out)
    if new != s:
        path.write_text(new, encoding="utf-8", newline="\n")
    return n_terms, n_imgs


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    pages = sorted(ROOT.glob("*.html")) + sorted((ROOT / "books").glob("*.html"))
    for p in pages:
        if p.name.startswith("_"):
            continue
        prefix = "../" if p.parent.name == "books" else ""
        t, i = process(p, prefix, do_terms=(p.name != "glossary.html"))
        print(f"{p.relative_to(ROOT)}: 用語 {t}, 画像番号 {i}")


if __name__ == "__main__":
    main()
