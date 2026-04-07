# ══════════════════════════════════════════════════════════════════════
#  history_detail.py — full detail view for a single history entry
#
#  Handles two data shapes:
# ══════════════════════════════════════════════════════════════════════
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st
from utils.styles import RISK_COLORS, RISK_MESSAGES

DETAIL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Lora:ital,wght@0,400;0,500;1,400&family=DM+Mono:wght@300;400&display=swap');

.hd-back {
    display     : inline-flex;
    align-items : center;
    gap         : 6px;
    font-family : 'DM Mono', monospace;
    font-size   : 0.65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color       : #8C8070;
    margin-bottom: 1.75rem;
    cursor      : pointer;
}
.hd-masthead {
    border-bottom: 1.5px solid #1C1916;
    padding-bottom: 1.1rem;
    margin-bottom: 1.5rem;
}
.hd-eyebrow {
    font-family   : 'DM Mono', monospace;
    font-size     : 0.58rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color         : #B8AD9E;
    margin-bottom : 0.35rem;
}
.hd-headline {
    font-family  : 'Playfair Display', serif;
    font-size    : 2.6rem;
    font-weight  : 400;
    line-height  : 1.05;
    letter-spacing: -0.5px;
    margin       : 0 0 0.2rem;
}
.hd-hl-low      { color: #4A7055; }
.hd-hl-moderate { color: #C07820; }
.hd-hl-high     { color: #B85C38; }
.hd-hl-unknown  { color: #8C8070; }

.hd-subhead {
    font-family: 'Lora', serif;
    font-size  : 0.92rem;
    font-style : italic;
    color      : #8C8070;
    line-height: 1.65;
}
.hd-section-label {
    font-family   : 'DM Mono', monospace;
    font-size     : 0.58rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color         : #B8AD9E;
    margin-bottom : 0.5rem;
    display       : block;
    margin-top    : 1.25rem;
}
.hd-meta-grid {
    display              : grid;
    grid-template-columns: 1fr 1fr;
    gap                  : 10px;
    margin-bottom        : 1rem;
}
.hd-meta-card {
    background   : #FAF7F2;
    border       : 1px solid #E8DFD0;
    border-radius: 4px;
    padding      : 0.7rem 0.9rem;
}
.hd-meta-label {
    font-family   : 'DM Mono', monospace;
    font-size     : 0.55rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color         : #B8AD9E;
    margin-bottom : 0.2rem;
    display       : block;
}
.hd-meta-value {
    font-family: 'Lora', serif;
    font-size  : 0.92rem;
    color      : #1C1916;
}
.hd-conf-track {
    display    : flex;
    align-items: center;
    gap        : 10px;
    margin     : 0.5rem 0 1rem;
}
.hd-conf-label {
    font-family   : 'DM Mono', monospace;
    font-size     : 0.62rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color         : #B8AD9E;
    min-width     : 80px;
}
.hd-conf-bar-bg {
    flex        : 1;
    height      : 5px;
    background  : #E8DFD0;
    border-radius: 3px;
    overflow    : hidden;
}
.hd-conf-bar-fill {
    height       : 100%;
    border-radius: 3px;
}
.hd-conf-pct {
    font-family: 'DM Mono', monospace;
    font-size  : 0.75rem;
    color      : #3D3830;
    min-width  : 34px;
    text-align : right;
}
.hd-prob-row {
    display    : flex;
    align-items: center;
    gap        : 10px;
    padding    : 6px 0;
    border-bottom: 1px solid #EAE4DA;
}
.hd-prob-row:last-child { border-bottom: none; }
.hd-prob-name {
    font-family   : 'DM Mono', monospace;
    font-size     : 0.62rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color         : #8C8070;
    min-width     : 72px;
}
.hd-prob-track {
    flex        : 1;
    height      : 3px;
    background  : #E8DFD0;
    border-radius: 2px;
}
.hd-prob-fill { height: 100%; border-radius: 2px; }
.hd-prob-pct {
    font-family: 'DM Mono', monospace;
    font-size  : 0.65rem;
    color      : #8C8070;
    min-width  : 30px;
    text-align : right;
}
.hd-input-box {
    background   : #FFFDF9;
    border       : 1px solid #E8DFD0;
    border-left  : 3px solid #B85C38;
    border-radius: 0 4px 4px 0;
    padding      : 1rem 1.1rem;
    margin       : 0.5rem 0 1rem;
}
.hd-input-text {
    font-family: 'Lora', serif;
    font-size  : 1rem;
    font-style : italic;
    color      : #1C1916;
    line-height: 1.78;
}
.hd-sentiment-row {
    display    : flex;
    align-items: center;
    gap        : 8px;
    padding    : 0.45rem 0;
}
.hd-sent-dot {
    width        : 8px;
    height       : 8px;
    border-radius: 50%;
    flex-shrink  : 0;
}
.hd-sent-label {
    font-family   : 'DM Mono', monospace;
    font-size     : 0.62rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color         : #8C8070;
    min-width     : 80px;
}
.hd-sent-value {
    font-family: 'Lora', serif;
    font-size  : 0.88rem;
    color      : #3D3830;
}
.hd-source-badge {
    display       : inline-block;
    font-family   : 'DM Mono', monospace;
    font-size     : 0.58rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding       : 3px 9px;
    border-radius : 3px;
    margin-bottom : 0.75rem;
}
.hd-src-transcript { background:#EAF2E8; color:#4A7055; border:1px solid #C8D8C4; }
.hd-src-audio      { background:#FAF7F2; color:#8C8070; border:1px solid #E8DFD0; }
.hd-db-notice {
    font-family: 'Lora', serif;
    font-size  : 0.82rem;
    font-style : italic;
    color      : #B8AD9E;
    padding    : 0.7rem 0.9rem;
    background : #FAF7F2;
    border     : 1px solid #E8DFD0;
    border-radius: 4px;
    margin-top : 0.75rem;
}
.hd-divider {
    height    : 1px;
    background: #E8DFD0;
    margin    : 1.1rem 0;
}
.hd-disclaimer {
    font-family: 'Lora', serif;
    font-size  : 0.75rem;
    font-style : italic;
    color      : #B8AD9E;
    line-height: 1.75;
    margin-top : 2.5rem;
    padding-top: 1rem;
    border-top : 1px solid #E8DFD0;
}
</style>
"""

RISK_CONF_COLORS = {
    'Low'     : '#4A7055',
    'Moderate': '#C07820',
    'High'    : '#B85C38',
    'Unknown' : '#8C8070',
}


def _inject_css():
    if not st.session_state.get('_hd_css_v2'):
        st.markdown(DETAIL_CSS, unsafe_allow_html=True)
        st.session_state['_hd_css_v2'] = True


def _fmt_datetime(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
        return dt.strftime('%d %B %Y  at  %H:%M')
    except Exception:
        return iso or '—'


def _esc(text: str) -> str:
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))


def render_history_detail(entry: dict):
    """
    Full detail page for one history entry.

    Handles two data shapes:
      fresh  — full_result contains class_probs, sentiment, elapsed_ms
      db     — full_result._from_db=True, only risk_level + confidence
    """
    _inject_css()

    risk        = entry.get('risk', 'Unknown')
    risk_lower  = risk.lower() if risk in ('Low', 'Moderate', 'High') else 'unknown'
    color       = RISK_CONF_COLORS.get(risk, '#8C8070')
    modality    = entry.get('modality', 'text')
    confidence  = entry.get('confidence', 0.0)
    conf_pct    = int(confidence * 100)
    created_at  = entry.get('created_at', '')
    input_full  = entry.get('input_full', entry.get('preview', ''))
    full        = entry.get('full_result') or {}
    from_db     = full.get('_from_db', False)

    # ── Back button ───────────────────────────────────────────────────
    if st.button("← Back", key="hd_back", type="secondary"):
        st.session_state['show_history_detail'] = False
        st.session_state.pop('history_detail_idx', None)
        st.rerun()

    # ── Masthead ──────────────────────────────────────────────────────
    icon_label = 'Text entry' if modality == 'text' else 'Voice recording'
    when_label = _fmt_datetime(created_at) if created_at else entry.get('time', '—')

    st.markdown(f"""
    <div class="hd-masthead">
        <div class="hd-eyebrow">
            Past entry &nbsp;&middot;&nbsp; {icon_label}
            &nbsp;&middot;&nbsp; {when_label}
        </div>
        <div class="hd-headline hd-hl-{risk_lower}">{risk} Risk</div>
        <div class="hd-subhead">{RISK_MESSAGES.get(risk, '')}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Source badge (live recordings only) ───────────────────────────
    source = full.get('_source', '')
    if source == 'transcript':
        st.markdown(
            '<span class="hd-source-badge hd-src-transcript">'
            'Analysed via transcript — text model'
            '</span>',
            unsafe_allow_html=True
        )
    elif source == 'audio':
        st.markdown(
            '<span class="hd-source-badge hd-src-audio">'
            'Analysed via audio features'
            '</span>',
            unsafe_allow_html=True
        )

    # ── Meta grid ─────────────────────────────────────────────────────
    elapsed = full.get('elapsed_ms')
    dur     = full.get('duration_seconds')

    meta = [
        ('Modality',    icon_label),
        ('Recorded',    when_label),
        ('Analysed in', f"{elapsed} ms" if elapsed else '—'),
        ('Duration',    f"{dur}s" if dur else '—'),
    ]
    st.markdown('<div class="hd-meta-grid">', unsafe_allow_html=True)
    for label, value in meta:
        st.markdown(f"""
        <div class="hd-meta-card">
            <span class="hd-meta-label">{label}</span>
            <div class="hd-meta-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Confidence bar ────────────────────────────────────────────────
    st.markdown('<span class="hd-section-label">Confidence</span>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div class="hd-conf-track">
        <div class="hd-conf-label">Overall</div>
        <div class="hd-conf-bar-bg">
            <div class="hd-conf-bar-fill"
                 style="width:{conf_pct}%;background:{color}"></div>
        </div>
        <div class="hd-conf-pct">{conf_pct}%</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Class probabilities — only for fresh predictions ──────────────
    probs = full.get('class_probs', {})
    if probs and not from_db:
        st.markdown('<span class="hd-section-label">Risk breakdown</span>',
                    unsafe_allow_html=True)
        prob_colors = {
            'High':     '#B85C38',
            'Moderate': '#C07820',
            'Low':      '#4A7055',
        }
        for cls in ['High', 'Moderate', 'Low']:
            p   = probs.get(cls, 0.0)
            pct = int(p * 100)
            c   = prob_colors.get(cls, '#8C8070')
            st.markdown(f"""
            <div class="hd-prob-row">
                <div class="hd-prob-name">{cls}</div>
                <div class="hd-prob-track">
                    <div class="hd-prob-fill"
                         style="width:{pct}%;background:{c}"></div>
                </div>
                <div class="hd-prob-pct">{pct}%</div>
            </div>
            """, unsafe_allow_html=True)

    elif from_db:
        st.markdown("""
        <div class="hd-db-notice">
            Detailed probability breakdown is only available for
            analyses performed in the current session.
        </div>
        """, unsafe_allow_html=True)

    # ── Sentiment (text modality only, fresh predictions only) ────────
    sentiment = full.get('sentiment')
    if sentiment is not None and not from_db and modality == 'text':
        st.markdown('<div class="hd-divider"></div>', unsafe_allow_html=True)
        st.markdown('<span class="hd-section-label">Sentiment score</span>',
                    unsafe_allow_html=True)

        if sentiment > 0.05:
            s_label, s_color = 'Positive', '#4A7055'
        elif sentiment < -0.05:
            s_label, s_color = 'Negative', '#B85C38'
        else:
            s_label, s_color = 'Neutral', '#8C8070'

        sign = '+' if sentiment > 0 else ''
        st.markdown(f"""
        <div class="hd-sentiment-row">
            <div class="hd-sent-dot" style="background:{s_color}"></div>
            <div class="hd-sent-label">Sentiment</div>
            <div class="hd-sent-value" style="color:{s_color}">
                {s_label} &nbsp;&middot;&nbsp; {sign}{sentiment:.3f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Audio secondary result (when transcript was primary) ──────────
    audio_risk = full.get('_audio_risk')
    audio_conf = full.get('_audio_confidence', 0.0)
    if audio_risk:
        st.markdown('<div class="hd-divider"></div>', unsafe_allow_html=True)
        st.markdown('<span class="hd-section-label">Audio model</span>',
                    unsafe_allow_html=True)
        ac = RISK_CONF_COLORS.get(audio_risk, '#8C8070')
        note = ' (differed from transcript result)' if audio_risk != risk else ''
        st.markdown(f"""
        <div style="font-family:'Lora',serif;font-size:.9rem;
                    color:{ac};font-style:italic">
            {audio_risk} risk &nbsp;&middot;&nbsp;
            {int(audio_conf*100)}% confidence{note}
        </div>
        """, unsafe_allow_html=True)

    # ── Input text / transcript ───────────────────────────────────────
    # Show for text entries always; show for audio if transcript exists
    show_input = (
        modality == 'text'
        or (modality == 'audio' and input_full
            and not input_full.startswith('['))
    )
    if show_input and input_full and input_full.strip():
        st.markdown('<div class="hd-divider"></div>', unsafe_allow_html=True)

        section_lbl = 'Your entry' if modality == 'text' else 'Transcript'
        st.markdown(f'<span class="hd-section-label">{section_lbl}</span>',
                    unsafe_allow_html=True)

        display = input_full if len(input_full) <= 500 \
                  else input_full[:500] + '…'

        st.markdown(f"""
        <div class="hd-input-box">
            <div class="hd-input-text">{_esc(display)}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────────────────
    st.markdown("""
    <div class="hd-disclaimer">
        This record is for self-reflection only. MindTrack AI does not provide
        medical diagnosis or treatment recommendations. If you are in distress,
        please contact a qualified healthcare professional.
    </div>
    """, unsafe_allow_html=True)