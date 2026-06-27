"""
Chitrabasha — topic classifier.
Run: streamlit run app/app.py
"""

import os, sys, requests
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from _theme import inject_css, theme_toggle_sidebar, get_mode

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Chitrabasha",
    page_icon="🏷",
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
    st.page_link("app.py",                    label="Classifier",          icon="🏷")
    st.page_link("pages/1_Dataset.py",        label="Dataset Statistics",  icon="📚")
    st.page_link("pages/2_Analytics.py",      label="Model Analytics",     icon="📊")

    st.markdown('<div class="sb-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Settings</div>', unsafe_allow_html=True)
    top_k = st.slider("Predictions shown", 1, 10, 3)

    st.markdown('<div class="sb-section">Ensemble</div>', unsafe_allow_html=True)
    for m in ["Naive Bayes", "Logistic Regression", "Linear SVM", "Meta-model"]:
        st.markdown(f'<div class="sb-item"><span class="sb-item-label">{m}</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">System</div>', unsafe_allow_html=True)
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.ok:
            status = '<span class="dot dot-on"></span><span style="font-size:0.78rem;color:#27ae60;font-weight:600">API online</span>'
        else:
            status = '<span class="dot dot-warn"></span><span style="font-size:0.78rem;color:#e67e22">Degraded</span>'
    except Exception:
        status = '<span class="dot dot-off"></span><span style="font-size:0.78rem;color:#c0392b">API offline</span>'
    st.markdown(status, unsafe_allow_html=True)

    st.markdown('<div class="sb-rule"></div>', unsafe_allow_html=True)
    for label, val in [("Categories", "24"), ("Training samples", "100k"), ("Macro F1", "82%")]:
        st.markdown(f"""
<div class="sb-item">
  <span class="sb-item-label">{label}</span>
  <span class="sb-item-val">{val}</span>
</div>
""", unsafe_allow_html=True)


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-top">
  <div>
    <div class="t-overline">NLP · Ensemble classifier</div>
    <div class="t-h1" style="margin-top:0.4rem">Topic classifier</div>
  </div>
  <div style="display:flex;gap:8px;align-items:flex-end">
    <span class="tag">24 categories</span>
    <span class="tag">Stacked ensemble</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Input area ────────────────────────────────────────────────────────────────
st.markdown('<div class="t-h2">Input text</div>', unsafe_allow_html=True)

# A key is required here: without one, Streamlit preserves whatever the user
# typed across reruns, so the "Clear" button below couldn't actually empty it.
text = st.text_area(
    label="text",
    key="input_text",
    label_visibility="collapsed",
    height=155,
    placeholder="Paste any article, paragraph, or sentence — the classifier works across 24 topic areas.",
)

char_count = len(text)
over_limit = char_count > 10_000

col_meta, col_btn, col_clr = st.columns([5.5, 1.1, 0.85])
with col_meta:
    col = "#c0392b" if over_limit else ""
    st.markdown(
        f'<span class="t-mono" style="color:{col if col else ""}">'
        f'{char_count:,} / 10,000 chars</span>',
        unsafe_allow_html=True,
    )
with col_btn:
    run = st.button("Classify", type="primary", use_container_width=True)
with col_clr:
    if st.button("Clear", use_container_width=True):
        st.session_state["input_text"] = ""
        st.rerun()


# ── Prediction ────────────────────────────────────────────────────────────────
if run:
    if not text.strip():
        st.warning("Enter some text first.")
        st.stop()
    if over_limit:
        st.error("Text exceeds 10,000 characters.")
        st.stop()

    with st.spinner("Running ensemble…"):
        try:
            resp = requests.post(
                f"{API_URL}/predict",
                json={"text": text, "top_k": top_k},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.ConnectionError:
            st.error("API offline — run `uvicorn api.main:app --port 8000`.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("Request timed out. Try again.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"API error {e.response.status_code}: {e.response.text}")
            st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    required = {"label", "confidence", "top_k", "model_votes", "decided_by", "latency_ms"}
    if not required.issubset(data):
        st.error("Unexpected API response. Check server logs.")
        st.stop()

    agreed   = len(set(data["model_votes"].values())) == 1
    verdict  = "Consensus" if agreed else "Resolved by meta-model"
    topic    = data["label"].replace("_", " ").title()
    conf_pct = f"{data['confidence']:.0%}"
    decided  = data["decided_by"].replace("_", " ").title()
    latency  = f"{data['latency_ms']:.0f}ms"

    st.markdown(f"""
<div class="result-block">
  <div>
    <div class="t-overline" style="margin-bottom:0.5rem">Predicted topic</div>
    <div class="result-topic">{topic}</div>
    <div class="result-meta">{decided} · {latency} · <span style="font-variant:small-caps">{verdict}</span></div>
  </div>
  <div class="conf-meter">
    <div class="conf-label">Confidence</div>
    <div class="conf-number">{conf_pct}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.markdown('<div class="t-h2">Top predictions</div>', unsafe_allow_html=True)
        for i, item in enumerate(data["top_k"]):
            name   = item["label"].replace("_", " ").title()
            score  = item["score"]
            is_top = item["label"] == data["label"]
            n_cls  = "pred-name top" if is_top else "pred-name"
            s_cls  = "pred-score top" if is_top else "pred-score"
            rank   = f"{i+1}."
            st.markdown(f"""
<div class="pred-row">
  <span class="{n_cls}"><span style="opacity:.35;margin-right:8px;font-variant-numeric:tabular-nums">{rank}</span>{name}</span>
  <span class="{s_cls}">{score:.1%}</span>
</div>
<div class="pred-bar-wrap"><div class="pred-bar-fill" style="width:{score*100:.1f}%"></div></div>
""", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="t-h2">Model votes</div>', unsafe_allow_html=True)
        rows = ""
        for model, pred in data["model_votes"].items():
            match     = pred == data["label"]
            pred_name = pred.replace("_", " ").title()
            cls       = "pred-cell match" if match else "pred-cell"
            rows += f"""
<tr>
  <td class="model-cell">{model.upper()}</td>
  <td class="{cls}">{pred_name}</td>
</tr>"""
        st.markdown(f"""
<table class="vote-table">
  {rows}
</table>
<div class="verdict-row">
  <span class="verdict-lbl">Decision</span>
  <span class="verdict-val">{decided}</span>
</div>
""", unsafe_allow_html=True)