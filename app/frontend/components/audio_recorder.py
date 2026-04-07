# ══════════════════════════════════════════════════════════════════════
#  audio_recorder.py  — Production version with accurate analysis
#
#  Key fixes:
#    1. Pre-emphasis filter → boosts emotional vocal features
#    2. Minimum 2s recording enforcement → enough data for MFCCs
#    3. Amplitude guard → warns if microphone is too quiet
#    4. Clean WAV output → no double-normalization with backend
#    5. Transcript exposed for text-model fallback in app.py
# ══════════════════════════════════════════════════════════════════════

from __future__ import annotations

import io
import logging
import threading
import time
import wave
from typing import List, Optional, Tuple

import av
import librosa
import numpy as np
import speech_recognition as sr
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

log = logging.getLogger(__name__)

# ── Constants — must match Phase 3 preprocessing exactly ─────────────
TARGET_SR      = 22_050
TARGET_RMS     = 0.1
TRIM_TOP_DB    = 20
CHUNK_S        = 4.0
MIN_DUR_S      = 2.0      # raised from 0.5 — MFCC needs at least 2s
MAX_DUR_S      = 30.0
PRE_EMPHASIS   = 0.97     # standard pre-emphasis coefficient for speech
MIN_RMS        = 0.001    # below this = microphone too quiet to analyse

_FALLBACK_SR = 48_000
RTC_CONFIG   = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}


RECORDER_CSS = """
<style>
div[data-testid="stVerticalBlock"] button {
    background    : #1C1916 !important; color: #FAF7F2 !important;
    border        : 1.5px solid #1C1916 !important;
    border-radius : 3px !important;
    font-family   : 'DM Mono', monospace !important;
    font-size     : 0.72rem !important; letter-spacing: 1.5px !important;
    text-transform: uppercase !important; padding: 0.6rem 1.5rem !important;
    cursor: pointer !important; transition: background 0.15s !important;
}
div[data-testid="stVerticalBlock"] button:hover {
    background: #3D3830 !important; border-color: #3D3830 !important;
}
.rl-label {
    font-family: 'DM Mono', monospace; font-size: 0.6rem;
    letter-spacing: 2px; text-transform: uppercase;
    color: #5D4037; margin-bottom: 0.55rem; display: block;
}
.rl-hint {
    font-family: 'Lora', serif; font-style: italic;
    font-size: 0.88rem; color: #4E342E;
    line-height: 1.65; margin: 0.4rem 0 0.9rem;
}
@keyframes rl-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(1.35); }
}
.rl-listening-row {
    display: flex; align-items: center; gap: 8px; margin: 0.7rem 0 0.45rem;
}
.rl-pulse-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #B85C38; flex-shrink: 0;
    animation: rl-pulse 1.1s ease-in-out infinite;
}
.rl-listening-label {
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: #B85C38; font-weight: 500;
}
.rl-live-panel {
    background: #FFF8F5; border: 1px solid #D7CCC8;
    border-left: 3px solid #B85C38; border-radius: 0 4px 4px 0;
    padding: 0.9rem 1.1rem; min-height: 72px; margin-top: 0.4rem;
}
.rl-panel-label {
    font-family: 'DM Mono', monospace; font-size: 0.58rem;
    letter-spacing: 2px; text-transform: uppercase;
    color: #8D6E63; margin-bottom: 0.4rem; display: block;
}
.rl-live-text {
    font-family: 'Lora', serif; font-style: italic;
    font-size: 1rem; color: #1C1916; line-height: 1.78;
}
.rl-waiting-text {
    font-family: 'Lora', serif; font-style: italic;
    font-size: 0.9rem; color: #A1887F; line-height: 1.65;
}
.rl-final-panel {
    background: #F1F8F4; border: 1px solid #C8D8C4;
    border-left: 3px solid #4A7055; border-radius: 0 4px 4px 0;
    padding: 0.9rem 1.1rem; margin-top: 0.75rem;
}
.rl-final-label {
    font-family: 'DM Mono', monospace; font-size: 0.58rem;
    letter-spacing: 2px; text-transform: uppercase;
    color: #4A7055; margin-bottom: 0.4rem; display: block;
}
.rl-final-text {
    font-family: 'Lora', serif; font-style: italic;
    font-size: 1rem; color: #1C1916; line-height: 1.78;
}
.rl-ok-row {
    display: flex; align-items: center; gap: 7px; margin-top: 0.55rem;
}
.rl-ok-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #4A7055; flex-shrink: 0;
}
.rl-ok-text {
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    letter-spacing: 1.2px; text-transform: uppercase; color: #4A7055;
}
.rl-err-text {
    font-family: 'Lora', serif; font-style: italic;
    font-size: 0.85rem; color: #B71C1C; margin-top: 0.45rem;
}
.rl-warn-text {
    font-family: 'Lora', serif; font-style: italic;
    font-size: 0.85rem; color: #C07820; margin-top: 0.45rem;
}
.rl-audio-label {
    font-family: 'DM Mono', monospace; font-size: 0.6rem;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: #5D4037; margin: 0.65rem 0 0.3rem; display: block;
}
.rl-sr-badge {
    font-family: 'DM Mono', monospace; font-size: 0.58rem;
    letter-spacing: 1px; color: #8D6E63; margin-top: 0.3rem;
}
.rl-timer {
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    letter-spacing: 1px; color: #B85C38; margin-top: 0.3rem;
}
</style>
"""


