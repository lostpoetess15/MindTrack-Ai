MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,700;1,400;1,500&family=Lora:ital,wght@0,400;0,500;1,400&family=DM+Mono:wght@300;400&display=swap');

/* ── Root variables ─────────────────────────────────── */
:root {
    --cream:       #FAF7F2;
    --cream-dark:  #F2EDE4;
    --cream-deep:  #E8DFD0;
    --charcoal:    #1C1916;
    --charcoal-md: #3D3830;
    --muted:       #8C8070;
    --muted-light: #B8AD9E;
    --terracotta:  #B85C38;
    --terra-light: #E8A882;
    --terra-pale:  #F5E8DF;
    --sage:        #4A7055;
    --sage-light:  #A8C4A0;
    --sage-pale:   #EAF2E8;
    --amber:       #C07820;
    --amber-light: #E8B86A;
    --amber-pale:  #FDF3E0;
    --border:      #D8CFC2;
    --border-light:#EAE4DA;
}

/* ── Base ───────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Lora', Georgia, serif !important;
}
.stApp {
    background-color: var(--cream) !important;
}

/* ── Hide Streamlit chrome ──────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Layout ─────────────────────────────────────────── */
.block-container {
    padding: 3rem 2.5rem 5rem !important;
    max-width: 780px !important;
}

/* ── Masthead ───────────────────────────────────────── */
.masthead {
    border-bottom: 1.5px solid var(--charcoal);
    padding-bottom: 1.2rem;
    margin-bottom: 2.5rem;
}
.masthead-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    font-weight: 300;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.4rem;
}
.masthead-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.6rem;
    font-weight: 400;
    color: var(--charcoal);
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin: 0;
}
.masthead-title em {
    font-style: italic;
    color: var(--terracotta);
}
.masthead-rule {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.8rem;
}
.masthead-rule-line {
    flex: 1;
    height: 1px;
    background: var(--border);
}
.masthead-rule-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--terracotta);
}

/* ── Section label ──────────────────────────────────── */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    font-weight: 400;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted-light);
    margin-bottom: 0.65rem;
}

/* ── Tabs ───────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    margin-bottom: 0.25rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 400 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.5rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    color: var(--charcoal) !important;
    border-bottom: 2px solid var(--terracotta) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 1.5rem 0 0 !important;
    background: transparent !important;
}

/* ── Journal textarea ───────────────────────────────── */
.stTextArea > label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}
.stTextArea textarea {
    background: #FFFDF9 !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    color: var(--charcoal) !important;
    font-family: 'Lora', serif !important;
    font-size: 1rem !important;
    line-height: 1.85 !important;
    padding: 1.1rem 1.25rem !important;
    resize: vertical !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.04) !important;
}
.stTextArea textarea:focus {
    border-color: var(--charcoal-md) !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.04),
                0 0 0 3px rgba(184,92,56,0.08) !important;
    outline: none !important;
}
.stTextArea textarea::placeholder {
    color: var(--muted-light) !important;
    font-style: italic !important;
}

/* ── File uploader ──────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #FFFDF9 !important;
    border: 1px dashed var(--border) !important;
    border-radius: 4px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--charcoal-md) !important;
}
[data-testid="stFileUploader"] label {
    color: var(--muted) !important;
    font-family: 'Lora', serif !important;
    font-style: italic !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
}

/* ── Buttons ────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: var(--charcoal) !important;
    color: var(--cream) !important;
    border: 1.5px solid var(--charcoal) !important;
    border-radius: 3px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 400 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--charcoal-md) !important;
    border-color: var(--charcoal-md) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: var(--cream-deep) !important;
    color: var(--muted-light) !important;
    border-color: var(--border) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--muted) !important;
    color: var(--charcoal-md) !important;
}

/* ── Result reveal animation ────────────────────────── */
.result-reveal {
    animation: fadeSlide 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Result: editorial treatment ───────────────────── */
.result-outer {
    border-top: 1.5px solid var(--charcoal);
    padding-top: 1.5rem;
    margin-top: 1.5rem;
}
.result-kicker {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--muted-light);
    margin-bottom: 0.5rem;
}
.result-headline {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 400;
    line-height: 1.05;
    margin: 0 0 0.15rem;
    letter-spacing: -0.5px;
}
.result-hl-low      { color: var(--sage); }
.result-hl-moderate { color: var(--amber); }
.result-hl-high     { color: var(--terracotta); }

.result-subhead {
    font-family: 'Lora', serif;
    font-size: 0.92rem;
    font-style: italic;
    color: var(--muted);
    line-height: 1.6;
    margin-bottom: 1.25rem;
    max-width: 480px;
}

/* ── Inline confidence meter ────────────────────────── */
.conf-track {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1rem;
}
.conf-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted-light);
    min-width: 80px;
}
.conf-bar-bg {
    flex: 1;
    height: 3px;
    background: var(--cream-deep);
    border-radius: 2px;
    overflow: hidden;
}
.conf-bar-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
}
.cfill-low      { background: var(--sage); }
.cfill-moderate { background: var(--amber); }
.cfill-high     { background: var(--terracotta); }
.conf-pct {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--charcoal-md);
    min-width: 34px;
    text-align: right;
}

/* ── Class breakdown ────────────────────────────────── */
.breakdown-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
    border-bottom: 1px solid var(--border-light);
}
.breakdown-row:last-child { border-bottom: none; }
.breakdown-name {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted-light);
    min-width: 68px;
}
.breakdown-track {
    flex: 1;
    height: 2px;
    background: var(--cream-deep);
    border-radius: 1px;
}
.breakdown-fill {
    height: 100%;
    border-radius: 1px;
}
.breakdown-pct {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    min-width: 32px;
    text-align: right;
}

