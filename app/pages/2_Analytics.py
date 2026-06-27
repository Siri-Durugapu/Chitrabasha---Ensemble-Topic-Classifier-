"""
Model Analytics — fixes applymap → map for pandas ≥ 2.1.
"""

import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _theme import inject_css, theme_toggle_sidebar, get_mode

RESULTS_PATH = os.path.join("final_models", "test_results.csv")

st.set_page_config(
    page_title="Analytics · Chitrabasha",
    page_icon="📊",
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

# ── Matplotlib palette ────────────────────────────────────────────────────────
mode = get_mode()
if mode == "dark":
    BG, SURFACE, BORDER = "#0e0e0e", "#161616", "#2a2a2a"
    TEXT, DIM, ACCENT   = "#f0ede8", "#3a3a3a", "#d4a853"
    AMBER, RED          = "#e6a817", "#c0392b"
else:
    BG, SURFACE, BORDER = "#f7f5f0", "#ffffff", "#d9d5cc"
    TEXT, DIM, ACCENT   = "#1a1814", "#c4bfb8", "#b8860b"
    AMBER, RED          = "#b8860b", "#c0392b"

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-top">
  <div>
    <div class="t-overline">Evaluation</div>
    <div class="t-h1" style="margin-top:0.4rem">Model analytics</div>
  </div>
  <span class="tag">test_results.csv</span>
</div>
""", unsafe_allow_html=True)

# ── Load ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading results…")
def load():
    return pd.read_csv(RESULTS_PATH)

try:
    df = load()
except FileNotFoundError:
    st.error("**test_results.csv** not found. Run `python -m src.train` first.")
    st.stop()
except Exception as e:
    st.error(f"Failed to load: {e}")
    st.stop()

if not {"actual", "predicted"}.issubset(df.columns):
    st.error(f"Missing columns. Found: {list(df.columns)}")
    st.stop()

actual    = df["actual"]
predicted = df["predicted"]
labels    = sorted(actual.unique())
report    = classification_report(actual, predicted, output_dict=True, zero_division=0)
accuracy  = accuracy_score(actual, predicted)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="stat-strip">
  <div class="stat-item">
    <div class="lbl">Accuracy</div>
    <div class="val">{accuracy:.1%}</div>
    <div class="sub">overall</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Macro F1</div>
    <div class="val">{report['macro avg']['f1-score']:.1%}</div>
    <div class="sub">unweighted mean</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Weighted F1</div>
    <div class="val">{report['weighted avg']['f1-score']:.1%}</div>
    <div class="sub">support-weighted</div>
  </div>
  <div class="stat-item">
    <div class="lbl">Classes</div>
    <div class="val">{len(labels)}</div>
    <div class="sub">topic categories</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="ruled"></div>', unsafe_allow_html=True)

# ── Per-class table ───────────────────────────────────────────────────────────
st.markdown('<div class="t-h2">Per-class report</div>', unsafe_allow_html=True)

report_df = (
    pd.DataFrame(report).T
    .drop(index=["accuracy"], errors="ignore")
    .rename(columns={"precision": "Precision", "recall": "Recall",
                     "f1-score": "F1", "support": "Support"})
)
report_df["Support"] = report_df["Support"].astype(float).astype(int)

def _f1_colour(v):
    if isinstance(v, float):
        g = int(150 * v); r = int(200 * (1 - v))
        return f"color: rgb({r},{g},80)"
    return ""

styler = report_df.style.format({"Precision": "{:.3f}", "Recall": "{:.3f}", "F1": "{:.3f}"})
try:
    styler = styler.map(_f1_colour, subset=["F1"])
except AttributeError:
    styler = styler.applymap(_f1_colour, subset=["F1"])

st.dataframe(styler, use_container_width=True, height=400)

st.markdown('<div class="ruled"></div>', unsafe_allow_html=True)

# ── F1 bar chart ──────────────────────────────────────────────────────────────
st.markdown('<div class="t-h2">F1 by class</div>', unsafe_allow_html=True)

valid   = [l for l in labels if l in report_df.index]
f1s     = report_df.loc[valid, "F1"].sort_values()
colours = [ACCENT if v >= 0.8 else AMBER if v >= 0.6 else RED for v in f1s.values]

fig, ax = plt.subplots(figsize=(10, max(5, len(f1s) * 0.38)))
fig.patch.set_facecolor(BG)
ax.set_facecolor(SURFACE)

bars = ax.barh(f1s.index, f1s.values, color=colours, height=0.55, edgecolor="none")
ax.set_xlim(0, 1.12)
ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.bar_label(bars, fmt="%.3f", padding=5, fontsize=8, color=DIM)
ax.set_xlabel("F1 score", color=DIM, fontsize=8.5)
ax.tick_params(colors=DIM, labelsize=8)
for sp in ax.spines.values():
    sp.set_color(BORDER)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="x", color=BORDER, linewidth=0.5, linestyle="--", alpha=0.6)
ax.set_axisbelow(True)
fig.tight_layout(pad=1.2)
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.markdown('<div class="ruled"></div>', unsafe_allow_html=True)

# ── Confusion matrix ──────────────────────────────────────────────────────────
st.markdown('<div class="t-h2">Confusion matrix (row-normalised)</div>', unsafe_allow_html=True)

cm = confusion_matrix(actual, predicted, labels=labels)
with np.errstate(divide="ignore", invalid="ignore"):
    rs      = cm.sum(axis=1, keepdims=True)
    cm_norm = np.where(rs > 0, cm / rs, 0.0)

n  = len(labels)
sz = max(9, n)
fig2, ax2 = plt.subplots(figsize=(sz, sz * 0.82))
fig2.patch.set_facecolor(BG)
ax2.set_facecolor(BG)

cmap = "YlOrBr" if mode == "light" else "Blues"
im   = ax2.imshow(cm_norm, cmap=cmap, vmin=0, vmax=1, aspect="auto")

for i in range(n):
    for j in range(n):
        if cm[i, j] == 0: continue
        c = "white" if cm_norm[i, j] > 0.55 else DIM
        ax2.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=6.5, color=c)

ax2.set_xticks(range(n)); ax2.set_yticks(range(n))
ax2.set_xticklabels(labels, rotation=50, ha="right", fontsize=7.5, color=DIM)
ax2.set_yticklabels(labels, fontsize=7.5, color=DIM)
ax2.set_xlabel("Predicted", color=DIM, fontsize=9)
ax2.set_ylabel("Actual",    color=DIM, fontsize=9)
for sp in ax2.spines.values(): sp.set_color(BORDER)

cbar = fig2.colorbar(im, ax=ax2, fraction=0.025, pad=0.03)
cbar.ax.tick_params(colors=DIM, labelsize=8)
cbar.set_label("Recall", color=DIM, fontsize=8)
fig2.tight_layout(pad=1.2)
st.pyplot(fig2, use_container_width=True)
plt.close(fig2)

st.markdown('<div class="ruled"></div>', unsafe_allow_html=True)

# ── Worst performers ──────────────────────────────────────────────────────────
st.markdown('<div class="t-h2">Lowest F1 classes</div>', unsafe_allow_html=True)

# Guard: default of 5 must never exceed max_value, or Streamlit raises
# StreamlitAPIException when there are fewer than 5 valid classes.
max_n   = min(12, len(f1s))
default_n = min(5, max_n)
n_worst = st.slider("Show bottom N classes", min(3, max_n), max_n, default_n)
worst   = f1s.head(n_worst)

# Built with the theme's .rank-* classes (defined in _theme.py) instead of
# hardcoded hex colors, so this section follows light/dark mode correctly —
# previously the bar track was hardcoded to the light-mode border color
# (#d9d5cc) and the class-name text had no color set at all, which made it
# unreadable in dark mode.
rows_html = ""
for cls, score in worst.items():
    bar_w = score * 100
    col   = AMBER if score >= 0.6 else RED
    rows_html += f"""
<div class="rank-row">
  <div>
    <div class="rank-name">{cls.replace('_', ' ').title()}</div>
    <div class="rank-bar-bg">
      <div style="height:2px;background:{col};width:{bar_w:.1f}%"></div>
    </div>
  </div>
  <div class="rank-score" style="color:{col}">{score:.1%}</div>
</div>
"""
st.markdown(f'<div class="rank-list">{rows_html}</div>', unsafe_allow_html=True)