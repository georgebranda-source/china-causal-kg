"""Build report.html (inline SVG, no external deps) from ./out/. Run after temporal.py."""
from pathlib import Path
from html import escape
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "out"
V = "event-035"
summ = pd.read_csv(OUT / "bucket_summary.csv")
ci = pd.read_csv(OUT / "top_nodes_share_ci.csv")
deg = pd.read_csv(OUT / "top_nodes_degree.csv")
lag = pd.read_csv(OUT / "similarity_by_lag.csv")
xv = pd.read_csv(OUT / "cross_version_nodes.csv")
mat = pd.read_csv(OUT / f"similarity_matrix_{V}_month.csv", index_col=0)
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def mlabel(b):  # '1925-06' -> 'Jun 25'
    y, m = b.split("-")[:2]
    return f"{MON[int(m) - 1]} {y[2:]}"


def frame(w, h, body, ylab=""):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" preserveAspectRatio="xMinYMin meet">'
            f'{body}</svg>')


def axis_x(xs, labels, y, every=1, rotate=False):
    s = ""
    for i, (x, l) in enumerate(zip(xs, labels)):
        if i % every:
            continue
        s += f'<text class="tick" x="{x:.1f}" y="{y + 14}" text-anchor="middle">{escape(l)}</text>'
    return s


def gridy(x0, x1, y_of, vals, fmt):
    s = ""
    for v in vals:
        y = y_of(v)
        s += f'<line class="grid" x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}"/>'
        s += f'<text class="tick" x="{x0 - 6}" y="{y + 4:.1f}" text-anchor="end">{fmt(v)}</text>'
    return s


# ---- chart 1: coverage (claims, pages) as two small bar charts
def bars(df, col, title, w=640, h=170):
    x0, x1, y0, y1 = 44, w - 8, 18, h - 26
    mx = df[col].max() * 1.08
    n = len(df)
    bw = (x1 - x0) / n
    yo = lambda v: y1 - (y1 - y0) * v / mx
    s = gridy(x0, x1, yo, [0, round(mx / 2, -1)], lambda v: f"{v:.0f}")
    for i, r in enumerate(df.itertuples()):
        v = getattr(r, col)
        x = x0 + i * bw + 1
        s += (f'<rect class="bar" x="{x:.1f}" y="{yo(v):.1f}" width="{bw - 2:.1f}" height="{y1 - yo(v):.1f}" rx="2">'
              f'<title>{mlabel(r.bucket)}: {v} {col}</title></rect>')
    s += axis_x([x0 + (i + .5) * bw for i in range(n)], [mlabel(b) for b in df.bucket], y1, every=2)
    return f'<figure><figcaption>{title}</figcaption>{frame(w, h, s)}</figure>'


cov = summ[(summ.version == V) & (summ.scheme == "month")]


# ---- chart 2: small multiples, monthly share_any with bootstrap CI band
def multiple(node, w=300, h=150):
    d = ci[(ci.version == V) & (ci.scheme == "month") & (ci.node == node)].sort_values("bucket")
    x0, x1, y0, y1 = 32, w - 6, 8, h - 24
    mx = max(0.06, d.ci_hi.max() * 1.05)
    n = len(d)
    xo = lambda i: x0 + (x1 - x0) * i / (n - 1)
    yo = lambda v: y1 - (y1 - y0) * v / mx
    top = [f"{xo(i):.1f},{yo(v):.1f}" for i, v in enumerate(d.ci_hi)]
    bot = [f"{xo(i):.1f},{yo(v):.1f}" for i, v in enumerate(d.ci_lo)][::-1]
    s = gridy(x0, x1, yo, [0, round(mx / 2, 2)], lambda v: f"{v * 100:.0f}%")
    s += f'<polygon class="band" points="{" ".join(top + bot)}"/>'
    s += f'<polyline class="line" points="{" ".join(f"{xo(i):.1f},{yo(v):.1f}" for i, v in enumerate(d.share_any))}"/>'
    for i, r in enumerate(d.itertuples()):
        s += (f'<circle class="hit" cx="{xo(i):.1f}" cy="{yo(r.share_any):.1f}" r="7"><title>{mlabel(r.bucket)}: '
              f'{r.share_any * 100:.1f}% of claims (95% CI {r.ci_lo * 100:.1f}-{r.ci_hi * 100:.1f})</title></circle>')
    s += axis_x([xo(0), xo(n - 1)], [mlabel(d.bucket.iloc[0]), mlabel(d.bucket.iloc[-1])], y1)
    lab = d.label.iloc[0]
    return f'<figure class="sm"><figcaption>{escape(lab)}</figcaption>{frame(w, h, s)}</figure>'


tops = ci[(ci.version == V) & (ci.scheme == "month")].drop_duplicates("node").sort_values("rank")
smalls = "".join(multiple(n) for n in tops.node[:12])


