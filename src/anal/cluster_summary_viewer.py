"""選定クラスタ・ペアの可視化とサマリービューア

クラスタモード: 選定クラスタを地図表示 + 温泉／地理（hionsen）サマリーを並列表示
ペアモード    : 選定ペアの2クラスタを色分け地図表示 + ペアサマリーを並列表示

Usage:
    uv run streamlit run src/anal/cluster_summary_viewer.py
"""

from pathlib import Path

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.cluster.hierarchy import dendrogram
from streamlit_folium import st_folium

DATA_DIR = Path("data/gee_results/all_node_5")
APPENDIX_PATH = Path("docs/app_docs/appendix.md")
OVERVIEW_PATH = Path("docs/app_docs/overview.md")
LEGEND_PATH  = Path("docs/app_docs/legend.md")
CREDITS_PATH = Path("docs/app_docs/datacredits.md")
UMAP_PATH = DATA_DIR / "umap_10d.parquet"
HDBSCAN_PATH = DATA_DIR / "hdbscan_mcs10.parquet"
CLUSTERS_PATH = DATA_DIR / "micro_clusters.csv"
PAIRS_PATH = DATA_DIR / "micro_clusters_pairs.csv"
STATS_PATH = DATA_DIR / "stats_mcs10.csv"
LINKAGE_PATH = DATA_DIR / "linkage_mcs10.csv"
LEAF_MAP_PATH = DATA_DIR / "linkage_mcs10_leaf_map.csv"
NODE_LOCATION_PATH = DATA_DIR / "node_location.csv"

COLOR_A = "#2980b9"   # 青: クラスタA / 単体
COLOR_B = "#e67e22"   # 橙: クラスタB
MAP_SAMPLE = 300      # クラスタあたりの最大プロット点数


def _latest(pattern: str) -> Path | None:
    files = sorted(DATA_DIR.glob(pattern))
    return files[-1] if files else None


@st.cache_data
def load_geo() -> pd.DataFrame:
    return pd.read_parquet(UMAP_PATH, columns=["node_id", "lat", "lon"]).drop_duplicates("node_id")


@st.cache_data
def load_hdbscan() -> pd.DataFrame:
    return pd.read_parquet(HDBSCAN_PATH, columns=["node_id", "hdbscan_10"]).drop_duplicates(["node_id", "hdbscan_10"])


@st.cache_data
def load_clusters() -> pd.DataFrame:
    return pd.read_csv(CLUSTERS_PATH)


@st.cache_data
def load_stats() -> pd.DataFrame:
    return pd.read_csv(STATS_PATH)


@st.cache_data
def load_pairs() -> pd.DataFrame:
    return pd.read_csv(PAIRS_PATH)


@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data
def load_linkage():
    df = pd.read_csv(LINKAGE_PATH)
    return df[["scipy_idx_a", "scipy_idx_b", "distance", "size"]].values.astype(float)


@st.cache_data
def load_leaf_map() -> pd.DataFrame:
    return pd.read_csv(LEAF_MAP_PATH)


@st.cache_data
def load_node_location() -> pd.DataFrame:
    return pd.read_csv(NODE_LOCATION_PATH)