def _inject_css():
    if not st.session_state.get('_rl_css_done'):
        st.markdown(RECORDER_CSS, unsafe_allow_html=True)
        st.session_state['_rl_css_done'] = True


def _esc(text: str) -> str:
    return (text.replace('&', '&amp;').replace('<', '&lt;')
                .replace('>', '&gt;').replace('"', '&quot;'))


def _listening_panel(live_text: str, duration: float) -> str:
    dur_str  = f"{duration:.0f}s" if duration >= 1 else "..."
    min_note = "" if duration >= MIN_DUR_S else (
        f" &nbsp;&middot;&nbsp; speak for at least {MIN_DUR_S:.0f}s"
    )
    if live_text:
        body = (f'<span class="rl-panel-label">What we heard so far</span>'
                f'<div class="rl-live-text">&ldquo;{_esc(live_text)}&rdquo;</div>')
    else:
        body = '<div class="rl-waiting-text">Your words will appear here&hellip;</div>'
    return f"""
    <div class="rl-listening-row">
        <div class="rl-pulse-dot"></div>
        <div class="rl-listening-label">Recording &mdash; speak now</div>
    </div>
    <div class="rl-timer">{dur_str}{min_note}</div>
    <div class="rl-live-panel">{body}</div>
    """


def _final_panel(text: str) -> str:
    if not text:
        return ''
    return f"""
    <div class="rl-final-panel">
        <span class="rl-final-label">What we heard</span>
        <div class="rl-final-text">&ldquo;{_esc(text)}&rdquo;</div>
    </div>
    """


def _ok_status(duration: float, actual_sr: int) -> str:
    return f"""
    <div class="rl-ok-row">
        <div class="rl-ok-dot"></div>
        <div class="rl-ok-text">Recording ready &nbsp;&middot;&nbsp; {duration:.1f}s</div>
    </div>
    <div class="rl-sr-badge">
        captured at {actual_sr:,} Hz &rarr; resampled to {TARGET_SR:,} Hz
    </div>
    """


def _err_status(msg: str) -> str:
    return f'<div class="rl-err-text">{_esc(msg)}</div>'


def _warn_status(msg: str) -> str:
    return f'<div class="rl-warn-text">{_esc(msg)}</div>'