# ---- chart 3: strike node as cause vs effect per bimonth (grouped bars)
def role_chart(node, w=640, h=200):
    d = deg[(deg.version == V) & (deg.scheme == "bimonth") & (deg.node == node)].sort_values("bucket")
    x0, x1, y0, y1 = 36, w - 8, 14, h - 26
    mx = max(d.out_claims.max(), d.in_claims.max()) * 1.1
    n = len(d)
    gw = (x1 - x0) / n
    bw = (gw - 8) / 2
    yo = lambda v: y1 - (y1 - y0) * v / mx
    s = gridy(x0, x1, yo, [0, 10, 20, 30, 40], lambda v: f"{v:.0f}")
    lbl = []
    for i, r in enumerate(d.itertuples()):
        gx = x0 + i * gw + 4
        b = r.bucket[:7]
        lab = f"{mlabel(b)[:3]}-{MON[int(b[5:7]) % 12][:3]} {b[2:4]}"
        lbl.append(lab)
        for k, (v, cls, nm) in enumerate([(r.out_claims, "s1", "as cause"), (r.in_claims, "s2", "as effect")]):
            s += (f'<rect class="{cls}" x="{gx + k * (bw + 2):.1f}" y="{yo(v):.1f}" width="{bw:.1f}" '
                  f'height="{y1 - yo(v):.1f}" rx="2"><title>{lab}: {v} claims {nm}</title></rect>')
    s += axis_x([x0 + (i + .5) * gw for i in range(n)], lbl, y1)
    return frame(w, h, s)


# ---- chart 4: heatmap of size-matched Jaccard
def heat(w=640):
    n = len(mat)
    x0, y0 = 52, 8
    c = (w - x0 - 8) / n
    lo, hi = 0.015, 0.067
    s = ""
    for i, b1 in enumerate(mat.index):
        for j, b2 in enumerate(mat.columns):
            if i == j:
                continue
            v = mat.iloc[i, j]
            t = max(0, min(1, (v - lo) / (hi - lo)))
            s += (f'<rect x="{x0 + j * c:.1f}" y="{y0 + i * c:.1f}" width="{c - 1:.1f}" height="{c - 1:.1f}" '
                  f'class="cell" style="opacity:{0.08 + 0.92 * t:.2f}"><title>{mlabel(b1)} vs {mlabel(b2)}: '
                  f'{v:.3f}</title></rect>')
        if i % 2 == 0:
            s += f'<text class="tick" x="{x0 - 4}" y="{y0 + i * c + c * .7:.1f}" text-anchor="end">{mlabel(b1)}</text>'
            s += (f'<text class="tick" x="{x0 + i * c + c / 2:.1f}" y="{y0 + n * c + 12:.1f}" '
                  f'text-anchor="middle">{mlabel(b1)[:3]}</text>')
    return frame(w, y0 + n * c + 20, s)


# ---- chart 5: similarity by lag, four versions
def lag_chart(w=640, h=220):
    d = lag[lag.scheme == "month"]
    x0, x1, y0, y1 = 40, w - 90, 10, h - 26
    mx = 0.08
    xo = lambda k: x0 + (x1 - x0) * (k - 1) / 18
    yo = lambda v: y1 - (y1 - y0) * v / mx
    s = gridy(x0, x1, yo, [0, 0.02, 0.04, 0.06, 0.08], lambda v: f"{v:.2f}")
    for k, v in enumerate(["event-035", "event-030", "topic-030", "topic-035"]):
        dv = d[d.version == v].sort_values("lag")
        pts = " ".join(f"{xo(r.lag):.1f},{yo(r.mean):.1f}" for r in dv.itertuples())
        s += f'<polyline class="l s{k + 1}l" points="{pts}"/>'
        for r in dv.itertuples():
            s += (f'<circle class="hit" cx="{xo(r.lag):.1f}" cy="{yo(r.mean):.1f}" r="6"><title>{v}, {r.lag} months '
                  f'apart: {r.mean:.3f} ({r.pairs} pairs)</title></circle>')
        last = dv.iloc[-4]
        s += f'<text class="dl" x="{x1 + 6}" y="{yo(dv["mean"].iloc[:16].mean()) + 4:.1f}">{v}</text>'
    s += axis_x([xo(k) for k in range(1, 20)], [str(k) for k in range(1, 20)], y1, every=2)
    return frame(w, h, s)


cov_tbl = cov[["bucket", "claims", "articles", "pages", "nodes", "self_loop_claims"]]
xv_tbl = (xv[xv["rank"] <= 12].pivot_table(index=["rank", "base_label"], columns="other_version",
                                           values="spearman_monthly_share").round(2).reset_index())


