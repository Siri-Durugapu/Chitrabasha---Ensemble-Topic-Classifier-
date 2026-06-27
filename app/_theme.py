"""
_theme.py — editorial design system for Chitrabasha.
"""
import streamlit as st


def get_mode():
    return st.session_state.get("theme_mode", "light")


def _css(mode):
    if mode == "dark":
        return _build_css(
            page_bg     = "#0e0e0e",
            surface     = "#161616",
            border_col  = "#2a2a2a",
            border_soft = "#1e1e1e",
            text_pri    = "#f0ede8",
            text_sec    = "#6b6b6b",
            text_dim    = "#3a3a3a",
            accent      = "#d4a853",
            accent_bg   = "#1e1a10",
            accent_text = "#d4a853",
            danger      = "#c0392b",
            success     = "#2ecc71",
            btn_bg      = "#1e1e1e",
            btn_border  = "#2a2a2a",
            btn_color   = "#6b6b6b",
            btn_pbg     = "#d4a853",
            btn_pcolor  = "#0e0e0e",
            inp_bg      = "#161616",
            inp_border  = "#2a2a2a",
            inp_text    = "#f0ede8",
            inp_ph      = "#3a3a3a",
            metric_bg   = "#161616",
            metric_brd  = "#2a2a2a",
            metric_lbl  = "#3a3a3a",
            metric_val  = "#f0ede8",
        )
    else:
        return _build_css(
            page_bg     = "#f7f5f0",
            surface     = "#ffffff",
            border_col  = "#d9d5cc",
            border_soft = "#ece9e3",
            text_pri    = "#1a1814",
            text_sec    = "#7a7570",
            text_dim    = "#c4bfb8",
            accent      = "#b8860b",
            accent_bg   = "#fdf8ed",
            accent_text = "#7a5500",
            danger      = "#c0392b",
            success     = "#27ae60",
            btn_bg      = "#f0ede8",
            btn_border  = "#d9d5cc",
            btn_color   = "#7a7570",
            btn_pbg     = "#1a1814",
            btn_pcolor  = "#f7f5f0",
            inp_bg      = "#ffffff",
            inp_border  = "#d9d5cc",
            inp_text    = "#1a1814",
            inp_ph      = "#c4bfb8",
            metric_bg   = "#ffffff",
            metric_brd  = "#d9d5cc",
            metric_lbl  = "#c4bfb8",
            metric_val  = "#1a1814",
        )


def _build_css(page_bg, surface, border_col, border_soft, text_pri, text_sec,
               text_dim, accent, accent_bg, accent_text, danger, success,
               btn_bg, btn_border, btn_color, btn_pbg, btn_pcolor,
               inp_bg, inp_border, inp_text, inp_ph,
               metric_bg, metric_brd, metric_lbl, metric_val):
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding: 0 3.5rem 4rem !important;
    max-width: 1200px !important;
}}

.stApp {{ background: {page_bg}; color: {text_pri}; }}

/* ── Sidebar container ──
   IMPORTANT: every override below is scoped to the EXPANDED state only
   (the [aria-expanded="true"] attribute selector). Streamlit itself
   toggles this attribute when the user clicks the collapse arrow, and
   relies on its own internal styles for the collapsed state — including
   resizing the main content area to fill the space the sidebar vacates.

   ACTUAL ROOT CAUSE OF THE "reopen button is unreachable" BUG, FOUND BY
   INSPECTING THE LIVE DOM STEP BY STEP: Streamlit collapses the sidebar
   using `transform: translateX(-300px)` on [data-testid="stSidebar"]
   itself. A non-`none` CSS `transform` on ANY ancestor creates a new
   containing block for `position: fixed` descendants (standard CSS
   behavior) — so the collapse button was being positioned relative to
   the sidebar's own offscreen box instead of the viewport.

   AN EARLIER VERSION OF THIS FIX neutralized the sidebar's `transform`
   and replaced it with `margin-left` to dodge the containing-block
   issue — but that broke something else: Streamlit's own JS resizes the
   main content area in response to the sidebar collapsing, and that
   logic depends on its own transform-based collapse mechanism, not the
   substitute. The result was a wide dead gap and clipped content on the
   left, because the main pane never got told to reclaim the freed
   space.

   CORRECT FIX: leave the sidebar's own transform completely untouched
   (so Streamlit's main-content resizing keeps working exactly as
   designed), and instead cancel the containing-block effect ONLY on the
   button, by applying an equal-and-opposite transform to it. The
   sidebar moves left by 300px; the button, as its descendant, inherits
   that 300px shift as its new fixed-position origin — so shifting the
   button right by the same 300px puts it back at the real viewport
   position it would have had with no transform involved at all. */