def _float32_to_wav(audio: np.ndarray, sample_rate: int) -> bytes:
    """Convert float32 [-1, 1] → 16-bit PCM WAV bytes."""
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _apply_pre_emphasis(audio: np.ndarray, coeff: float = PRE_EMPHASIS) -> np.ndarray:
    """
    Apply pre-emphasis filter to boost high-frequency vocal features.

    Speech emotion is heavily encoded in high-frequency spectral content
    (fricatives, consonant transitions, pitch harmonics). RAVDESS training
    data was recorded in a controlled environment where these features are
    prominent. Live WebRTC audio often has them dampened.

    Pre-emphasis: y[n] = x[n] - coeff * x[n-1]
    This is the same filter applied in many MFCC implementations before
    computing the filterbank energies. Applying it explicitly here ensures
    consistency with the training pipeline regardless of microphone quality.

    Standard coefficient: 0.97 (used in HTK, Kaldi, librosa default).
    """
    if len(audio) < 2:
        return audio
    return np.append(audio[0], audio[1:] - coeff * audio[:-1]).astype(np.float32)


# ══════════════════════════════════════════════════════════════════════
#  LiveTranscriber
# ══════════════════════════════════════════════════════════════════════

class LiveTranscriber:
    """
    Thread-safe audio accumulator with chunked speech-to-text.
    Uses PyAV AudioResampler to handle all sample-rate and format
    conversion at the C level (fast, pitch-accurate).
    """

    def __init__(self):
        self._lock              = threading.Lock()
        self._all_frames:  List[np.ndarray] = []
        self._chunk_frames: List[np.ndarray] = []
        self._parts:        List[str]        = []
        self._sample_count  = 0
        self._busy          = False
        self._recognizer    = sr.Recognizer()
        self._actual_sr: int = _FALLBACK_SR

        # PyAV C-level resampler → correct pitch, mono, TARGET_SR
        self.resampler = av.AudioResampler(
            format = 'flt',
            layout = 'mono',
            rate   = TARGET_SR,
        )

    def add_frame(self, frame: av.AudioFrame):
        try:
            with self._lock:
                self._actual_sr = frame.sample_rate

            resampled_frames = self.resampler.resample(frame)

            for r_frame in resampled_frames:
                arr = r_frame.to_ndarray().flatten().astype(np.float32)

                with self._lock:
                    self._all_frames.append(arr)
                    self._chunk_frames.append(arr)
                    self._sample_count += len(arr)

                    if (self._sample_count >= int(TARGET_SR * CHUNK_S)
                            and not self._busy):
                        chunk              = np.concatenate(self._chunk_frames)
                        self._chunk_frames = []
                        self._sample_count = 0
                        self._busy         = True
                        threading.Thread(
                            target = self._transcribe,
                            args   = (chunk,),
                            daemon = True,
                        ).start()

        except Exception as exc:
            log.debug(f"add_frame skipped: {exc}")

    def _transcribe(self, audio: np.ndarray):
        try:
            wav = _float32_to_wav(audio, TARGET_SR)
            with sr.AudioFile(io.BytesIO(wav)) as src:
                audio_data = self._recognizer.record(src)
            text = self._recognizer.recognize_google(
                audio_data, language='en-IN'
            )
            if text.strip():
                with self._lock:
                    self._parts.append(text.strip())
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            log.warning(f"Google STT request error: {e}")
        except Exception as e:
            log.debug(f"Transcription error: {e}")
        finally:
            with self._lock:
                self._busy = False

    def get_live_transcript(self) -> str:
        with self._lock:
            return ' '.join(self._parts)

    def get_actual_sr(self) -> int:
        with self._lock:
            return self._actual_sr

    def get_duration(self) -> float:
        with self._lock:
            n = sum(len(f) for f in self._all_frames)
        return n / TARGET_SR

    def get_rms(self) -> float:
        """Raw RMS before any normalization — used to detect quiet mics."""
        with self._lock:
            if not self._all_frames:
                return 0.0
            audio = np.concatenate(self._all_frames)
        return float(np.sqrt(np.mean(audio ** 2)))

    def get_full_wav(self) -> bytes:
        """
        Builds the final WAV for the ML pipeline.

        Processing chain (matches Phase 3 exactly):
          1. Pre-emphasis filter  → boosts high-freq emotional features
          2. Trim silence         → top_db=20 (Phase 3 value)
          3. RMS normalise        → 0.1 (Phase 3 value)

        Note: the backend audio_pipeline.py also normalises, but that
        second pass is a no-op since RMS is already at target.
        The pre-emphasis is the critical addition for live audio accuracy.
        """
        with self._lock:
            if not self._all_frames:
                return b''
            audio = np.concatenate(self._all_frames)

        log.info(f"get_full_wav: {len(audio)} samples, "
                 f"dur={len(audio)/TARGET_SR:.1f}s, "
                 f"raw_rms={np.sqrt(np.mean(audio**2)):.4f}")

        # 1. Pre-emphasis — critical for matching RAVDESS MFCC distribution
        audio = _apply_pre_emphasis(audio)

        # 2. Trim silence (matches Phase 3)
        audio, _ = librosa.effects.trim(audio, top_db=TRIM_TOP_DB)

        # Safety net: pure silence after trim
        if len(audio) == 0:
            audio = np.zeros(int(TARGET_SR * 0.5), dtype=np.float32)

        # 3. RMS normalise (matches Phase 3)
        rms = np.sqrt(np.mean(audio ** 2))
        if rms > 0.0:
            audio = audio * (TARGET_RMS / rms)

        audio = np.clip(audio, -1.0, 1.0)

        log.info(f"get_full_wav: final rms={np.sqrt(np.mean(audio**2)):.4f}, "
                 f"samples={len(audio)}")

        return _float32_to_wav(audio, TARGET_SR)

    def finalise_transcript(self, wav_bytes: bytes) -> str:
        existing = self.get_live_transcript()
        if existing:
            return existing
        try:
            rec = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(wav_bytes)) as src:
                audio_data = rec.record(src)
            return rec.recognize_google(audio_data, language='en-IN')
        except Exception:
            return ''

    def reset(self):
        with self._lock:
            self._all_frames.clear()
            self._chunk_frames.clear()
            self._parts.clear()
            self._sample_count = 0
            self._busy         = False


