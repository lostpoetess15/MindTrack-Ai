# ══════════════════════════════════════════════════════
#  Auth forms — login and registration UI components
#  Matches the warm editorial aesthetic of Phase 8
# ══════════════════════════════════════════════════════
import streamlit as st
import requests
from utils.api_client import login, register

AUTH_CSS = """
<style>
.auth-wrap {
    max-width: 420px;
    margin: 3rem auto 0;
}
.auth-masthead {
    text-align: center;
    margin-bottom: 2.5rem;
    border-bottom: 1.5px solid #1C1916;
    padding-bottom: 1.2rem;
}
.auth-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 400;
    color: #1C1916;
    letter-spacing: -0.5px;
}
.auth-title em { font-style: italic; color: #B85C38; }
.auth-subtitle {
    font-family: 'Lora', serif;
    font-size: 0.9rem;
    font-style: italic;
    color: #8C8070;
    margin-top: 0.3rem;
}
.auth-tab-row {
    display: flex;
    border-bottom: 1px solid #D8CFC2;
    margin-bottom: 1.75rem;
}
.auth-tab {
    flex: 1;
    text-align: center;
    padding: 0.65rem 0;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #B8AD9E;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
}
.auth-tab.active {
    color: #1C1916;
    border-bottom-color: #B85C38;
}
.auth-field-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #8C8070;
    margin-bottom: 0.4rem;
    display: block;
}
.auth-error {
    font-family: 'Lora', serif;
    font-size: 0.85rem;
    font-style: italic;
    color: #B85C38;
    padding: 0.6rem 0.8rem;
    background: #F5E8DF;
    border-left: 2.5px solid #B85C38;
    border-radius: 0 3px 3px 0;
    margin-bottom: 1rem;
}
.auth-success {
    font-family: 'Lora', serif;
    font-size: 0.85rem;
    font-style: italic;
    color: #4A7055;
    padding: 0.6rem 0.8rem;
    background: #EAF2E8;
    border-left: 2.5px solid #4A7055;
    border-radius: 0 3px 3px 0;
    margin-bottom: 1rem;
}
.auth-hint {
    font-family: 'Lora', serif;
    font-size: 0.78rem;
    font-style: italic;
    color: #B8AD9E;
    margin-top: 0.35rem;
    line-height: 1.5;
}
.auth-divider {
    height: 1px;
    background: #EAE4DA;
    margin: 1.5rem 0;
}
</style>
"""


def render_auth_page():
    """
    Full-page auth component. Shows login or register form.
    On success: stores token + user in st.session_state and triggers rerun.
    """
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    # Init tab state
    if 'auth_tab' not in st.session_state:
        st.session_state.auth_tab = 'login'

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:

        # Masthead
        st.markdown("""
        <div class="auth-masthead">
            <div class="auth-title">Mind<em>Track</em> AI</div>
            <div class="auth-subtitle">Mental health risk awareness tool</div>
        </div>
        """, unsafe_allow_html=True)

        # Tab switcher
        tab_cols = st.columns(2)
        with tab_cols[0]:
            if st.button("Sign in",
                         key      = "tab_login",
                         type     = "primary" if st.session_state.auth_tab == 'login' else "secondary",
                         use_container_width = True):
                st.session_state.auth_tab = 'login'
                st.rerun()
        with tab_cols[1]:
            if st.button("Create account",
                         key      = "tab_register",
                         type     = "primary" if st.session_state.auth_tab == 'register' else "secondary",
                         use_container_width = True):
                st.session_state.auth_tab = 'register'
                st.rerun()

        st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)

        # ── LOGIN FORM ─────────────────────────────────────────────────
        if st.session_state.auth_tab == 'login':
            _render_login_form()

        # ── REGISTER FORM ──────────────────────────────────────────────
        else:
            _render_register_form()

        # Disclaimer
        st.markdown("""
        <div style="margin-top:2rem;text-align:center;font-family:'Lora',serif;
                    font-size:0.72rem;font-style:italic;color:#B8AD9E;line-height:1.8">
            For self-reflection only.<br>Not a medical device or diagnostic tool.
        </div>
        """, unsafe_allow_html=True)


