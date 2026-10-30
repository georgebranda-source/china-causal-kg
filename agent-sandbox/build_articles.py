"""Rebuild readable, article-ordered markdown from PaddleOCR-VL layout blocks.

PaddleOCR-VL's own .md follows the model's reading order, which on busy newspaper pages jumps
between columns and splices unrelated paragraphs together. This script ignores that order and
uses the block geometry in ocr_vl_out/<page>_res.json instead:

1. Find the page's text columns by clustering the x-centres of ordinary-width text blocks.
2. Classify title blocks: CAPS titles are headlines (start an article), "(Reuter's Service.)"-style
   lines are sources, "Canton, June 15."-style lines are datelines, other mixed-case titles are
   subheads. Short CAPS text right under a headline is a deck.
3. Read columns left to right, top to bottom. A headline starts an article; the blocks below it
   belong to it until the next headline. Text at the top of a column with no headline above it
   continues the article that was running in the previous column (at the same height, if a
   multi-column block splits the column).
4. Articles that look like adverts or page furniture go to a collapsed section at the end.

Usage (from the repo root):
    agent-sandbox/.venv-kg/Scripts/python agent-sandbox/build_articles.py            # the 40 strike pages
    agent-sandbox/.venv-kg/Scripts/python agent-sandbox/build_articles.py page_001_NPCM19250610_01_0001

Writes to agent-sandbox/articles_md/:
    <page>.md            article-ordered markdown
    <page>_articles.png  page image with each article's blocks outlined in its own colour
    articles.jsonl       one line per article (page, date, headline, block ids, text, is_ad)
"""

import json
import re
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SANDBOX = Path(__file__).resolve().parent
REPO = SANDBOX.parent
VL_DIR = SANDBOX / "ocr_vl_out"
OUT_DIR = SANDBOX / "articles_md"

SKIP_LABELS = {"header_image", "header", "footer", "number"}
# Vertical gap (px at full scan resolution) between blocks in a column that starts a new article.
# Within an article, text blocks are 3 px apart at the median and under 63 px for 90% of pairs; a bigger
# gap is usually a headline the layout model did not detect.
GAP_PX = 90
TITLE_LABELS = {"paragraph_title", "doc_title"}

SOURCE_RE = re.compile(r"^\(.*(service|correspondent|courtesy|reuter|router|from our|by wire).*\)\.?$", re.I)
DATELINE_RE = re.compile(r"^[A-Z][A-Za-z'.\- ]{2,30},\s*(June|July|Jue|J[uü]ly|Jun|Jul|Tura)[a-z]*\.?\s*\d{0,2}", re.I)
# bottom line of the front-page masthead: issue number, price, date line
MASTHEAD_RE = re.compile(r"^(No\.\s*[\d,]{4,}|P?R?ICE,?\s*\$|HONGKONG,\s*\w+DAY)", re.I)
AD_WORDS = re.compile(
    r"telephone|tel\.|\bltd\b|sole agents|solo agents|catalogues|per bottle|per month|\$\d|cts\b|"
    r"barometer|humidity|closing rate|opening rate|wholesale|prices|stock of|obtainable|specialists|"
    r"agents?:|on application|\bsale\b|cash.{0,3}basis|annual subscription",
    re.I,
)