# ══════════════════════════════════════════════════════════════════════
#  Public component
# ══════════════════════════════════════════════════════════════════════

def render_live_recorder() -> Tuple[Optional[bytes], str]:
    _inject_css()

    if 'live_transcriber' not in st.session_state:
        st.session_state['live_transcriber'] = LiveTranscriber()

    transcriber: LiveTranscriber = st.session_state['live_transcriber']

    st.markdown("""
    <span class="rl-label">Live microphone</span>
    <div class="rl-hint">
        Click <strong>Start recording</strong> to begin.
        Speak naturally for at least 2 seconds — your words appear below.
        Click <strong>Stop recording</strong> when finished.
        Analysis begins automatically.
    </div>
    """, unsafe_allow_html=True)

    ctx = webrtc_streamer(
        key                      = "mindtrack-live",
        mode                     = WebRtcMode.SENDONLY,
        rtc_configuration        = RTC_CONFIG,
        media_stream_constraints = {
            "video": False,
            "audio": {
                "echoCancellation": False,
                "noiseSuppression": False,
                "autoGainControl" : False,
            }
        },
        audio_frame_callback = transcriber.add_frame,
        async_processing     = True,
        translations         = {
            "start": "Start recording",
            "stop" : "Stop recording",
        },
    )

    transcript_slot = st.empty()
    is_playing      = ctx.state.playing

    # ── RECORDING ────────────────────────────────────────────────────
    if is_playing:
        live_text = transcriber.get_live_transcript()
        duration  = transcriber.get_duration()
        transcript_slot.markdown(
            _listening_panel(live_text, duration),
            unsafe_allow_html=True
        )
        st.session_state['_rl_was_recording'] = True
        st.session_state['_rl_finalised']     = False
        time.sleep(0.8)
        st.rerun()
        return None, ''

    # ── JUST STOPPED ─────────────────────────────────────────────────
    if (not is_playing
            and st.session_state.get('_rl_was_recording')
            and not st.session_state.get('_rl_finalised')):

        st.session_state['_rl_was_recording'] = False
        st.session_state['_rl_finalised']     = True

        duration  = transcriber.get_duration()
        actual_sr = transcriber.get_actual_sr()
        raw_rms   = transcriber.get_rms()

        log.info(f"Stopped: {duration:.1f}s @ {actual_sr}Hz, rms={raw_rms:.4f}")

        # ── Minimum duration guard ─────────────────────────────────────
        if duration < MIN_DUR_S:
            transcript_slot.markdown(
                _err_status(
                    f"Recording too short ({duration:.1f}s). "
                    f"Please speak for at least {MIN_DUR_S:.0f} seconds "
                    f"for accurate analysis."
                ),
                unsafe_allow_html=True
            )
            transcriber.reset()
            return None, ''

        # ── Maximum duration guard ─────────────────────────────────────
        if duration > MAX_DUR_S:
            transcript_slot.markdown(
                _err_status(f"Too long ({duration:.0f}s). Max is {int(MAX_DUR_S)}s."),
                unsafe_allow_html=True
            )
            transcriber.reset()
            return None, ''

        # ── Quiet microphone warning ───────────────────────────────────
        # Store warning but don't block — analysis can still run
        if raw_rms < MIN_RMS:
            st.session_state['_rl_quiet_warning'] = True
            log.warning(f"Microphone very quiet: rms={raw_rms:.5f}")
        else:
            st.session_state.pop('_rl_quiet_warning', None)

        with st.spinner("Processing audio…"):
            wav_bytes = transcriber.get_full_wav()

        with st.spinner("Finishing transcription…"):
            transcript = transcriber.finalise_transcript(wav_bytes)

        st.session_state['live_wav']           = wav_bytes
        st.session_state['live_transcript']    = transcript
        st.session_state['live_duration']      = duration
        st.session_state['live_actual_sr']     = actual_sr
        st.session_state['live_raw_rms']       = raw_rms
        st.session_state['auto_analyse_audio'] = True

        transcriber.reset()
        st.rerun()
        return wav_bytes, transcript

    # ── IDLE ─────────────────────────────────────────────────────────
    if not is_playing:
        st.session_state['_rl_finalised'] = False

    prev_wav        = st.session_state.get('live_wav')
    prev_transcript = st.session_state.get('live_transcript', '')
    prev_dur        = st.session_state.get('live_duration', 0.0)
    prev_sr         = st.session_state.get('live_actual_sr', _FALLBACK_SR)

    if prev_wav:
        st.markdown(_ok_status(prev_dur, prev_sr), unsafe_allow_html=True)
        # Quiet mic warning
        if st.session_state.get('_rl_quiet_warning'):
            st.markdown(
                _warn_status(
                    "Your microphone seems very quiet. "
                    "Try speaking louder or moving closer. "
                    "Analysis will use the transcript if audio features are unclear."
                ),
                unsafe_allow_html=True
            )
        st.markdown('<span class="rl-audio-label">Playback</span>',
                    unsafe_allow_html=True)
        st.audio(prev_wav, format='audio/wav')

    if prev_transcript:
        transcript_slot.markdown(_final_panel(prev_transcript),
                                 unsafe_allow_html=True)
    else:
        transcript_slot.markdown("""
        <div class="rl-hint" style="margin-top:.3rem">
            Make sure your browser has microphone permission,
            then click <strong>Start recording</strong> above.
        </div>
        """, unsafe_allow_html=True)

    return prev_wav, prev_transcript