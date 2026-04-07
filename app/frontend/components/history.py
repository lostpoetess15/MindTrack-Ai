# ══════════════════════════════════════════════════════
#  history.py — session history component
# ══════════════════════════════════════════════════════
import logging
from datetime import datetime, timezone

import streamlit as st
from utils.styles import RISK_COLORS

log = logging.getLogger(__name__)

HISTORY_BTN_CSS = """
<style>
/* Shrink the › arrow button to inline size */
div[data-testid="stHorizontalBlock"] > div:last-child button {
    padding       : 0 6px !important;
    min-height    : 0 !important;
    height        : 28px !important;
    font-size     : 14px !important;
    background    : transparent !important;
    border        : 0.5px solid #D8CFC2 !important;
    color         : #8C8070 !important;
    border-radius : 3px !important;
    margin-top    : 4px !important;
}
div[data-testid="stHorizontalBlock"] > div:last-child button:hover {
    background   : #F2EDE4 !important;
    border-color : #B8AD9E !important;
    color        : #3D3830 !important;
}
</style>
"""


def _inject_history_css():
    if not st.session_state.get('_hist_btn_css'):
        st.markdown(HISTORY_BTN_CSS, unsafe_allow_html=True)
        st.session_state['_hist_btn_css'] = True


def add_to_history(preview: str, risk: str, modality: str,
                   confidence: float, full_result: dict = None):
    """
    Prepend a prediction entry to the session history list.
    full_result holds the complete API response for the detail view.
    """
    if 'history' not in st.session_state or st.session_state.history is None:
        st.session_state.history = []

    st.session_state.history.insert(0, {
        'preview'    : preview[:55] + ('…' if len(preview) > 55 else ''),
        'input_full' : preview,                          # untruncated
        'risk'       : risk,
        'modality'   : modality,
        'confidence' : confidence,
        'time'       : datetime.now().strftime('%H:%M'),
        'created_at' : datetime.now(timezone.utc).isoformat(),
        'full_result': full_result or {},
    })
    st.session_state.history = st.session_state.history[:20]


def refresh_history_from_db():
    """Re-fetch history from the backend database."""
    try:
        from utils.api_client import get_history as _get_history
        response = _get_history(page=1, limit=20)
        raw      = response.get('predictions', [])

        loaded = []
        for p in raw:
            try:
                ts       = p.get('created_at', '')
                time_str = datetime.fromisoformat(
                    ts.replace('Z', '+00:00')
                ).strftime('%H:%M')
            except Exception:
                time_str = '--:--'

            loaded.append({
                'preview'    : p.get('input_preview') or f"[{p.get('modality','?')}]",
                'input_full' : p.get('input_preview', ''),
                'risk'       : p.get('risk_level', 'Unknown'),
                'modality'   : p.get('modality', 'text'),
                'confidence' : p.get('confidence', 0.0),
                'time'       : time_str,
                'created_at' : p.get('created_at', ''),
                # DB records only have summary fields — no class_probs etc.
                # history_detail.py handles this gracefully.
                'full_result': {
                    'risk_level' : p.get('risk_level', 'Unknown'),
                    'confidence' : p.get('confidence', 0.0),
                    'elapsed_ms' : None,
                    '_from_db'   : True,        # flag: limited data available
                },
            })

        st.session_state.history = loaded

    except Exception as e:
        log.warning(f"refresh_history_from_db failed: {e}")


def render_history():
    """Renders session history in the sidebar with clickable detail arrows."""
    _inject_history_css()

    history = st.session_state.get('history') or []

    if not history:
        st.markdown(
            '<div style="font-family:\'Lora\',serif;font-style:italic;'
            'font-size:0.8rem;color:#B8AD9E;padding:0.5rem 0">'
            'No entries yet.</div>',
            unsafe_allow_html=True
        )
        return

    for idx, item in enumerate(history):
        color    = RISK_COLORS.get(item['risk'], '#8C8070')
        icon     = 'T' if item['modality'] == 'text' else 'A'
        conf_pct = int(item['confidence'] * 100)

        # ── Row: card HTML (wide col) + arrow button (narrow col) ─────
        row_col, btn_col = st.columns([9, 1])

        with row_col:
            st.markdown(f"""
            <div class="hist-entry">
                <div class="hist-risk-dot" style="background:{color}"></div>
                <div class="hist-body">
                    <div class="hist-preview">{item['preview']}</div>
                    <div class="hist-meta">
                        {icon} &middot; {conf_pct}% &middot; {item['time']}
                    </div>
                </div>
                <div class="hist-risk-label" style="color:{color}">
                    {item['risk']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with btn_col:
            if st.button("›", key=f"hist_open_{idx}",
                         help="View full details"):
                st.session_state['show_history_detail'] = True
                st.session_state['history_detail_idx']  = idx
                st.rerun()