def table(df):
    h = "".join(f"<th>{escape(str(c))}</th>" for c in df.columns)
    rows = "".join("<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in r) + "</tr>" for r in df.itertuples(index=False))
    return f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{rows}</tbody></table></div>'


html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Monthly causal graph</title>
<style>
:root{{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e4e3df;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#353532;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;}}}}
:root[data-theme="dark"]{{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#353532;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;}}
body{{background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,sans-serif;margin:0;padding:24px 16px;}}
main{{max-width:880px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}} h2{{font-size:18px;margin:32px 0 6px}}
p,li{{color:var(--ink)}} .muted{{color:var(--ink2);font-size:13px}}
figure{{margin:8px 0}} figcaption{{font-size:13px;color:var(--ink2);margin-bottom:2px}}
.grid{{stroke:var(--grid);stroke-width:1}} .tick{{fill:var(--ink2);font-size:10px}} .dl{{fill:var(--ink);font-size:11px}}
.bar,.s1,.cell{{fill:var(--s1)}} .s2{{fill:var(--s2)}} .band{{fill:var(--s1);opacity:.15}}
.line{{fill:none;stroke:var(--s1);stroke-width:2}} .l{{fill:none;stroke-width:2}}
.s1l{{stroke:var(--s1)}} .s2l{{stroke:var(--s2)}} .s3l{{stroke:var(--s3)}} .s4l{{stroke:var(--s4)}}
.hit{{fill:transparent}} .hit:hover{{fill:var(--ink);fill-opacity:.25}} rect:hover{{opacity:.75}}
.grid3{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:4px 16px}}
.legend{{font-size:13px;color:var(--ink2)}} .sw{{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 12px}}
.tw{{overflow-x:auto}} table{{border-collapse:collapse;font-size:12px}} td,th{{padding:3px 8px;border-bottom:1px solid var(--grid);text-align:left}}
</style></head><body><main>
<h1>Causal graph by month</h1>
<p class="muted">Snapshot <code>snapshot_v1_ceb6e08a</code> (3,479 claims, Apr 1925 to Nov 1926). Working version {V}; all four versions in <code>out/</code>. Hover over marks for values.</p>

<h2>Summary</h2>
<ul>
<li><b>Coverage drives raw counts.</b> Pages per month range from 16 to 75, so everything below uses shares of the month's claims.</li>
<li><b>Themes that clearly move</b> (95% intervals don't overlap): "Recent disturbances occur in Shanghai" is 8% of claims in Q2 1925 (11% in June) and 1% or less in each later quarter. China Mail delivery appears only from June to September 1925. "A strike is taken" falls from 8% (Q3 1925) to 2% (Q3 1926). <b>Suggestive only:</b> the boycott is about 1% in every 1925 quarter and 1-3% in 1926, reaching 6% in Nov 1926; its intervals overlap.</li>
<li><b>Caution, May 1926:</b> the strike spike (12%) mixes in the British General Strike (London printers, coal). The event node does not keep strikes in different places apart.</li>
<li><b>Strike as cause or effect:</b> it is mostly a cause in every period (about 3-5 claims as cause for each claim as effect). As an effect it peaks in Jun-Jul 1925 and Jun-Jul 1926. It never shifts from effect to cause.</li>
<li><b>Similarity between months is low throughout</b> (size-matched Jaccard 0.03-0.07). Adjacent months are only slightly more alike than distant ones (0.049 vs about 0.041 at 2-16 months apart), so there is no gradual drift. A small core of hub nodes recurs; the rest are one-off incidents. The low point in all four versions is Nov to Dec 1925, and December 1925 is unlike every other month. The fall at 17-19 months apart only reflects pairs involving Apr-May 1925. Exact edges almost never repeat (Jaccard 0-0.02).</li>
<li><b>Robust to clustering:</b> monthly share series of the top 12 nodes correlate 0.63-0.97 (Spearman) across the four versions. Monthly similarity series agree 0.78-0.95. Two-month series agree 0.55-0.85. Quarterly similarity barely varies (0.135-0.151), so it cannot tell periods apart.</li>
</ul>
<h2>1. Coverage varies a lot from month to month</h2>
<p>Use shares, not raw counts. Nov 1925 to Apr 1926 and Apr to May 1925 rest on 16 to 47 pages, against 52 to 75 in the strike peaks.</p>
{bars(cov, "claims", "Claims per month")}
{bars(cov, "pages", "Pages per month")}

<h2>2. Theme shares: top 12 nodes, share of the month's claims</h2>
<p>Line = share of claims with the node as cause or effect; band = 95% interval from resampling articles within the month. Most monthly differences fall inside these bands; the ones that don't are named in the summary.</p>
<div class="grid3">{smalls}</div>

<h2>3. "A strike is taken": cause or effect?</h2>
<p class="legend"><span class="sw" style="background:var(--s1)"></span>as cause<span class="sw" style="background:var(--s2)"></span>as effect (claims, two-month buckets, self-loops excluded)</p>
{role_chart("n0")}

<h2>4. Similarity between months</h2>
<p>Size-matched Jaccard: each month subsampled to 42 claims (the smallest month), 200 draws. Darker = more nodes in common (palest ≤ 0.015, darkest ≥ 0.067).</p>
{heat()}
<p>Mean similarity by distance in months, all four versions:</p>
{lag_chart()}

<h2>5. Do the trends depend on the clustering?</h2>
<p>Each top {V} node matched to the node holding most of its claims in the other version; Spearman correlation of the two monthly share series.</p>
{table(xv_tbl)}

<h2>Coverage table ({V}, monthly)</h2>
{table(cov_tbl)}
</main></body></html>"""
(HERE / "report.html").write_text(html, encoding="utf-8")
print("wrote", HERE / "report.html")