def render_dendrogram(highlight: dict[int, str], chart_key: str) -> int | None:
    """系統樹を描画する（plotly）。highlight: {hdbscan_10: color}
    クリックされたリーフのクラスタIDを返す（クリックなしの場合はNone）。
    """
    Z = load_linkage()
    leaf_map = load_leaf_map().sort_values("scipy_leaf_idx")
    id_to_loc = stats_df.set_index("hdbscan_10")["location"].to_dict()
    label_ids = [str(int(row["hdbscan_10"])) for _, row in leaf_map.iterrows()]

    ddata = dendrogram(Z, labels=label_ids, no_plot=True, color_threshold=0)
    highlight_str = {str(k): v for k, v in highlight.items()}

    max_y = max(max(ys) for ys in ddata["dcoord"])
    n = len(ddata["ivl"])

    fig = go.Figure()

    # 枝線
    for xs, ys in zip(ddata["icoord"], ddata["dcoord"]):
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color="#bbbbbb", width=1),
            hoverinfo="skip", showlegend=False,
        ))

    # リーフ: クリック可能なマーカー + ラベルアノテーション
    for i, lbl in enumerate(ddata["ivl"]):
        x = 10 * i + 5
        loc = id_to_loc.get(int(lbl), "?")
        is_hl = lbl in highlight_str
        color = highlight_str.get(lbl, "#999999")
        fig.add_trace(go.Scatter(
            x=[x], y=[0],
            mode="markers",
            marker=dict(size=10 if is_hl else 7, color=color),
            customdata=[int(lbl)],
            hovertext=f"ID{lbl} {loc}",
            hoverinfo="text",
            showlegend=False,
        ))
        fig.add_annotation(
            x=x, y=0,
            xref="x", yref="paper",
            text=f"<b>ID{lbl}</b><br>{loc}" if is_hl else f"ID{lbl}<br>{loc}",
            showarrow=False,
            xanchor="right", yanchor="top",
            textangle=-90,
            font=dict(color=color, size=14 if is_hl else 12),
        )

    # ハイライトリーフを中心にした初期表示範囲
    hl_positions = [10 * i + 5 for i, lbl in enumerate(ddata["ivl"]) if lbl in highlight_str]
    if hl_positions:
        cx = sum(hl_positions) / len(hl_positions)
    else:
        cx = n * 5
    half_w = 200  # 表示幅（約40クラスタ分）
    x_range = [max(-5, cx - half_w), min(n * 10 + 5, cx + half_w)]

    fig.update_layout(
        height=520,
        showlegend=False,
        clickmode="event+select",
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                   range=x_range),
        yaxis=dict(title="distance", showgrid=False, zeroline=False,
                   range=[0, max_y * 1.05]),
        margin=dict(l=50, r=20, t=20, b=160),
        plot_bgcolor="white",
        dragmode="pan",
    )
    event = st.plotly_chart(
        fig, use_container_width=True,
        config={"scrollZoom": True},
        on_select="rerun",
        key=chart_key,
    )
    if event and event.selection and event.selection.points:
        pt = event.selection.points[0]
        cd = pt.get("customdata")
        if cd is not None:
            # customdata はリストで返る場合がある
            return int(cd[0]) if isinstance(cd, (list, tuple)) else int(cd)
    return None


def cluster_nodes(cluster_id: int, geo: pd.DataFrame, hdb: pd.DataFrame, node_loc: pd.DataFrame) -> pd.DataFrame:
    nids = hdb[hdb["hdbscan_10"] == cluster_id]["node_id"].unique()
    df = geo[geo["node_id"].isin(nids)].merge(node_loc, on="node_id", how="left")
    df["location"] = df["location"].fillna("?")
    if len(df) > MAP_SAMPLE:
        df = df.sample(MAP_SAMPLE, random_state=42)
    return df


def render_map(layers: list[tuple[pd.DataFrame, str, str]]) -> None:
    """layers: [(geo_df, color, ab_label), ...]"""
    all_lats = pd.concat([df["lat"] for df, _, _ in layers])
    all_lons = pd.concat([df["lon"] for df, _, _ in layers])
    m = folium.Map(
        location=[all_lats.mean(), all_lons.mean()],
        zoom_start=6,
        tiles="CartoDB Positron",
    )
    for df, color, ab_label in layers:
        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=4,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=f"{ab_label} {row['location']}",
            ).add_to(m)
    st_folium(m, width=None, height=520)


def render_feature(row: pd.Series | None) -> None:
    if row is None:
        st.warning("データなし")
        return
    st.info(row["CORE_TRAIT"])
    with st.expander("variation"):
        st.write(row["VARIATION"])


def render_pair_summary(row: pd.Series | None) -> None:
    if row is None:
        st.warning("データなし")
        return
    st.info(row["SIMILARITY"])
    with st.expander("contrast"):
        st.write(row["CONTRAST"])


# ── ページ設定 ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="温泉クラスタ サマリービューア", layout="wide")
st.title("温泉クラスタ サマリービューア")

geo      = load_geo()
hdb      = load_hdbscan()
cls_df   = load_clusters()
pair_df  = load_pairs()
stats_df = load_stats()
node_loc = load_node_location()
stats_df = stats_df.copy()
stats_df["umap_rank"] = stats_df["umap_std_mean"].rank(method="min").astype(int)
stats_df["geo_rank"]  = stats_df["geo_std_km"].rank(method="min").astype(int)

# 樹形図クリックによる遷移リクエストをウィジェット描画前に適用
if "pending_nav_cid" in st.session_state:
    _nav_cid = st.session_state.pop("pending_nav_cid")
    _nav_row = cls_df[cls_df["hdbscan_10"] == _nav_cid]
    if not _nav_row.empty:
        st.session_state["mode"] = "クラスタ"
        st.session_state["sel_crit_c"] = _nav_row.iloc[0]["criterion"]
        st.session_state["sel_cid"] = _nav_cid

if "pending_nav_pair_cid" in st.session_state:
    _nav_cid = st.session_state.pop("pending_nav_pair_cid")
    _pair_row = pair_df[
        (pair_df["cluster_a"] == _nav_cid) | (pair_df["cluster_b"] == _nav_cid)
    ]
    if not _pair_row.empty:
        _crit = _pair_row.iloc[0]["criterion"]
        _fp = pair_df[pair_df["criterion"] == _crit].reset_index(drop=True)
        _idx_matches = _fp[
            (_fp["cluster_a"] == _nav_cid) | (_fp["cluster_b"] == _nav_cid)
        ].index
        if len(_idx_matches) > 0:
            st.session_state["mode"] = "ペア"
            st.session_state["sel_crit_p"] = _crit
            st.session_state["sel_pair_idx"] = int(_idx_matches[0])