section[data-testid="stSidebar"][aria-expanded="true"] {{
    background: {surface} !important;
    border-right: 1px solid {border_col} !important;
    width: 240px !important;
    min-width: 240px !important;
    max-width: 240px !important;
}}
section[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {{
    width: 240px !important;
}}
section[data-testid="stSidebar"] .block-container {{
    padding: 2rem 1.5rem !important;
}}

/* ── Reopen button — guaranteed visible AND on-screen ──
   VERIFIED LIVE in DevTools before being committed here: with the
   sidebar collapsed, manually adding `transform: translateX(300px)` to
   this button via the Styles pane moved its rect from x:-288 to x:312
   — an exact +300 shift, confirming the counter-transform mechanism
   works as intended. (12 - 300 = -288, the original broken position;
   12 + 300 = 312, what we just saw — both match, so this isn't a
   coincidence.)

   The 300px value matches the sidebar's own collapse transform
   (translateX(-300px), read directly from getComputedStyle on the
   collapsed sidebar earlier in this debugging session). If a future
   Streamlit version changes that collapse distance, this number needs
   to change with it.

   position/top/left are restated explicitly here rather than assumed
   from Streamlit's own default CSS, since that default was never
   directly confirmed — only inferred from the original (broken)
   coordinates. */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    position: fixed !important;
    top: 12px !important;
    left: 12px !important;
    color: {text_sec} !important;
    background: {surface} !important;
    border: 1px solid {border_col} !important;
}}
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="collapsedControl"] {{
    transform: translateX(300px) !important;
}}

/* ── Streamlit's AUTO-GENERATED multipage nav ──
   We render our own nav manually via st.page_link() in each page, so the
   auto nav's link list is hidden to avoid a duplicate menu. We ONLY ever
   touch the inner <ul> — never the outer stSidebarNav container's box
   model (no padding/min-height overrides), because zeroing those out is
   what previously made empty-wrapper edge cases collapse the sidebar. */
section[data-testid="stSidebarNav"] ul {{
    display: none !important;
}}

/* ── Manual st.page_link() nav — styled to match the design system ── */
[data-testid="stPageLink"] {{
    padding: 0.45rem 0 !important;
    border-bottom: 1px solid {border_soft} !important;
    border-radius: 0 !important;
    min-height: 0 !important;
}}
[data-testid="stPageLink"] > a {{
    gap: 0.5rem !important;
}}
[data-testid="stPageLink"] p {{
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    color: {text_sec} !important;
}}
[data-testid="stPageLink"]:hover p {{
    color: {accent} !important;
}}
[data-testid="stPageLink"] a[aria-current="page"] p {{
    color: {accent} !important;
}}

/* ── Header collapse/expand button (desktop top bar) — always visible ──
   Note: the sidebar reopen button (stSidebarCollapseButton, formerly
   collapsedControl) is already handled in the dedicated block above,
   right next to the sidebar rules it's paired with — kept as a single
   source of truth instead of duplicating the selector in two places
   that could drift out of sync. */
button[kind="header"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: {text_sec} !important;
    background: {surface} !important;
    border: 1px solid {border_col} !important;
}}

/* ── Typography tokens ── */
.t-overline {{
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {text_dim};
}}
.t-h1 {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: {text_pri};
    letter-spacing: -0.02em;
    line-height: 1.2;
}}
.t-h2 {{
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {text_dim};
    margin-bottom: 0.6rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid {border_soft};
}}
.t-body {{
    font-size: 0.88rem;
    color: {text_sec};
    line-height: 1.7;
}}
.t-mono {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: {text_sec};
    font-variant-numeric: tabular-nums;
}}
.t-mono-lg {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 500;
    color: {text_pri};
    letter-spacing: -0.03em;
}}
.t-label {{
    font-size: 0.75rem;
    font-weight: 500;
    color: {text_sec};
}}

/* ── Layout rules ── */
.ruled {{
    border-top: 1px solid {border_col};
    margin: 2rem 0;
}}
.ruled-soft {{
    border-top: 1px solid {border_soft};
    margin: 1.25rem 0;
}}
.page-top {{
    padding: 2.5rem 0 1.5rem;
    border-bottom: 2px solid {text_pri};
    margin-bottom: 2rem;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
}}

