"""Temporal bucketing of graph_v1: node shares, degree of top nodes, and
similarity between buckets, for all four clustering versions and three bucket sizes.

Reads a frozen snapshot (see SNAP), never the live kg/out/graph_v1.
Run with the repo-root venv:  ../../../../.venv/Scripts/python.exe temporal.py
Outputs go to ./out/.
"""
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
SNAP = HERE / "snapshot_v1_ceb6e08a"
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
VERSIONS = ["event-035", "event-030", "topic-030", "topic-035"]  # event-035 = working version
SCHEMES = ["month", "bimonth", "quarter"]
TOP_K = 20
N_BOOT = 1000
N_SUB = 200
RNG = np.random.default_rng(1925)


def bucket(dates: pd.Series, scheme: str) -> pd.Series:
    if scheme == "month":
        return dates.dt.strftime("%Y-%m")
    if scheme == "bimonth":
        # pairs aligned with the batch runs: Apr-May 1925, Jun-Jul, ..., Oct-Nov 1926
        idx = (dates.dt.year - 1925) * 12 + dates.dt.month - 4
        start = idx // 2 * 2
        y = 1925 + (start + 3) // 12
        m = (start + 3) % 12 + 1
        return y.astype(str) + "-" + m.map("{:02d}".format) + "+1"
    if scheme == "quarter":
        return dates.dt.to_period("Q").astype(str)
    raise ValueError(scheme)


def load(version: str) -> tuple[pd.DataFrame, pd.Series]:
    d = SNAP / version
    claims = pd.read_csv(d / "claims.csv", usecols=["id", "date"], parse_dates=["date"])
    fa = pd.read_csv(d / "from_article.csv")
    arts = pd.read_csv(d / "articles.csv", usecols=["id", "page"])
    hc = pd.read_csv(d / "has_cause.csv").rename(columns={"event": "cause"})
    he = pd.read_csv(d / "has_effect.csv").rename(columns={"event": "effect"})
    t = (claims.merge(fa, left_on="id", right_on="claim").drop(columns="claim")
         .merge(arts.rename(columns={"id": "article"}), on="article")
         .merge(hc, left_on="id", right_on="claim").drop(columns="claim")
         .merge(he, left_on="id", right_on="claim").drop(columns="claim"))
    assert len(t) == len(claims), (version, len(t), len(claims))
    t["self"] = t.cause == t.effect
    labels = pd.read_csv(d / "events.csv").set_index("id").label
    return t, labels


def node_roles(t: pd.DataFrame) -> pd.DataFrame:
    """One row per (claim, node) with cause/effect flags; a self-loop claim gives one row."""
    c = t[["id", "b", "article", "cause"]].rename(columns={"cause": "node"}).assign(is_cause=1, is_effect=0)
    e = t[["id", "b", "article", "effect"]].rename(columns={"effect": "node"}).assign(is_cause=0, is_effect=1)
    r = pd.concat([c, e]).groupby(["id", "b", "article", "node"], as_index=False)[["is_cause", "is_effect"]].max()
    return r