def _render_login_form():
    if 'login_error' not in st.session_state:
        st.session_state.login_error = ''

    with st.form("login_form", clear_on_submit=False):
        st.markdown('<span class="auth-field-label">Email address</span>',
                    unsafe_allow_html=True)
        email = st.text_input(
            label            = "Email",
            placeholder      = "your@email.com",
            label_visibility = "collapsed",
            key              = "login_email",
        )

        st.markdown('<span class="auth-field-label">Password</span>',
                    unsafe_allow_html=True)
        password = st.text_input(
            label            = "Password",
            type             = "password",
            placeholder      = "········",
            label_visibility = "collapsed",
            key              = "login_password",
        )

        st.markdown('<div style="margin-top:0.75rem"></div>',
                    unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Sign in",
            use_container_width = True,
            type = "primary",
        )

    if st.session_state.login_error:
        st.markdown(
            f'<div class="auth-error">{st.session_state.login_error}</div>',
            unsafe_allow_html=True
        )

    if submitted:
        st.session_state.login_error = ''
        email    = (email or '').strip().lower()
        password = (password or '').strip()

        if not email or not password:
            st.session_state.login_error = "Please fill in both fields."
            st.rerun()
            return

        try:
            data = login(email, password)
            _store_auth(data)
        except requests.HTTPError as e:
            body = e.response.json() if e.response else {}
            st.session_state.login_error = body.get(
                'message', 'Login failed. Please try again.'
            )
            st.rerun()
        except requests.ConnectionError:
            st.session_state.login_error = (
                "Cannot reach the server. Is Flask running?"
            )
            st.rerun()


def _render_register_form():
    if 'reg_error' not in st.session_state:
        st.session_state.reg_error = ''

    with st.form("register_form", clear_on_submit=False):
        st.markdown('<span class="auth-field-label">Display name (optional)</span>',
                    unsafe_allow_html=True)
        display_name = st.text_input(
            label            = "Display name",
            placeholder      = "How should we address you?",
            label_visibility = "collapsed",
            key              = "reg_name",
        )

        st.markdown('<span class="auth-field-label">Email address</span>',
                    unsafe_allow_html=True)
        email = st.text_input(
            label            = "Email",
            placeholder      = "your@email.com",
            label_visibility = "collapsed",
            key              = "reg_email",
        )

        st.markdown('<span class="auth-field-label">Password</span>',
                    unsafe_allow_html=True)
        password = st.text_input(
            label            = "Password",
            type             = "password",
            placeholder      = "Min 8 chars, 1 uppercase, 1 digit",
            label_visibility = "collapsed",
            key              = "reg_password",
        )
        st.markdown(
            '<div class="auth-hint">8+ characters &nbsp;·&nbsp; '
            'one uppercase letter &nbsp;·&nbsp; one digit</div>',
            unsafe_allow_html=True
        )

        st.markdown('<div style="margin-top:0.75rem"></div>',
                    unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Create account",
            use_container_width = True,
            type = "primary",
        )

    if st.session_state.reg_error:
        st.markdown(
            f'<div class="auth-error">{st.session_state.reg_error}</div>',
            unsafe_allow_html=True
        )

    if submitted:
        st.session_state.reg_error = ''
        email        = (email        or '').strip().lower()
        password     = (password     or '').strip()
        display_name = (display_name or '').strip()

        if not email or not password:
            st.session_state.reg_error = "Email and password are required."
            st.rerun()
            return

        try:
            data = register(email, password, display_name)
            _store_auth(data)
        except requests.HTTPError as e:
            body = e.response.json() if e.response else {}
            st.session_state.reg_error = body.get(
                'message', 'Registration failed. Please try again.'
            )
            st.rerun()
        except requests.ConnectionError:
            st.session_state.reg_error = (
                "Cannot reach the server. Is Flask running?"
            )
            st.rerun()


def _store_auth(data: dict):
    """
    Saves token + user to session state, then immediately loads
    the user's prediction history from the database so it appears
    in the sidebar on first render after login.
    """
    st.session_state.token        = data['token']
    st.session_state.current_user = data['user']
    st.session_state.auth_tab     = 'login'
    st.session_state.text_result  = None
    st.session_state.audio_result = None

    # ── Load history from database ────────────────────────────────────
    # get_history() hits GET /auth/history which reads from the
    # predictions table — all entries are there from previous sessions.
    try:
        from utils.api_client import get_history as _get_history
        response = _get_history(page=1, limit=20)
        raw      = response.get('predictions', [])

        # Convert DB format → session history format so render_history()
        # can display it without any changes
        loaded = []
        for p in raw:
            # Parse ISO timestamp → HH:MM display
            try:
                from datetime import datetime
                ts   = p.get('created_at', '')
                time = datetime.fromisoformat(
                    ts.replace('Z', '+00:00')
                ).strftime('%H:%M')
            except Exception:
                time = '--:--'

            loaded.append({
                'preview'   : p.get('input_preview') or f"[{p.get('modality','?')}]",
                'risk'      : p.get('risk_level', 'Unknown'),
                'modality'  : p.get('modality', 'text'),
                'confidence': p.get('confidence', 0.0),
                'time'      : time,
            })

        st.session_state.history = loaded

    except Exception as e:
        # Never block login because history failed to load
        import logging
        logging.getLogger(__name__).warning(f"Could not load history: {e}")
        st.session_state.history = []

    st.rerun()