/* ── Meta strip ─────────────────────────────────────── */
.meta-strip {
    display: flex;
    gap: 1.5rem;
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-light);
}
.meta-piece {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted-light);
}
.meta-piece span { color: var(--muted); margin-left: 4px; }

/* ── Sentiment tag ──────────────────────────────────── */
.sentiment-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 2px;
    margin-top: 0.4rem;
}
.st-positive { background: var(--sage-pale);  color: var(--sage); }
.st-negative { background: var(--terra-pale); color: var(--terracotta); }
.st-neutral  { background: var(--cream-dark); color: var(--muted); }

/* ── Notice card (message below result) ─────────────── */
.notice-card {
    background: var(--cream-dark);
    border-left: 2.5px solid var(--charcoal-md);
    padding: 0.9rem 1.1rem;
    margin-top: 1rem;
    border-radius: 0 3px 3px 0;
}
.notice-card.low      { border-left-color: var(--sage); }
.notice-card.moderate { border-left-color: var(--amber); }
.notice-card.high     { border-left-color: var(--terracotta); }
.notice-body {
    font-family: 'Lora', serif;
    font-size: 0.9rem;
    font-style: italic;
    color: var(--charcoal-md);
    line-height: 1.7;
}

/* ── Disclaimer ─────────────────────────────────────── */
.disclaimer {
    margin-top: 3rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border);
}
.disclaimer-text {
    font-family: 'Lora', serif;
    font-size: 0.78rem;
    color: var(--muted-light);
    line-height: 1.8;
    font-style: italic;
}
.disclaimer-text strong { color: var(--muted); font-style: normal; }

/* ── Char counter ───────────────────────────────────── */
.char-count {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted-light);
    text-align: right;
    margin-top: -0.4rem;
    margin-bottom: 0.6rem;
}
.char-warn  { color: var(--amber) !important; }
.char-error { color: var(--terracotta) !important; }

/* ── Inline alert ───────────────────────────────────── */
.inline-warn {
    font-family: 'Lora', serif;
    font-size: 0.85rem;
    font-style: italic;
    color: var(--terracotta);
    margin-top: 0.4rem;
    padding: 0.4rem 0;
}

/* ── Backend offline warning ────────────────────────── */
.offline-banner {
    background: var(--terra-pale);
    border: 1px solid var(--terra-light);
    border-radius: 3px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 2rem;
}
.offline-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--terracotta);
    font-weight: 400;
    margin-bottom: 0.3rem;
}
.offline-body {
    font-family: 'Lora', serif;
    font-size: 0.85rem;
    color: var(--charcoal-md);
}
.offline-code {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    background: rgba(0,0,0,0.06);
    padding: 1px 6px;
    border-radius: 2px;
}

/* ── Sidebar ────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--cream-dark) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1.25rem !important;
}
.sidebar-brand {
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
    margin-bottom: 1.1rem;
}
.sidebar-brand-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    font-weight: 500;
    color: var(--charcoal);
    letter-spacing: -0.2px;
}
.sidebar-brand-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted-light);
    margin-top: 3px;
}
.sidebar-section {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted-light);
    margin-bottom: 0.5rem;
    margin-top: 1rem;
}
.status-line {
    font-family: 'Lora', serif;
    font-size: 0.8rem;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
}
.status-dot-on  { width:7px;height:7px;border-radius:50%;background:var(--sage);flex-shrink:0; }
.status-dot-off { width:7px;height:7px;border-radius:50%;background:var(--terracotta);flex-shrink:0; }

/* ── History entries ────────────────────────────────── */
.hist-entry {
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--border-light);
    display: flex;
    gap: 8px;
    align-items: flex-start;
}
.hist-entry:last-child { border-bottom: none; }
.hist-risk-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
}
.hist-body { flex: 1; overflow: hidden; }
.hist-preview {
    font-family: 'Lora', serif;
    font-size: 0.78rem;
    color: var(--charcoal-md);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
}
.hist-meta {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.5px;
    color: var(--muted-light);
    margin-top: 2px;
    text-transform: uppercase;
}
.hist-risk-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.5px;
    flex-shrink: 0;
    text-transform: uppercase;
}

/* ── Risk legend ────────────────────────────────────── */
.legend-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
}
.legend-swatch {
    width: 20px;
    height: 2px;
    border-radius: 1px;
    flex-shrink: 0;
}
.legend-text {
    font-family: 'Lora', serif;
    font-size: 0.78rem;
    color: var(--muted);
}

/* ── Model status list ──────────────────────────────── */
.model-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 3px 0;
}
.model-name {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.5px;
    color: var(--muted);
}
.model-ok  { color: var(--sage); font-size: 0.65rem; font-family: monospace; }
.model-err { color: var(--terracotta); font-size: 0.65rem; font-family: monospace; }

/* ── Audio preview ──────────────────────────────────── */
.audio-meta {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted-light);
    margin-bottom: 0.5rem;
}
</style>
"""

RISK_COLORS = {
    'Low':      '#4A7055',   # sage
    'Moderate': '#C07820',   # amber
    'High':     '#B85C38',   # terracotta
}

RISK_FILL_CLASSES = {
    'Low':      'cfill-low',
    'Moderate': 'cfill-moderate',
    'High':     'cfill-high',
}

RISK_MESSAGES = {
    'Low':
        "Your language reflects a positive or settled emotional state. "
        "This is a good sign — keep nurturing the habits and connections "
        "that are supporting you.",
    'Moderate':
        "Some indicators of elevated stress were present. This is common "
        "and manageable. Consider speaking openly with someone you trust, "
        "or taking intentional time to rest.",
    'High':
        "Significant distress signals were detected in your input. "
        "Please know that support is available. Reaching out to a mental "
        "health professional or a trusted person today is a meaningful step.",
}