def jacc(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else np.nan


rows_summary, rows_share, rows_ci, rows_deg, rows_sim, rows_rf, top_lists = [], [], [], [], [], [], {}
tables = {}
for v in VERSIONS:
    t0, labels = load(v)
    tables[v] = (t0, labels)
    total_any = node_roles(t0.assign(b="all")).groupby("node").size().sort_values(ascending=False)
    top = list(total_any.index[:TOP_K])
    top_lists[v] = top
    for s in SCHEMES:
        t = t0.assign(b=bucket(t0.date, s))
        buckets = sorted(t.b.unique())
        r = node_roles(t)
        nclaims = t.groupby("b").size()

        # 1. bucket summary
        for b in buckets:
            tb = t[t.b == b]
            nodes = set(tb.cause) | set(tb.effect)
            edges = set(zip(tb.cause[~tb.self], tb.effect[~tb.self]))
            rows_summary.append(dict(version=v, scheme=s, bucket=b, claims=len(tb), articles=tb.article.nunique(),
                                     pages=tb.page.nunique(), issue_days=tb.date.nunique(), nodes=len(nodes),
                                     edges=len(edges), self_loop_claims=int(tb.self.sum())))

        # 2. node share per bucket (all nodes)
        g = r.groupby(["b", "node"]).agg(any_claims=("id", "size"), cause_claims=("is_cause", "sum"),
                                         effect_claims=("is_effect", "sum")).reset_index()
        g["bucket_claims"] = g.b.map(nclaims)
        for k in ["any", "cause", "effect"]:
            g[f"share_{k}"] = g[f"{k}_claims"] / g.bucket_claims
        g["label"] = g.node.map(labels)
        rows_share.append(g.rename(columns={"b": "bucket"}).assign(version=v, scheme=s))

        # 3. article-cluster bootstrap CI on share_any for top nodes
        for b in buckets:
            tb = t[t.b == b]
            arts = tb.article.unique()
            ai = {a: i for i, a in enumerate(arts)}
            per_art = tb.groupby("article").size().reindex(arts).to_numpy()
            rb = r[(r.b == b) & r.node.isin(top)]
            m = np.zeros((len(arts), len(top)))
            for (a, n), cnt in rb.groupby(["article", "node"]).size().items():
                m[ai[a], top.index(n)] = cnt
            idx = RNG.integers(0, len(arts), size=(N_BOOT, len(arts)))
            boot = m[idx].sum(axis=1) / per_art[idx].sum(axis=1)[:, None]
            lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
            point = m.sum(axis=0) / per_art.sum()
            for j, n in enumerate(top):
                rows_ci.append(dict(version=v, scheme=s, bucket=b, node=n, label=labels[n], rank=j + 1,
                                    share_any=point[j], ci_lo=lo[j], ci_hi=hi[j]))

        # 4. degree of top nodes (self-loops excluded, reported separately)
        for b in buckets:
            tb = t[t.b == b]
            ns = tb[~tb.self]
            for j, n in enumerate(top):
                out_ = ns[ns.cause == n]
                in_ = ns[ns.effect == n]
                o, i = len(out_), len(in_)
                rows_deg.append(dict(version=v, scheme=s, bucket=b, node=n, label=labels[n], rank=j + 1,
                                     out_claims=o, in_claims=i, out_nbrs=out_.effect.nunique(),
                                     in_nbrs=in_.cause.nunique(), self_claims=int((tb.self & (tb.cause == n)).sum()),
                                     cause_ratio=o / (o + i) if o + i else np.nan,
                                     out_per_100=100 * o / len(tb), in_per_100=100 * i / len(tb)))

        # 5. similarity between buckets
        node_sets = {b: set(r.node[r.b == b]) for b in buckets}
        edge_sets = {b: set(zip(t.cause[(t.b == b) & ~t.self], t.effect[(t.b == b) & ~t.self])) for b in buckets}
        vec = g.pivot_table(index="node", columns="b", values="any_claims", fill_value=0)
        nmin = int(nclaims.min())
        claim_nodes = {b: [frozenset((c, e)) for c, e in zip(t.cause[t.b == b], t.effect[t.b == b])] for b in buckets}
        subs = {b: [set().union(*(claim_nodes[b][k] for k in RNG.choice(len(claim_nodes[b]), nmin, replace=False)))
                    for _ in range(N_SUB)] for b in buckets}
        mat = pd.DataFrame(np.nan, index=buckets, columns=buckets)
        for i, b1 in enumerate(buckets):
            for b2 in buckets[i:]:
                val = np.mean([jacc(x, y) for x, y in zip(subs[b1], subs[b2])]) if b1 != b2 else 1.0
                mat.loc[b1, b2] = mat.loc[b2, b1] = val
        mat.to_csv(OUT / f"similarity_matrix_{v}_{s}.csv", float_format="%.4f")
        for b1, b2 in zip(buckets, buckets[1:]):
            x, y = vec[b1].to_numpy(), vec[b2].to_numpy()
            rows_sim.append(dict(version=v, scheme=s, bucket_from=b1, bucket_to=b2,
                                 jaccard_nodes=jacc(node_sets[b1], node_sets[b2]),
                                 jaccard_nodes_size_matched=mat.loc[b1, b2], size_matched_n=nmin,
                                 jaccard_edges=jacc(edge_sets[b1], edge_sets[b2]),
                                 cosine_weighted=float(x @ y / np.linalg.norm(x) / np.linalg.norm(y))))
            # 6. risers and fallers between consecutive buckets (nodes with >= 3 claims in either)
            w = vec[[b1, b2]].copy()
            w = w[(w[b1] >= 3) | (w[b2] >= 3)]
            d = (w[b2] / nclaims[b2] - w[b1] / nclaims[b1]).sort_values()
            for kind, part in [("faller", d[d < 0].head(5)), ("riser", d[d > 0].tail(5)[::-1])]:
                for n, dv in part.items():
                    rows_rf.append(dict(version=v, scheme=s, bucket_from=b1, bucket_to=b2, kind=kind, node=n,
                                        label=labels[n], claims_from=int(w.loc[n, b1]), claims_to=int(w.loc[n, b2]),
                                        share_change=dv))
    print("done", v)

pd.DataFrame(rows_summary).to_csv(OUT / "bucket_summary.csv", index=False)
pd.concat(rows_share)[["version", "scheme", "bucket", "node", "label", "any_claims", "cause_claims", "effect_claims",
                       "bucket_claims", "share_any", "share_cause", "share_effect"]].to_csv(
    OUT / "node_share.csv", index=False, float_format="%.4f")
pd.DataFrame(rows_ci).to_csv(OUT / "top_nodes_share_ci.csv", index=False, float_format="%.4f")
pd.DataFrame(rows_deg).to_csv(OUT / "top_nodes_degree.csv", index=False, float_format="%.4f")
pd.DataFrame(rows_sim).to_csv(OUT / "consecutive_similarity.csv", index=False, float_format="%.4f")
pd.DataFrame(rows_rf).to_csv(OUT / "risers_fallers.csv", index=False, float_format="%.4f")

# 7. cross-version robustness: map each event-035 top node to the node in each other version
# that holds most of its (claim, role) slots, then correlate the monthly share series.
base = "event-035"
tb_, lb_ = tables[base]
slots = lambda t: pd.concat([t[["id", "cause"]].rename(columns={"cause": "node"}).assign(role="c"),
                             t[["id", "effect"]].rename(columns={"effect": "node"}).assign(role="e")])
bs = slots(tb_)
share = pd.concat(rows_share)
share = share[share.scheme == "month"]
months = sorted(share.bucket.unique())
rows_x = []
for other in VERSIONS[1:]:
    to, lo_ = tables[other]
    os_ = slots(to)
    m = bs.merge(os_, on=["id", "role"], suffixes=("", "_o"))
    for j, n in enumerate(top_lists[base]):
        mm = m[m.node == n].node_o.value_counts()
        n_o = mm.index[0]
        a = share[(share.version == base) & (share.node == n)].set_index("bucket").share_any.reindex(months, fill_value=0)
        b = share[(share.version == other) & (share.node == n_o)].set_index("bucket").share_any.reindex(months, fill_value=0)
        rows_x.append(dict(base_node=n, base_label=lb_[n], rank=j + 1, other_version=other, other_node=n_o,
                           other_label=lo_[n_o], slots_kept=mm.iloc[0] / mm.sum(),
                           other_size_ratio=(os_.node == n_o).sum() / (bs.node == n).sum(),
                           spearman_monthly_share=a.corr(b, method="spearman"),
                           pearson_monthly_share=a.corr(b)))
pd.DataFrame(rows_x).to_csv(OUT / "cross_version_nodes.csv", index=False, float_format="%.3f")

sim = pd.DataFrame(rows_sim)
xs = []
for s in SCHEMES:
    p = sim[sim.scheme == s].pivot(index="bucket_from", columns="version", values="jaccard_nodes_size_matched")
    c = p.corr(method="spearman")
    xs.append(c.assign(scheme=s))
pd.concat(xs).to_csv(OUT / "cross_version_similarity_corr.csv", float_format="%.3f")

# 8. similarity by lag (size-matched Jaccard, mean over all bucket pairs that far apart)
lag_rows = []
for v in VERSIONS:
    for s in SCHEMES:
        m = pd.read_csv(OUT / f"similarity_matrix_{v}_{s}.csv", index_col=0).to_numpy()
        for k in range(1, len(m)):
            d = np.diag(m, k)
            lag_rows.append(dict(version=v, scheme=s, lag=k, pairs=len(d), mean=d.mean(), min=d.min(), max=d.max()))
pd.DataFrame(lag_rows).to_csv(OUT / "similarity_by_lag.csv", index=False, float_format="%.4f")
print("written to", OUT)