/* ── Stat blocks ── */
.stat-strip {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-top: 1px solid {border_col};
    margin-bottom: 2rem;
}}
.stat-item {{
    padding: 1.25rem 0 1.25rem;
    border-right: 1px solid {border_col};
    padding-right: 1.5rem;
    margin-right: 1.5rem;
}}
.stat-item:last-child {{ border-right: none; }}
.stat-item .lbl {{ font-size: 0.62rem; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: {text_dim}; margin-bottom: 0.4rem; }}
.stat-item .val {{
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: {text_pri};
    letter-spacing: -0.03em;
    line-height: 1;
}}
.stat-item .sub {{ font-size: 0.72rem; color: {text_sec}; margin-top: 0.25rem; }}

/* ── Result display ── */
.result-block {{
    padding: 2rem 0;
    border-top: 2px solid {accent};
    border-bottom: 1px solid {border_col};
    margin: 1.5rem 0;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2rem;
    align-items: start;
}}
.result-topic {{
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 700;
    color: {text_pri};
    letter-spacing: -0.03em;
    line-height: 1.1;
}}
.result-meta {{
    font-size: 0.72rem;
    color: {text_dim};
    margin-top: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
}}
.conf-meter {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.25rem;
}}
.conf-number {{
    font-family: 'Playfair Display', serif;
    font-size: 3.5rem;
    font-weight: 700;
    color: {accent};
    letter-spacing: -0.04em;
    line-height: 1;
}}
.conf-label {{
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {text_dim};
}}

/* ── Prediction rows ── */
.pred-row {{
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    padding: 0.65rem 0;
    border-bottom: 1px solid {border_soft};
    gap: 1rem;
}}
.pred-row:first-child {{ border-top: 1px solid {border_soft}; }}
.pred-name {{ font-size: 0.88rem; color: {text_sec}; font-weight: 400; }}
.pred-name.top {{ color: {text_pri}; font-weight: 600; }}
.pred-score {{ font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: {text_dim}; }}
.pred-score.top {{ color: {accent}; font-weight: 500; }}
.pred-bar-wrap {{
    grid-column: 1 / -1;
    height: 2px;
    background: {border_soft};
    margin-top: -1px;
}}
.pred-bar-fill {{
    height: 2px;
    background: {accent};
}}

/* ── Vote table ── */
.vote-table {{ width: 100%; border-collapse: collapse; }}
.vote-table td {{
    padding: 0.55rem 0;
    border-bottom: 1px solid {border_soft};
    font-size: 0.82rem;
}}
.vote-table .model-cell {{ color: {text_dim}; font-size: 0.62rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; }}
.vote-table .pred-cell {{ color: {text_sec}; text-align: right; }}
.vote-table .pred-cell.match {{ color: {accent}; font-weight: 600; }}
.verdict-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    border-top: 2px solid {text_pri};
    margin-top: 0.25rem;
}}
.verdict-lbl {{ font-size: 0.62rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: {text_dim}; }}
.verdict-val {{ font-size: 0.82rem; font-weight: 600; color: {text_pri}; }}

/* ── Tag/pill ── */
.tag {{
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 8px;
    border: 1px solid {border_col};
    color: {text_sec};
}}
.tag-accent {{
    border-color: {accent};
    color: {accent_text};
    background: {accent_bg};
}}

/* ── Rank list (Analytics page "Lowest F1 classes") ── */
.rank-list {{
    border-top: 2px solid {text_pri};
}}
.rank-row {{
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    padding: 0.7rem 0;
    border-bottom: 1px solid {border_soft};
}}
.rank-name {{
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 4px;
    color: {text_pri};
}}
.rank-bar-bg {{
    height: 2px;
    background: {border_col};
    width: 100%;
}}
.rank-score {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    padding-left: 1.5rem;
}}

/* ── Streamlit overrides ── */
.stProgress {{ margin: 0 !important; }}
.stProgress > div > div {{
    background: {border_soft} !important;
    border-radius: 0 !important;
    height: 2px !important;
}}
.stProgress > div > div > div {{
    background: {accent} !important;
    border-radius: 0 !important;
}}
.stTextArea textarea {{
    background: {inp_bg} !important;
    border: 1px solid {inp_border} !important;
    border-radius: 0 !important;
    color: {inp_text} !important;
    font-size: 0.92rem !important;
    line-height: 1.75 !important;
    font-family: 'Inter', sans-serif !important;
}}
.stTextArea textarea::placeholder {{ color: {inp_ph} !important; }}
.stTextArea textarea:focus {{
    border-color: {accent} !important;
    box-shadow: none !important;
    outline: none !important;
}}
.stButton > button[kind="primary"] {{
    background: {btn_pbg} !important;
    border: none !important;
    border-radius: 0 !important;
    color: {btn_pcolor} !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.6rem !important;
    transition: opacity 0.15s !important;
}}
.stButton > button[kind="primary"]:hover {{ opacity: 0.85 !important; }}
.stButton > button:not([kind="primary"]) {{
    background: {btn_bg} !important;
    border: 1px solid {btn_border} !important;
    border-radius: 0 !important;
    color: {btn_color} !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}}
