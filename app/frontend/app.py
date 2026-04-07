# main directory for frontend
import os
import streamlit as st
import requests
from dotenv import load_dotenv

# 1. PAGE CONFIG MUST BE THE VERY FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title            = "MindTrack AI",
    page_icon             = "◈",
    layout                = "centered",
    initial_sidebar_state = "expanded",
)

load_dotenv()

from components.auth_forms import render_auth_page
from utils.api_client      import logout, get_history
from utils.styles          import MAIN_CSS, RISK_COLORS
from utils.api_client      import check_health, predict_text, predict_audio
from components.result_card import render_result
from components.history    import add_to_history, render_history
from components.history_detail import render_history_detail

# ══════════════════════════════════════════════════════════════════════
#  AUTH GATE
# ══════════════════════════════════════════════════════════════════════
# If no valid token in session, show the auth page instead of the app.
if not st.session_state.get('token'):
    render_auth_page()
    st.stop()                    # Nothing below renders for logged-out users

# From here down, user is authenticated.
current_user = st.session_state.get('current_user', {})
display_name = current_user.get('display_name', 'there')

st.markdown(MAIN_CSS, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────
for key in ['history', 'text_result', 'audio_result', 'audio_mode', 'live_wav', 'live_transcript']:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'history' else None

# ── API health (cached 60s) ───────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_health():
    try:
        return True, check_health()
    except Exception:
        return False, {}

api_ok, health_data = get_health()

# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:

    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">MindTrack AI</div>
        <div class="sidebar-brand-sub">Mental health risk monitor</div>
    </div>
    """, unsafe_allow_html=True)

    # User greeting
    st.markdown(f"""
    <div style="margin-bottom:0.75rem;padding-bottom:0.75rem;
                border-bottom:1px solid var(--border)">
        <div style="font-family:'DM Mono',monospace;font-size:0.58rem;
                    letter-spacing:1.5px;text-transform:uppercase;
                    color:#B8AD9E;margin-bottom:2px">Signed in as</div>
        <div style="font-family:'Lora',serif;font-size:0.88rem;
                    color:#3D3830">{display_name}</div>
        <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                    color:#B8AD9E">{current_user.get('email','')}</div>
    </div>
    """, unsafe_allow_html=True)

    # Logout button
    if st.button("Sign out", key="logout_btn", type="secondary"):
        try:
            logout()
        except Exception:
            pass   # Token may already be expired — still clear local state
        for key in ['token', 'current_user', 'history',
                    'text_result', 'audio_result', 'live_wav', 'live_transcript']:
            st.session_state.pop(key, None)
        st.rerun()

    # API status
    if api_ok:
        st.markdown("""
        <div class="status-line">
            <div class="status-dot-on"></div>
            Backend connected
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-line">
            <div class="status-dot-off"></div>
            Backend offline
        </div>
        """, unsafe_allow_html=True)

    # Model status
    if api_ok and health_data.get('models'):
        st.markdown('<div class="sidebar-section">Models</div>',
                    unsafe_allow_html=True)
        for name, loaded in health_data['models'].items():
            label = name.replace('_', ' ')
            mark  = '<span class="model-ok">&#10003;</span>' if loaded \
                    else '<span class="model-err">&#10007;</span>'
            st.markdown(
                f'<div class="model-row">'
                f'<span class="model-name">{label}</span>{mark}</div>',
                unsafe_allow_html=True
            )

    # History
    st.markdown('<div class="sidebar-section">Recent entries</div>',
                unsafe_allow_html=True)
    render_history()

    if st.session_state.history:
        st.markdown('<div style="margin-top:0.75rem"></div>',
                    unsafe_allow_html=True)
        if st.button("Clear entries", key="clear_hist", type="secondary"):
            for k in ['history', 'text_result', 'audio_result', 'live_wav', 'live_transcript']:
                st.session_state[k] = [] if k == 'history' else None
            st.cache_data.clear()
            st.rerun()

    # Risk legend
    st.markdown('<div class="sidebar-section">Risk levels</div>',
                unsafe_allow_html=True)
    for level, desc in [
        ('Low',      'Positive or neutral'),
        ('Moderate', 'Elevated stress'),
        ('High',     'Significant distress'),
    ]:
        color = RISK_COLORS[level]
        st.markdown(f"""
        <div class="legend-row">
            <div class="legend-swatch" style="background:{color}"></div>
            <div class="legend-text">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # Small print
    st.markdown("""
    <div style="margin-top:2rem;font-family:'Lora',serif;font-size:0.7rem;
                font-style:italic;color:#B8AD9E;line-height:1.7">
        For self-reflection only.<br>Not a medical device.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  HISTORY DETAIL PAGE GATE
#  If a history entry was clicked, show its detail page instead of
#  the main app. The back button returns to the main view.
# ══════════════════════════════════════════════════════════════════════
if st.session_state.get('show_history_detail'):
    idx     = st.session_state.get('history_detail_idx', 0)
    history = st.session_state.get('history', [])

    if 0 <= idx < len(history):
        render_history_detail(history[idx])
    else:
        # Index out of range (history was cleared) — reset
        st.session_state['show_history_detail'] = False
        st.session_state.pop('history_detail_idx', None)
        st.rerun()

    st.stop()   # Nothing below renders while detail page is open

# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

# Masthead
st.markdown("""
<div class="masthead">
    <div class="masthead-eyebrow">Mental health awareness tool</div>
    <div class="masthead-title">Mind<em>Track</em> AI</div>
    <div class="masthead-rule">
        <div class="masthead-rule-line"></div>
        <div class="masthead-rule-dot"></div>
        <div class="masthead-rule-line"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Offline banner
if not api_ok:
    st.markdown("""
    <div class="offline-banner">
        <div class="offline-title">Backend unreachable</div>
        <div class="offline-body">
            Start the Flask API first —
            <span class="offline-code">cd app/backend &amp;&amp; python app.py</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────
tab_text, tab_audio = st.tabs(["  Written entry  ", "  Voice recording  "])


# ══════════════════════════════════════════════════════════════════════
#  TAB 1 — TEXT
# ══════════════════════════════════════════════════════════════════════
with tab_text:

    st.markdown("""
    <div class="section-label">Your entry</div>
    <div style="font-family:'Lora',serif;font-style:italic;font-size:0.9rem;
                color:#8C8070;line-height:1.7;margin-bottom:1rem">
        Write openly about how you have been feeling.
        There are no right or wrong answers.
    </div>
    """, unsafe_allow_html=True)

    text_input = st.text_area(
        label            = "Your entry",
        placeholder      = "Today I feel…",
        height           = 180,
        key              = "text_input",
        label_visibility = "collapsed",
    )

    # Character counter
    MAX_CHARS   = 2000
    char_count  = len(text_input) if text_input else 0
    char_class  = 'char-error' if char_count > MAX_CHARS else \
                  'char-warn'  if char_count > MAX_CHARS * 0.85 else ''

    st.markdown(
        f'<div class="char-count {char_class}">'
        f'{char_count} / {MAX_CHARS}</div>',
        unsafe_allow_html=True
    )

    col_btn, col_clr = st.columns([4, 1])
    with col_btn:
        run_text = st.button(
            "Analyse entry",
            key      = "btn_text",
            type     = "primary",
            disabled = not api_ok,
        )
    with col_clr:
        if st.button("Clear", key="clr_text", type="secondary"):
            st.session_state.text_result = None
            st.rerun()

    # Validation & prediction
    if run_text:
        stripped = (text_input or '').strip()
        if not stripped:
            st.markdown(
                '<div class="inline-warn">Please write something first.</div>',
                unsafe_allow_html=True
            )
        elif len(stripped) < 5:
            st.markdown(
                '<div class="inline-warn">'
                'A little more detail helps — try a sentence or two.'
                '</div>',
                unsafe_allow_html=True
            )
        elif char_count > MAX_CHARS:
            st.markdown(
                f'<div class="inline-warn">'
                f'Please shorten your entry to under {MAX_CHARS} characters.'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            with st.spinner("Reading…"):
                try:
                    result = predict_text(text_input)
                    st.session_state.text_result = result
                    add_to_history(
                        preview     = text_input,
                        risk        = result['risk_level'],
                        modality    = 'text',
                        confidence  = result['confidence'],
                        full_result = result,
                    )
                    st.rerun()
                except requests.ConnectionError:
                    st.error("Cannot reach the backend. Is Flask running?")
                except requests.HTTPError as e:
                    msg = (e.response.json().get('message', str(e))
                           if e.response else str(e))
                    st.error(f"API error: {msg}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

    if st.session_state.text_result:
        render_result(st.session_state.text_result, modality='text')


# ══════════════════════════════════════════════════════════════════════
#  TAB 2 — AUDIO
# ══════════════════════════════════════════════════════════════════════
with tab_audio:

    from components.audio_recorder import render_live_recorder

    # ── Mode toggle ───────────────────────────────────────────────────
    audio_mode = st.session_state.get('audio_mode', 'live')

    mcol1, mcol2 = st.columns(2)
    with mcol1:
        if st.button(
            "Record live",
            key  = "mode_live",
            type = "primary" if audio_mode == 'live' else "secondary",
            use_container_width = True,
        ):
            if audio_mode != 'live':
                st.session_state['audio_mode']      = 'live'
                st.session_state['live_wav']        = None
                st.session_state['live_transcript'] = None
                st.session_state.audio_result       = None
                st.rerun()

    with mcol2:
        if st.button(
            "Upload file",
            key  = "mode_upload",
            type = "primary" if audio_mode == 'upload' else "secondary",
            use_container_width = True,
        ):
            if audio_mode != 'upload':
                st.session_state['audio_mode']      = 'upload'
                st.session_state['live_wav']        = None
                st.session_state['live_transcript'] = None
                st.session_state.audio_result       = None
                st.rerun()

    st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────
    #  LIVE RECORDING MODE
    # ─────────────────────────────────────────────────────────────────
    if audio_mode == 'live':

        # render_live_recorder handles all recording state internally.
        # It sets auto_analyse_audio=True when recording stops.
        render_live_recorder()

        ready_bytes = st.session_state.get('live_wav')
        ready_text  = st.session_state.get('live_transcript', '')

        # ── Auto-analyse (triggered when recording stops) ─────────────
        auto = st.session_state.pop('auto_analyse_audio', False)

        if auto and ready_bytes and api_ok:
            with st.spinner("Analysing your recording…"):
                try:
                    result = predict_audio(ready_bytes, "live_recording.wav")
                    st.session_state.audio_result = result
                    preview = (f"[Live] {ready_text[:55]}"
                               if ready_text else "[Live mic] recording")
                    add_to_history(
                        preview     = preview,
                        risk        = result['risk_level'],
                        modality    = 'audio',
                        confidence  = result['confidence'],
                        full_result = result,
                    )
                    # Clear recording so next session starts fresh
                    for k in ['live_wav', 'live_transcript', 'live_duration']:
                        st.session_state.pop(k, None)
                    st.rerun()

                except requests.ConnectionError:
                    st.error("Cannot reach the backend. Is Flask running?")
                except requests.HTTPError as e:
                    body = e.response.json() if e.response else {}
                    st.error(f"API error: {body.get('message', str(e))}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

        # Manual clear button (only visible when a recording exists)
        if ready_bytes:
            if st.button("Clear recording", key="clr_live", type="secondary"):
                for k in ['live_wav', 'live_transcript', 'live_duration',
                          'auto_analyse_audio', '_rl_was_recording',
                          '_rl_finalised']:
                    st.session_state.pop(k, None)
                if 'live_transcriber' in st.session_state:
                    st.session_state['live_transcriber'].reset()
                st.session_state.audio_result = None
                st.rerun()

    # ─────────────────────────────────────────────────────────────────
    #  UPLOAD MODE
    # ─────────────────────────────────────────────────────────────────
    else:

        st.markdown("""
        <div style="font-family:'Lora',serif;font-style:italic;font-size:.88rem;
                    color:#4E342E;line-height:1.7;margin-bottom:.75rem">
            WAV or MP3, maximum 10 MB, at least 0.5 seconds.
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            label            = "Upload recording",
            type             = ['wav', 'mp3'],
            key              = "audio_file",
            label_visibility = "collapsed",
        )

        if uploaded:
            size_kb = uploaded.size // 1024
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:.62rem;'
                f'letter-spacing:1px;text-transform:uppercase;color:#5D4037;'
                f'margin-bottom:.4rem">'
                f'{uploaded.name} &nbsp;&middot;&nbsp; {size_kb} KB'
                f'</div>',
                unsafe_allow_html=True
            )
            st.audio(uploaded, format='audio/wav')

        ucol1, ucol2 = st.columns([4, 1])
        with ucol1:
            run_upload = st.button(
                "Analyse file",
                key      = "btn_upload",
                type     = "primary",
                disabled = not api_ok or uploaded is None,
                use_container_width = True,
            )
        with ucol2:
            if st.button("Clear", key="clr_upload", type="secondary"):
                st.session_state.audio_result = None
                st.rerun()

        if run_upload and uploaded:
            with st.spinner("Processing audio…"):
                try:
                    uploaded.seek(0)
                    result = predict_audio(uploaded.read(), uploaded.name)
                    st.session_state.audio_result = result
                    add_to_history(
                        preview     = f"[Upload] {uploaded.name}",
                        risk        = result['risk_level'],
                        modality    = 'audio',
                        confidence  = result['confidence'],
                        full_result = result,
                    )
                    st.rerun()
                except requests.ConnectionError:
                    st.error("Cannot reach the backend. Is Flask running?")
                except requests.HTTPError as e:
                    body = e.response.json() if e.response else {}
                    st.error(f"API error: {body.get('message', str(e))}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

    # ── Shared result display (both modes) ────────────────────────────
    if st.session_state.audio_result:
        render_result(st.session_state.audio_result, modality='audio')

# ── Disclaimer ────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    <div class="disclaimer-text">
        <strong>Important.</strong> MindTrack AI is a self-reflection tool
        and does not constitute medical advice, diagnosis, or treatment.
        All outputs are statistical estimates. If you are in distress,
        please speak with a qualified mental health professional or
        contact a crisis line in your region.
    </div>
</div>
""", unsafe_allow_html=True)