_n_clusters = len(stats_df)

feat_path          = _latest("cluster_feature_2*.csv")
feat_hionsen_path  = _latest("cluster_feature_hionsen_2*.csv")
cpair_path         = _latest("cluster_pair_2*.csv")
cpair_hionsen_path = _latest("cluster_pair_hionsen_2*.csv")

feat_df         = load_csv(str(feat_path))         if feat_path         else None
feat_hionsen_df = load_csv(str(feat_hionsen_path)) if feat_hionsen_path else None
cpair_df        = load_csv(str(cpair_path))         if cpair_path        else None
cpair_hionsen_df= load_csv(str(cpair_hionsen_path))if cpair_hionsen_path else None

# ── サイドバー ─────────────────────────────────────────────────────────────────
with st.sidebar:
    with st.expander("概要"):
        st.markdown(OVERVIEW_PATH.read_text(encoding="utf-8"))
    st.divider()
    st.header("設定")
    mode = st.radio("表示モード", ["クラスタ", "ペア"], key="mode")
    st.divider()

    if mode == "クラスタ":
        criteria = cls_df["criterion"].unique().tolist()
        sel_crit = st.selectbox("基準", criteria, key="sel_crit_c")
        filtered = cls_df[cls_df["criterion"] == sel_crit]
        cids = filtered["hdbscan_10"].tolist()
        if "sel_cid" not in st.session_state:
            import random
            st.session_state["sel_cid"] = cids[random.randrange(len(cids))]
        # sel_cid が現在の criterion に含まれない場合は先頭にリセット
        if st.session_state.get("sel_cid") not in cids:
            st.session_state["sel_cid"] = cids[0]
        sel_cid = st.selectbox(
            "クラスタ",
            cids,
            key="sel_cid",
            format_func=lambda x: f"ID={x}  {filtered.set_index('hdbscan_10').loc[x, 'location']}  (n={filtered.set_index('hdbscan_10').loc[x, 'count']})",
        )
        r = filtered[filtered["hdbscan_10"] == sel_cid].iloc[0]
        sr = stats_df[stats_df["hdbscan_10"] == sel_cid]
        umap_rank = f" ({int(sr.iloc[0]['umap_rank'])}/{_n_clusters})" if not sr.empty else ""
        st.metric("σUMAP", f"{r['umap_std_mean']:.4f}{umap_rank}")
        geo_rank = f" ({int(sr.iloc[0]['geo_rank'])}/{_n_clusters})" if not sr.empty else ""
        st.metric("σgeo (km)", f"{r['geo_std_km']:.1f}{geo_rank}")

    else:
        criteria = pair_df["criterion"].unique().tolist()
        sel_crit = st.selectbox("基準", criteria, key="sel_crit_p")
        fp = pair_df[pair_df["criterion"] == sel_crit].reset_index(drop=True)
        if "sel_pair_idx" not in st.session_state:
            import random
            st.session_state["sel_pair_idx"] = random.randrange(len(fp))
        _pair_idx = st.session_state.get("sel_pair_idx")
        if not isinstance(_pair_idx, int) or _pair_idx >= len(fp):
            st.session_state["sel_pair_idx"] = 0
        sel_idx = st.selectbox(
            "ペア",
            fp.index.tolist(),
            key="sel_pair_idx",
            format_func=lambda i: f"ID{fp.loc[i,'cluster_a']} {fp.loc[i,'location_a']} ↔ ID{fp.loc[i,'cluster_b']} {fp.loc[i,'location_b']}",
        )
        pr = fp.iloc[sel_idx]
        st.metric("cosine_distance", f"{pr['cosine_distance']:.4f}")
        st.metric("geo_dist_km", f"{pr['geo_dist_km']:.1f}")
        st.caption(f"A: ID={int(pr['cluster_a'])}  {pr['location_a']}")
        st.caption(f"B: ID={int(pr['cluster_b'])}  {pr['location_b']}")

    st.divider()
    with st.expander("凡例"):
        st.markdown(LEGEND_PATH.read_text(encoding="utf-8"))
    with st.expander("出典 / Data Credits"):
        st.markdown(CREDITS_PATH.read_text(encoding="utf-8"))