.stSlider [data-baseweb="thumb"] {{
    background: {accent} !important;
    border: none !important;
    border-radius: 0 !important;
    width: 3px !important;
    height: 16px !important;
}}
.stSlider [data-baseweb="track-background"] {{ background: {border_col} !important; border-radius: 0 !important; }}
.stSlider [data-baseweb="track-fill"] {{ background: {accent} !important; border-radius: 0 !important; }}
[data-testid="metric-container"] {{
    background: {metric_bg} !important;
    border: none !important;
    border-top: 2px solid {metric_brd} !important;
    border-radius: 0 !important;
    padding: 1rem 0 !important;
}}
[data-testid="stMetricLabel"] {{ color: {metric_lbl} !important; font-size: 0.62rem !important; text-transform: uppercase; letter-spacing: 0.14em; font-weight: 600 !important; }}
[data-testid="stMetricValue"] {{
    color: {metric_val} !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    font-family: 'Playfair Display', serif !important;
}}
.stDataFrame {{ border: 1px solid {border_col} !important; border-radius: 0 !important; overflow: hidden !important; }}
.streamlit-expanderHeader {{
    background: {surface} !important;
    border: 1px solid {border_col} !important;
    border-radius: 0 !important;
    color: {text_sec} !important;
}}
.stSpinner > div {{ border-top-color: {accent} !important; }}
label[data-testid="stWidgetLabel"] p {{
    font-size: 0.72rem !important;
    color: {text_sec} !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}}
hr {{ border-color: {border_col} !important; margin: 1.5rem 0 !important; }}

/* ── Sidebar chrome ── */
.sb-wordmark {{
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: {text_pri};
    margin-bottom: 1.5rem;
    letter-spacing: -0.01em;
}}
.sb-rule {{ border-top: 1px solid {border_col}; margin: 1rem 0; }}
.sb-section {{
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {text_dim};
    margin: 1.25rem 0 0.6rem;
}}
.sb-item {{
    display: flex;
    justify-content: space-between;
    padding: 0.35rem 0;
    border-bottom: 1px solid {border_soft};
}}
.sb-item-label {{ font-size: 0.78rem; color: {text_sec}; }}
.sb-item-val   {{ font-size: 0.78rem; color: {text_pri}; font-family: 'JetBrains Mono', monospace; font-weight: 500; }}
.dot {{ display: inline-block; width: 5px; height: 5px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }}
.dot-on   {{ background: {success}; }}
.dot-off  {{ background: {danger}; }}
.dot-warn {{ background: #e67e22; }}
.theme-toggle {{
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {text_dim};
    cursor: pointer;
    border: 1px solid {border_col};
    background: transparent;
    padding: 3px 8px;
}}
</style>
"""


def inject_css():
    mode = get_mode()
    st.markdown(_css(mode), unsafe_allow_html=True)


def theme_toggle_sidebar():
    mode = get_mode()
    label = "Switch to light" if mode == "dark" else "Switch to dark"
    if st.button(label, key="__theme_toggle__", use_container_width=True):
        st.session_state["theme_mode"] = "dark" if mode == "light" else "light"
        st.rerun()


def render_nav():
    """Shared navigation block — one source of truth for all three pages.

    Using a single helper instead of copy-pasting the nav markup into every
    page means there's only one place that can ever drift out of sync with
    the actual page filenames.
    """
    st.markdown('<div class="sb-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Navigation</div>', unsafe_allow_html=True)
    st.page_link("app.py", label="Classifier", icon="🏷")
    st.page_link("pages/1_Dataset.py", label="Dataset Statistics", icon="📚")
    st.page_link("pages/2_Analytics.py", label="Model Analytics", icon="📊")


def render_sidebar_header():
    """Wordmark + theme toggle + nav — the part identical across all pages."""
    st.markdown('<div class="sb-wordmark">Chitrabasha</div>', unsafe_allow_html=True)
    theme_toggle_sidebar()
    render_nav()