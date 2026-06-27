"""
Dataset Statistics — memory-safe reservoir sampling.
"""

import os, sys, time, random
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _theme import inject_css, theme_toggle_sidebar

DATA_PATH     = os.path.join("data", "dataset_10M.parquet")
SAMPLE_TARGET = 30_000
TEXT_COL      = "DATA"
LABEL_COL     = "TOPIC"

st.set_page_config(
    page_title="Dataset · Chitrabasha",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-wordmark">Chitrabasha</div>', unsafe_allow_html=True)
    theme_toggle_sidebar()

    st.markdown('<div class="sb-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Navigation</div>', unsafe_allow_html=True)
    st.page_link("app.py",               label="Classifier",         icon="🏷")
    st.page_link("pages/1_Dataset.py",   label="Dataset Statistics", icon="📚")
    st.page_link("pages/2_Analytics.py", label="Model Analytics",    icon="📊")

    st.markdown('<div class="sb-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Sample size</div>', unsafe_allow_html=True)
    sample_size = st.slider("Rows", 5_000, SAMPLE_TARGET, 20_000, step=5_000)
    st.markdown("""
<div class="t-body" style="margin-top:0.5rem">
One row group in memory at a time. Larger samples are more representative.
</div>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-top">
  <div>
    <div class="t-overline">Training data</div>
    <div class="t-h1" style="margin-top:0.4rem">Dataset statistics</div>
  </div>
  <span class="tag">Parquet · 10M rows</span>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at `{DATA_PATH}`.")
    st.stop()

# ── Metadata KPIs ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_meta():
    pf = pq.ParquetFile(DATA_PATH)
    m  = pf.metadata
    return {"total_rows": m.num_rows, "num_rg": m.num_row_groups, "num_cols": m.num_columns}

with st.spinner("Reading metadata…"):
    try:
        meta = get_meta()
    except Exception as e:
        st.error(f"Could not open file: {e}")
        st.stop()

st.markdown(f"""
<div class="stat-strip">
  <div class="stat-item">
    <div class="lbl">Total rows</div>
    <div class="val">{meta['total_rows']/1_000_000:.1f}M</div>
    <div class="sub">in dataset</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Row groups</div>
    <div class="val">{meta['num_rg']:,}</div>
    <div class="sub">parquet chunks</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Columns</div>
    <div class="val">{meta['num_cols']}</div>
    <div class="sub">per record</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Sample ratio</div>
    <div class="val">{sample_size/meta['total_rows']*100:.2f}%</div>
    <div class="sub">{sample_size:,} rows</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Reservoir sample ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def reservoir_sample(target: int, seed: int = 42):
    rng = random.Random(seed)
    res = []
    n   = 0
    pf  = pq.ParquetFile(DATA_PATH)
    t0  = time.perf_counter()
    for rg in range(pf.metadata.num_row_groups):
        tbl   = pf.read_row_group(rg, columns=[TEXT_COL, LABEL_COL])
        chunk = tbl.to_pandas()
        tbl   = None
        for _, row in chunk.iterrows():
            n += 1
            if len(res) < target:
                res.append({TEXT_COL: row[TEXT_COL], LABEL_COL: row[LABEL_COL]})
            else:
                j = rng.randint(0, n - 1)
                if j < target:
                    res[j] = {TEXT_COL: row[TEXT_COL], LABEL_COL: row[LABEL_COL]}
        chunk = None
    return pd.DataFrame(res).reset_index(drop=True), time.perf_counter() - t0

with st.spinner(f"Sampling {sample_size:,} rows…"):
    try:
        df, elapsed = reservoir_sample(sample_size)
    except MemoryError:
        st.error("Out of memory — lower sample size in sidebar.")
        st.stop()
    except Exception as e:
        st.error(f"Sampling failed: {e}")
        st.stop()

text_len = df[TEXT_COL].str.len()

st.markdown(f"""
<div class="stat-strip">
  <div class="stat-item">
    <div class="lbl">Sampled rows</div>
    <div class="val">{len(df):,}</div>
    <div class="sub">reservoir sample</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Categories</div>
    <div class="val">{df[LABEL_COL].nunique()}</div>
    <div class="sub">distinct topics</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Avg length</div>
    <div class="val">{text_len.mean():.0f}</div>
    <div class="sub">chars per text</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Sample time</div>
    <div class="val">{elapsed:.1f}s</div>
    <div class="sub">wall clock</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<p class="t-body">Reservoir sample — category counts are estimates proportional to the full dataset.</p>', unsafe_allow_html=True)
st.markdown('<div class="ruled"></div>', unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown('<div class="t-h2">Category distribution</div>', unsafe_allow_html=True)
counts = df[LABEL_COL].value_counts().rename_axis("Topic").rename("Count").reset_index().set_index("Topic")
st.bar_chart(counts, color="#b8860b", height=280)

st.markdown('<div class="ruled-soft"></div>', unsafe_allow_html=True)
st.markdown('<div class="t-h2">Text length distribution (chars, capped at 2,000)</div>', unsafe_allow_html=True)

lens = text_len.clip(upper=2_000)
cnts, edges = np.histogram(lens, bins=40)
hist_df = pd.DataFrame({
    "Length": ((edges[:-1] + edges[1:]) / 2).astype(int),
    "Count": cnts,
}).set_index("Length")
st.bar_chart(hist_df, color="#6b6b6b", height=200)

st.markdown('<div class="ruled"></div>', unsafe_allow_html=True)

# ── Sample rows ───────────────────────────────────────────────────────────────
st.markdown('<div class="t-h2">Sample rows</div>', unsafe_allow_html=True)
n_rows = st.slider("Rows", 5, 50, 10, step=5)
st.dataframe(
    df.sample(n=min(n_rows, len(df)), random_state=None).reset_index(drop=True),
    use_container_width=True, height=280,
)