# ── メインコンテンツ ──────────────────────────────────────────────────────────
if mode == "クラスタ":
    st.subheader(f"クラスタ {sel_cid} — {r['location']}")
    nodes = cluster_nodes(sel_cid, geo, hdb, node_loc)
    render_map([(nodes, COLOR_A, f"ID={sel_cid}")])

    col_onsen, col_geo = st.columns(2)
    with col_onsen:
        st.markdown("#### 温泉サマリー")
        if feat_df is not None:
            row = feat_df[feat_df["CLUSTER_ID"] == sel_cid]
            render_feature(row.iloc[0] if not row.empty else None)
        else:
            st.warning("cluster_feature が見つかりません")
    with col_geo:
        st.markdown("#### 地理サマリー (hionsen)")
        if feat_hionsen_df is not None:
            row = feat_hionsen_df[feat_hionsen_df["CLUSTER_ID"] == sel_cid]
            render_feature(row.iloc[0] if not row.empty else None)
        else:
            st.warning("cluster_feature_hionsen が見つかりません")

    with st.expander("系統樹"):
        st.caption("リーフの点をクリックするとそのクラスタに遷移します。")
        clicked = render_dendrogram({sel_cid: COLOR_A}, chart_key="dendro_cluster")
        if clicked is not None and clicked != sel_cid:
            st.session_state["pending_nav_cid"] = clicked
            st.rerun()

    with st.expander("手法詳細"):
        st.markdown(APPENDIX_PATH.read_text(encoding="utf-8"))

else:
    cid_a = int(pr["cluster_a"])
    cid_b = int(pr["cluster_b"])
    st.subheader(f"ペア: {cid_a} ({pr['location_a']}) ↔ {cid_b} ({pr['location_b']})")

    nodes_a = cluster_nodes(cid_a, geo, hdb, node_loc)
    nodes_b = cluster_nodes(cid_b, geo, hdb, node_loc)
    render_map([
        (nodes_a, COLOR_A, f"A: ID={cid_a}"),
        (nodes_b, COLOR_B, f"B: ID={cid_b}"),
    ])

    col_onsen, col_geo = st.columns(2)
    with col_onsen:
        st.markdown("#### 温泉ペアサマリー")
        if cpair_df is not None:
            row = cpair_df[(cpair_df["CLUSTER_A"] == cid_a) & (cpair_df["CLUSTER_B"] == cid_b)]
            render_pair_summary(row.iloc[0] if not row.empty else None)
        else:
            st.warning("cluster_pair が見つかりません")
    with col_geo:
        st.markdown("#### 地理ペアサマリー (hionsen)")
        if cpair_hionsen_df is not None:
            row = cpair_hionsen_df[(cpair_hionsen_df["CLUSTER_A"] == cid_a) & (cpair_hionsen_df["CLUSTER_B"] == cid_b)]
            render_pair_summary(row.iloc[0] if not row.empty else None)
        else:
            st.warning("cluster_pair_hionsen が見つかりません")

    st.divider()
    st.markdown("### クラスタ別特徴")
    for ab, cid, color, label in [("A", cid_a, COLOR_A, pr["location_a"]), ("B", cid_b, COLOR_B, pr["location_b"])]:
        st.markdown(f"#### :{'blue' if color == COLOR_A else 'orange'}[{ab}: ID={cid} — {label}]")
        cls_row = stats_df[stats_df["hdbscan_10"] == cid]
        if not cls_row.empty:
            m1, m2 = st.columns(2)
            m1.metric("σUMAP", f"{cls_row.iloc[0]['umap_std_mean']:.4f} ({int(cls_row.iloc[0]['umap_rank'])}/{_n_clusters})")
            m2.metric("σgeo (km)", f"{cls_row.iloc[0]['geo_std_km']:.1f} ({int(cls_row.iloc[0]['geo_rank'])}/{_n_clusters})")
        col_f, col_h = st.columns(2)
        with col_f:
            st.markdown("**温泉**")
            if feat_df is not None:
                r = feat_df[feat_df["CLUSTER_ID"] == cid]
                render_feature(r.iloc[0] if not r.empty else None)
            else:
                st.warning("cluster_feature が見つかりません")
        with col_h:
            st.markdown("**地理 (hionsen)**")
            if feat_hionsen_df is not None:
                r = feat_hionsen_df[feat_hionsen_df["CLUSTER_ID"] == cid]
                render_feature(r.iloc[0] if not r.empty else None)
            else:
                st.warning("cluster_feature_hionsen が見つかりません")

    with st.expander("系統樹"):
        st.caption("リーフの点をクリックするとそのペアに遷移します。")
        clicked = render_dendrogram({cid_a: COLOR_A, cid_b: COLOR_B}, chart_key="dendro_pair")
        if clicked is not None:
            st.session_state["pending_nav_pair_cid"] = clicked
            st.rerun()

    with st.expander("手法詳細"):
        st.markdown(APPENDIX_PATH.read_text(encoding="utf-8"))