def caps_ratio(s):
    letters = [c for c in s if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0.0


def one_line(s):
    return re.sub(r"\s+", " ", s).strip()


class Block:
    def __init__(self, raw):
        self.id = raw["block_id"]
        self.label = raw["block_label"]
        self.text = raw["block_content"].strip()
        self.x1, self.y1, self.x2, self.y2 = raw["block_bbox"]
        self.cols = []
        self.kind = self._kind()

    @property
    def w(self):
        return self.x2 - self.x1

    def _kind(self):
        t = one_line(self.text)
        if self.label == "image":
            return "image"
        if self.label == "vision_footnote" or re.match(r"^photo\b", t, re.I):
            return "caption"
        if SOURCE_RE.match(t):
            return "source"
        if len(t) < 40 and DATELINE_RE.match(t):
            return "dateline"
        if self.label in TITLE_LABELS:
            return "headline" if caps_ratio(t) >= 0.75 and sum(c.isalpha() for c in t) >= 4 else "subhead"
        if len(t) < 60 and caps_ratio(t) >= 0.8 and sum(c.isalpha() for c in t) >= 4:
            return "capsline"  # headline or deck the layout model labelled as text; decided in build_articles
        return "text"


class Article:
    def __init__(self, n, col):
        self.n = n
        self.col = col
        self.headline = []  # stacked headline lines, first is the main one
        self.items = []  # (kind, Block)
        self.blocks = []
        self.before = None  # article that was running in the column when this headline appeared
        self.picture = False  # headline sits directly above a picture
        self.parent = None  # for a section started by a subhead: the headlined article it sits under

    @property
    def has_body(self):
        return any(k == "text" for k, _ in self.items)

    @property
    def fresh(self):
        """Has a headline but no body text yet."""
        return bool(self.headline) and not self.has_body

    def add(self, kind, b):
        self.items.append((kind, b))
        self.blocks.append(b)

    def plain_text(self):
        return "\n\n".join(one_line(b.text) for k, b in self.items if k in ("text", "caption", "deck"))

    def is_ad(self):
        if any(k == "caption" for k, _ in self.items):
            return False
        texts = [one_line(b.text) for k, b in self.items if k in ("text", "subhead", "deck")]
        body = " ".join(texts + [one_line(b.text) for b in self.headline])
        # prose = a long block that is mostly lower case; ad copy is short, capitalised, or full of trade words
        prose = any(len(t.split()) >= 25 and caps_ratio(t) < 0.35 for t in texts)
        hits = len(AD_WORDS.findall(body))
        return not prose or hits * 100 / max(len(body.split()), 1) >= 4


def find_columns(blocks):
    """Cluster the left edges of ordinary-width text blocks into columns -> list of (x1, x2).

    Left edges sit on the page's column grid; the odd block that starts mid-column forms a small
    cluster overlapping a real column and is dropped (best-supported clusters win)."""
    text = [b for b in blocks if b.kind == "text" and len(b.text) > 60]
    med_w = statistics.median(b.w for b in text)
    narrow = sorted((b for b in text if 0.6 * med_w < b.w < 1.4 * med_w), key=lambda b: b.x1)
    groups, cur = [], [narrow[0]]
    for b in narrow[1:]:
        if b.x1 - cur[-1].x1 > 0.25 * med_w:
            groups.append(cur)
            cur = [b]
        else:
            cur.append(b)
    groups.append(cur)
    cands = sorted(((statistics.median(b.x1 for b in g), statistics.median(b.x2 for b in g), len(g)) for g in groups),
                   key=lambda c: -c[2])
    cols = []
    for x1, x2, _ in cands:
        if all(min(x2, a2) - max(x1, a1) < 0.5 * (x2 - x1) for a1, a2 in cols):
            cols.append((x1, x2))
    return sorted(cols)


def assign_columns(blocks, cols):
    for b in blocks:
        for i, (cx1, cx2) in enumerate(cols):
            overlap = min(b.x2, cx2) - max(b.x1, cx1)
            if overlap > 0.4 * min(b.w, cx2 - cx1):
                b.cols.append(i)
        if not b.cols:  # sits in a gutter: nearest column by centre
            c = (b.x1 + b.x2) / 2
            b.cols.append(min(range(len(cols)), key=lambda i: abs((cols[i][0] + cols[i][1]) / 2 - c)))


def ends_mid_sentence(t):
    return not re.search(r"[.!?:;—\-]['\"”’)\]]*$", one_line(t))


def starts_mid_sentence(t):
    return bool(re.match(r"^[\"'“‘(]*[a-z]", one_line(t)))


def repair_continuations(articles):
    """Move stray continuations back to the article they continue.

    An article that runs off the bottom of a column often resumes part-way down a later column, under
    another article; column reading then glues the continuation onto that other article. The text gives
    it away: a block that starts mid-sentence right after a finished sentence (or opens a headline-less
    unit). It and everything after it in that unit move to the nearest article to its left whose text
    stops mid-sentence."""
    for _ in range(50):
        moved = False
        for a in list(articles):
            texts = [i for i, (k, _) in enumerate(a.items) if k == "text"]
            for j, i in enumerate(texts):
                b = a.items[i][1]
                if not starts_mid_sentence(b.text):
                    continue
                if j > 0 and ends_mid_sentence(a.items[texts[j - 1]][1].text):
                    continue  # ordinary continuation inside a
                if j == 0 and a.headline:
                    continue  # body right under a headline: leave it
                targets = []
                for t in articles:
                    t_text = [x for k, x in t.items if k == "text"]
                    if t is a or not t_text or not ends_mid_sentence(t_text[-1].text):
                        continue
                    last = t_text[-1]
                    if max(last.cols) < min(b.cols):  # continuation reads on to the right
                        targets.append((max(last.cols), last.y2, t))
                if not targets:
                    continue
                t = max(targets, key=lambda x: (x[0], x[1]))[2]
                tail = a.items[i:]
                a.items = a.items[:i]
                t.items += tail
                for k, x in tail:
                    a.blocks.remove(x)
                    t.blocks.append(x)
                if not a.items and not a.headline:
                    articles.remove(a)
                moved = True
                break
            if moved:
                break
        if not moved:
            return


def build_articles(blocks, ncols):
    seq = [sorted((b for b in blocks if k in b.cols), key=lambda b: (b.y1, b.x1)) for k in range(ncols)]
    art_of, articles = {}, []

    def new_article(col):
        a = Article(len(articles) + 1, col)
        articles.append(a)
        return a

    def predecessor(k, b):
        """Article running at the bottom of column k-1 (above the next block spanning k-1 and k),
        if b reads as its continuation: the article's last text ends mid-sentence or b starts lowercase."""
        if k == 0 or b.kind != "text":
            return None
        bound = min((x.y1 for x in seq[k] if x.y1 > b.y1 and k - 1 in x.cols), default=float("inf"))
        cands = [x for x in seq[k - 1] if x.y1 < bound and k not in x.cols and x.id in art_of]
        if not cands:
            return None
        prev = art_of[cands[-1].id]
        last = next((one_line(x.text) for kind, x in reversed(prev.items) if kind == "text"), "")
        first = one_line(b.text).lstrip("\"'“‘(")
        ends_sentence = bool(re.search(r"[.!?:]['\"”’)]*$", last))
        starts_sentence = bool(first) and (first[0].isupper() or first[0].isdigit())
        return None if ends_sentence and starts_sentence else prev

    def start_headline(k, b, current):
        if current is not None and current.headline and not current.items and not current.parent:  # stacked lines
            current.headline.append(b)
        else:
            new = new_article(k)
            new.headline.append(b)
            new.before = current
            current = new
        current.blocks.append(b)
        return current

    last_picture = None
    for k in range(ncols):
        current, prev = None, None
        for b in seq[k]:
            gap = prev is not None and b.y1 - prev.y2 > GAP_PX
            prev = b
            fresh = current is not None and current.fresh
            if b.id in art_of:  # multi-column block, already placed from an earlier column
                if b.kind != "caption" and not art_of[b.id].picture:
                    current = art_of[b.id]
                continue
            if b.kind == "image":
                # a headline straight above a picture belongs to the picture: resume the article it interrupted
                if fresh and not current.picture:
                    current.picture = True
                    last_picture = current
                    current = current.before
                continue
            if b.kind == "caption":  # goes with its picture headline, or stands alone; never changes the running article
                above = last_picture is not None and not any(kd == "caption" for kd, _ in last_picture.items) and any(
                    min(b.x2, h.x2) - max(b.x1, h.x1) > 0 for h in last_picture.headline)
                cap = last_picture if above else new_article(k)
                cap.add("caption", b)
                art_of[b.id] = cap
                continue
            if b.kind == "headline":
                current = start_headline(k, b, current)
            elif b.kind == "subhead" and not fresh:
                # a subhead starts a section: own text, but keeps the headline above it as context.
                # The China Mail runs separate items under mixed-case subheads, so text never flows across one.
                sec = new_article(k)
                sec.headline.append(b)
                sec.blocks.append(b)
                sec.parent = (current.parent or current) if current is not None and (current.parent or current).headline else None
                sec.before = current
                current = sec
            elif b.kind == "capsline" and not fresh:
                current = start_headline(k, b, None if gap else current)
            else:
                if current is None:
                    current = predecessor(k, b) or new_article(k)
                elif gap and not fresh:  # big empty band: probably a headline the layout model missed
                    current = new_article(k)
                current.add("deck" if b.kind == "capsline" else b.kind, b)
            art_of[b.id] = current

    repair_continuations(articles)

    # a caption read before its picture headline (headline in a later column): join them up
    for cap in [a for a in articles if not a.headline and [k for k, _ in a.items] == ["caption"]]:
        c = cap.items[0][1]
        heads = [a for a in articles if a.headline and not a.has_body and a is not cap
                 and all(k != "caption" for k, _ in a.items)
                 and a.headline[0].y2 < c.y1 and min(c.x2, a.headline[0].x2) - max(c.x1, a.headline[0].x1) > 0]
        if heads:
            pic = max(heads, key=lambda a: a.headline[0].y2)
            pic.add("caption", c)
            articles.remove(cap)
    return articles


def render_md(page, date, articles):
    news = [a for a in articles if not a.is_ad()]
    ads = [a for a in articles if a.is_ad()]
    out = [
        f"# China Mail, {date}, page {int(page.split('_')[1])}",
        "",
        f"> Rebuilt from PaddleOCR-VL layout blocks by column position (`build_articles.py`). "
        f"{len(news)} articles, {len(ads)} advert/furniture groups. Article numbers match `{page}_articles.png`.",
        "",
    ]

    def body(a, ad=False):
        lines = []
        if a.headline:
            lines.append(f"{'###' if ad else '##'} [{a.n}] {one_line(a.headline[0].text)}")
            lines += [f"**{one_line(h.text)}**" for h in a.headline[1:]]
            if a.parent is not None:
                lines.append(f"<sub>section under [{a.parent.n}] {one_line(a.parent.headline[0].text)}</sub>")
        else:
            lines.append(f"{'###' if ad else '##'} [{a.n}] *(no headline: column {a.col + 1})*")
        for kind, b in a.items:
            t = one_line(b.text) if kind != "text" else b.text.strip()
            lines.append({
                "deck": f"**{t}**",
                "subhead": f"{'####' if ad else '###'} {t}",
                "source": f"*{t}*",
                "dateline": f"*{t}*",
                "caption": f"> *Picture caption:* {t}",
            }.get(kind, t))
        return "\n\n".join(lines)

    for a in news:
        out += [body(a), ""]
    if ads:
        out += ["---", "", "<details><summary>Adverts and page furniture</summary>", ""]
        out += [body(a, ad=True) + "\n" for a in ads]
        out += ["</details>", ""]
    return "\n".join(out)


def render_overlay(img_path, articles, dest, scale=0.4):
    img = Image.open(img_path).convert("RGB")
    img = img.resize((int(img.width * scale), int(img.height * scale)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    try:
        font = ImageFont.truetype("arialbd.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    palette = [(230, 25, 75), (60, 180, 75), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 190, 190),
               (240, 50, 230), (128, 128, 0), (0, 0, 128), (170, 110, 40), (128, 0, 0), (0, 128, 128)]
    for a in articles:
        ad = a.is_ad()
        col = (150, 150, 150) if ad else palette[a.n % len(palette)]
        for b in a.blocks:
            box = [int(v * scale) for v in (b.x1, b.y1, b.x2, b.y2)]
            d.rectangle(box, fill=col + (40 if not ad else 25,), outline=col + (255,), width=3 if not ad else 1)
        if not ad:
            first = a.blocks[0]
            x, y = int(first.x1 * scale), int(first.y1 * scale)
            label = str(a.n)
            tw = d.textlength(label, font=font)
            d.rectangle([x, y, x + tw + 10, y + 28], fill=col + (255,))
            d.text((x + 5, y + 2), label, fill=(255, 255, 255, 255), font=font)
    Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB").save(dest, quality=82)


def process(page):
    res = json.loads((VL_DIR / f"{page}_res.json").read_text(encoding="utf-8"))
    blocks = [Block(b) for b in res["parsing_res_list"]
              if b["block_label"] not in SKIP_LABELS and (b["block_label"] == "image" or b["block_content"].strip())]
    # front page: everything above the masthead's bottom line is page furniture
    masthead_y = max((b.y2 for b in blocks if b.y1 < 700 and MASTHEAD_RE.match(one_line(b.text))), default=0)
    furniture = [b for b in blocks if b.y2 <= masthead_y + 10]
    blocks = [b for b in blocks if b.y2 > masthead_y + 10]

    cols = find_columns(blocks)
    assign_columns(blocks, cols)
    articles = build_articles(blocks, len(cols))
    if furniture:
        mast = Article(0, 0)
        for b in sorted(furniture, key=lambda b: (b.y1, b.x1)):
            if b.kind != "image":
                mast.add("text", b)
        mast.headline = []
        mast.is_ad = lambda: True
        articles.insert(0, mast)

    m = re.search(r"NPCM(\d{4})(\d{2})(\d{2})", page)
    date = f"{m[1]}-{m[2]}-{m[3]}"
    (OUT_DIR / f"{page}.md").write_text(render_md(page, date, articles), encoding="utf-8")
    render_overlay(REPO / res["input_path"], articles, OUT_DIR / f"{page}_articles.png")

    rows = [{
        "page": page, "date": date, "article": a.n, "is_ad": a.is_ad(),
        "headline": " / ".join(one_line(h.text) for h in a.headline) or None,
        "parent": a.parent.n if a.parent is not None else None,
        "parent_headline": " / ".join(one_line(h.text) for h in a.parent.headline) if a.parent is not None else None,
        "blocks": [b.id for b in a.blocks], "columns": sorted({c for b in a.blocks for c in b.cols}),
        "text": a.plain_text(),
    } for a in articles]
    news = sum(not r["is_ad"] for r in rows)
    print(f"{page}: {len(cols)} columns, {len(blocks)} blocks -> {news} articles + {len(rows) - news} ad/furniture")
    return rows


def main():
    OUT_DIR.mkdir(exist_ok=True)
    pages = sys.argv[1:] or sorted(p.stem for p in (SANDBOX / "strike_pages_md").glob("page_*.md"))
    rows = [r for p in pages for r in process(p)]
    if not sys.argv[1:]:
        with open(OUT_DIR / "articles.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
