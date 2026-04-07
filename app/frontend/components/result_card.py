import streamlit as st
from utils.styles import RISK_COLORS, RISK_FILL_CLASSES, RISK_MESSAGES


def render_result(result: dict, modality: str = 'text'):
    risk      = result.get('risk_level', 'Unknown')
    conf      = result.get('confidence', 0.0)
    probs     = result.get('class_probs', {})
    elapsed   = result.get('elapsed_ms', 0)
    sentiment = result.get('sentiment')
    duration  = result.get('duration_seconds')

    risk_lower  = risk.lower()
    color       = RISK_COLORS.get(risk, '#8C8070')
    fill_class  = RISK_FILL_CLASSES.get(risk, 'cfill-low')
    message     = RISK_MESSAGES.get(risk, '')
    conf_pct    = int(conf * 100)

    # ── Outer wrapper with reveal animation ───────────────────────────
    st.markdown('<div class="result-reveal">', unsafe_allow_html=True)

    # ── Editorial headline treatment ──────────────────────────────────
    st.markdown(f"""
    <div class="result-outer">
        <div class="result-kicker">Assessment</div>
        <div class="result-headline result-hl-{risk_lower}">{risk} Risk</div>
        <div class="result-subhead">{message}</div>
    """, unsafe_allow_html=True)

    # ── Analysis source badge (live recordings only) ──────────────────
    source = result.get('_source')
    if source == 'transcript':
        st.markdown("""
        <div style="font-family:'DM Mono',monospace;font-size:.6rem;
                    letter-spacing:1.5px;text-transform:uppercase;
                    color:#4A7055;margin:.3rem 0 .6rem">
            Analysed via transcript &mdash; text model
        </div>
        """, unsafe_allow_html=True)
        # Show audio result if it differed
        audio_risk = result.get('_audio_risk')
        if audio_risk and audio_risk != risk:
            st.markdown(f"""
            <div style="font-family:'Lora',serif;font-style:italic;
                        font-size:.78rem;color:#8C8070;margin-bottom:.5rem">
                Audio model suggested {audio_risk}
                ({int(result.get('_audio_confidence',0)*100)}% confidence)
            </div>
            """, unsafe_allow_html=True)
    elif source == 'audio':
        st.markdown("""
        <div style="font-family:'DM Mono',monospace;font-size:.6rem;
                    letter-spacing:1.5px;text-transform:uppercase;
                    color:#8D6E63;margin:.3rem 0 .6rem">
            Analysed via audio features
        </div>
        """, unsafe_allow_html=True)

    # ── Confidence bar ────────────────────────────────────────────────
    st.markdown(f"""
        <div class="conf-track">
            <div class="conf-label">Confidence</div>
            <div class="conf-bar-bg">
                <div class="conf-bar-fill {fill_class}"
                     style="width:{conf_pct}%"></div>
            </div>
            <div class="conf-pct">{conf_pct}%</div>
        </div>
    """, unsafe_allow_html=True)

    # ── Class probability breakdown ───────────────────────────────────
    st.markdown('<div style="margin:0.75rem 0 0.5rem">', unsafe_allow_html=True)
    for cls in ['High', 'Moderate', 'Low']:
        p    = probs.get(cls, 0.0)
        pct  = int(p * 100)
        c    = RISK_COLORS.get(cls, '#8C8070')
        st.markdown(f"""
        <div class="breakdown-row">
            <div class="breakdown-name">{cls}</div>
            <div class="breakdown-track">
                <div class="breakdown-fill"
                     style="width:{pct}%;background:{c}"></div>
            </div>
            <div class="breakdown-pct">{pct}%</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sentiment tag (text only) ─────────────────────────────────────
    if sentiment is not None:
        if sentiment > 0.05:
            s_label, s_cls, s_val = "Positive", "st-positive", f"+{sentiment:.3f}"
        elif sentiment < -0.05:
            s_label, s_cls, s_val = "Negative", "st-negative", f"{sentiment:.3f}"
        else:
            s_label, s_cls, s_val = "Neutral",  "st-neutral",  f"{sentiment:.3f}"

        st.markdown(
            f'<div class="sentiment-tag {s_cls}">'
            f'{s_label} &nbsp; {s_val}'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Meta strip ────────────────────────────────────────────────────
    meta = [f'Analysed in<span> {elapsed} ms</span>']
    if duration:
        meta.append(f'Duration<span> {duration}s</span>')
    meta.append(f'Via<span> {modality}</span>')

    st.markdown(f"""
        <div class="meta-strip">
            {''.join(f'<div class="meta-piece">{m}</div>' for m in meta)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close result-reveal