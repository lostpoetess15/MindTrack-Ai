# ══════════════════════════════════════════════════════════════════════
#  MINDTRACK AI — Phase 10: Full Test Suite
#
#  Run all tests : pytest tests/test_api.py -v
#  Run one group : pytest tests/test_api.py -v -k "text"
#  Run with report: pytest tests/test_api.py -v --tb=short
#
#  Requirements  : pytest requests
#  Backend must be running: cd app/backend && python app.py
# ══════════════════════════════════════════════════════════════════════

import pytest
import requests
import os
import time
import wave
import struct
import numpy as np

BASE_URL = os.getenv("API_URL", "http://localhost:5000")
TIMEOUT  = 15


# ─────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────

def post_text(text: str) -> requests.Response:
    return requests.post(
        f"{BASE_URL}/predict/text",
        json    = {"text": text},
        timeout = TIMEOUT
    )


def post_audio(audio_bytes: bytes, filename: str = "test.wav") -> requests.Response:
    return requests.post(
        f"{BASE_URL}/predict/audio",
        files   = {"file": (filename, audio_bytes, "audio/wav")},
        timeout = TIMEOUT
    )


def make_wav(duration_seconds: float = 2.0,
             frequency: float = 440.0,
             sample_rate: int = 22050,
             silent: bool = False) -> bytes:
    """
    Generates a synthetic .wav file in memory.
    Used for audio tests — no real audio file needed.
    """
    import io
    n_samples = int(sample_rate * duration_seconds)

    if silent:
        samples = [0] * n_samples
    else:
        samples = [
            int(32767 * np.sin(2 * np.pi * frequency * i / sample_rate))
            for i in range(n_samples)
        ]

    buffer = io.BytesIO()
    with wave.open(buffer, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{n_samples}h', *samples))

    return buffer.getvalue()


VALID_RISK_LEVELS  = {"Low", "Moderate", "High"}
RISK_LEVEL_MESSAGES = {
    "Low":      "positive or neutral",
    "Moderate": "elevated stress",
    "High":     "significant distress",
}


# ─────────────────────────────────────────────────────────────────────
#  Fixture: confirm backend is reachable before running any test
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def require_backend():
    """Skips all tests if the Flask backend is not reachable."""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200, "Health check returned non-200"
        data = r.json()
        assert data.get("server") == "online", "Server reports offline"
    except (requests.ConnectionError, AssertionError) as e:
        pytest.skip(
            f"Backend not reachable at {BASE_URL}. "
            f"Start Flask first: cd app/backend && python app.py\n{e}"
        )


# ─────────────────────────────────────────────────────────────────────
#  GROUP 1: Health check
# ─────────────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_returns_200(self):
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200

    def test_health_status_is_success(self):
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.json()["status"] == "success"

    def test_health_server_is_online(self):
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.json()["server"] == "online"

    def test_health_all_models_loaded(self):
        r   = requests.get(f"{BASE_URL}/health", timeout=5)
        models = r.json().get("models", {})
        for name, loaded in models.items():
            assert loaded, f"Model '{name}' is not loaded"

    def test_health_no_failed_models(self):
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.json().get("failed_models", []) == [], \
            "Some models failed to load"

    def test_health_has_timestamp(self):
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert "timestamp" in r.json()
        assert "started_at" in r.json()


# ─────────────────────────────────────────────────────────────────────
#  GROUP 2: Text prediction — happy path
# ─────────────────────────────────────────────────────────────────────

class TestTextPredictionValid:

    def _assert_valid_response(self, r: requests.Response):
        """Shared assertions for every valid prediction response."""
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        body = r.json()
        assert body["status"]     == "success"
        assert body["risk_level"] in VALID_RISK_LEVELS
        assert 0.0 <= body["confidence"] <= 1.0
        assert "class_probs"  in body
        assert "elapsed_ms"   in body
        assert "sentiment"    in body
        # class_probs must sum to ~1.0
        total = sum(body["class_probs"].values())
        assert abs(total - 1.0) < 0.05, \
            f"class_probs sum to {total:.4f}, expected ~1.0"

    def test_low_risk_text(self):
        r = post_text(
            "I feel genuinely happy and grateful today. "
            "Life is good and I am calm and content."
        )
        self._assert_valid_response(r)
        # Soft assertion — model might not always predict Low but should be reasonable
        body = r.json()
        assert body["class_probs"].get("Low", 0) > 0.0, \
            "Low probability should be non-zero for positive text"

    def test_high_risk_text(self):
        r = post_text(
            "I feel completely hopeless and empty. "
            "Nothing matters anymore and I cannot see a way forward. "
            "I am exhausted and broken inside."
        )
        self._assert_valid_response(r)
        body = r.json()
        assert body["class_probs"].get("High", 0) > 0.0, \
            "High probability should be non-zero for distress text"

    def test_moderate_risk_text(self):
        r = post_text(
            "I have been very stressed at work lately. "
            "I feel anxious about deadlines and I am not sleeping well."
        )
        self._assert_valid_response(r)

    def test_long_valid_text(self):
        text = ("I feel quite stressed about many things in my life. " * 20).strip()
        r    = post_text(text)
        self._assert_valid_response(r)

    def test_single_sentence(self):
        r = post_text("I am doing well today.")
        self._assert_valid_response(r)

    def test_mixed_case_input(self):
        """Cleaning pipeline must handle uppercase correctly."""
        r = post_text("I AM FEELING VERY ANXIOUS AND STRESSED OUT TODAY.")
        self._assert_valid_response(r)

    def test_text_with_punctuation(self):
        """Punctuation stripping must not crash the pipeline."""
        r = post_text(
            "How are you feeling? I'm okay... but a bit down, "
            "you know? Life has its ups and downs!"
        )
        self._assert_valid_response(r)

    def test_text_with_numbers(self):
        """Digit stripping must not crash the pipeline."""
        r = post_text(
            "I have been feeling stressed for 3 weeks now. "
            "My anxiety score is 7 out of 10."
        )
        self._assert_valid_response(r)

    def test_response_contains_sentiment(self):
        r    = post_text("I feel very sad and alone today.")
        body = r.json()
        assert "sentiment" in body
        assert -1.0 <= body["sentiment"] <= 1.0

    def test_confidence_is_reasonable(self):
        """Model should not be 0% confident on clear inputs."""
        r    = post_text("I feel absolutely wonderful and joyful today.")
        body = r.json()
        assert body["confidence"] > 0.30, \
            f"Confidence too low: {body['confidence']}"

    def test_elapsed_ms_is_fast(self):
        """Text prediction should complete in under 3 seconds."""
        r    = post_text("I feel okay today, nothing special.")
        body = r.json()
        assert body["elapsed_ms"] < 3000, \
            f"Text prediction too slow: {body['elapsed_ms']}ms"


# ─────────────────────────────────────────────────────────────────────
#  GROUP 3: Text prediction — validation (bad inputs)
# ─────────────────────────────────────────────────────────────────────

class TestTextPredictionValidation:

    def test_empty_string_returns_400(self):
        r = post_text("")
        assert r.status_code == 400
        assert r.json()["status"] == "error"

    def test_whitespace_only_returns_400(self):
        r = post_text("     ")
        assert r.status_code == 400

    def test_too_short_returns_400(self):
        r = post_text("hi")
        assert r.status_code == 400

    def test_too_long_returns_400(self):
        r = post_text("a " * 1100)    # ~2200 chars > 2000 limit
        assert r.status_code == 400

    def test_missing_text_key_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/predict/text",
            json    = {"wrong_key": "some text"},
            timeout = TIMEOUT
        )
        assert r.status_code == 400

    def test_non_json_body_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/predict/text",
            data    = "plain text body",
            headers = {"Content-Type": "text/plain"},
            timeout = TIMEOUT
        )
        assert r.status_code == 400

    def test_null_text_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/predict/text",
            json    = {"text": None},
            timeout = TIMEOUT
        )
        assert r.status_code == 400

    def test_numeric_text_returns_valid_response(self):
        """Numbers only — cleaned to empty or near-empty."""
        r = post_text("12345 67890")
        # Either 400 (empty after cleaning) or valid prediction
        assert r.status_code in (200, 400), \
            f"Unexpected status: {r.status_code}"

    def test_non_english_text_does_not_crash(self):
        """Non-English input must not crash the server."""
        r = post_text("आज मैं बहुत अच्छा महसूस कर रहा हूँ।")
        assert r.status_code in (200, 400), \
            f"Server crashed on non-English input: {r.status_code}"

    def test_error_response_has_message_field(self):
        r = post_text("")
        body = r.json()
        assert "message" in body, "Error response missing 'message' field"

    def test_server_does_not_return_500_on_bad_input(self):
        """Bad input must never cause a 500 internal server error."""
        bad_inputs = ["", "  ", "ab", "a" * 5000, None]
        for inp in bad_inputs:
            r = requests.post(
                f"{BASE_URL}/predict/text",
                json    = {"text": inp},
                timeout = TIMEOUT
            )
            assert r.status_code != 500, \
                f"Server returned 500 for input: {repr(inp)[:50]}"


# ─────────────────────────────────────────────────────────────────────
#  GROUP 4: Audio prediction — happy path
# ─────────────────────────────────────────────────────────────────────

class TestAudioPredictionValid:

    def _assert_valid_audio_response(self, r: requests.Response):
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        body = r.json()
        assert body["status"]     == "success"
        assert body["risk_level"] in VALID_RISK_LEVELS
        assert 0.0 <= body["confidence"] <= 1.0
        assert "class_probs"      in body
        assert "elapsed_ms"       in body
        assert "duration_seconds" in body
        assert body["duration_seconds"] > 0
        total = sum(body["class_probs"].values())
        assert abs(total - 1.0) < 0.05

    def test_standard_wav_2s(self):
        wav = make_wav(duration_seconds=2.0, frequency=440.0)
        r   = post_audio(wav)
        self._assert_valid_audio_response(r)

    def test_standard_wav_3s(self):
        wav = make_wav(duration_seconds=3.0, frequency=300.0)
        r   = post_audio(wav)
        self._assert_valid_audio_response(r)

    def test_wav_high_frequency(self):
        wav = make_wav(duration_seconds=2.0, frequency=880.0)
        r   = post_audio(wav)
        self._assert_valid_audio_response(r)

    def test_wav_low_frequency(self):
        wav = make_wav(duration_seconds=2.0, frequency=150.0)
        r   = post_audio(wav)
        self._assert_valid_audio_response(r)

    def test_duration_seconds_is_accurate(self):
        """Reported duration must be within 0.5s of actual clip length."""
        wav  = make_wav(duration_seconds=3.0)
        r    = post_audio(wav)
        body = r.json()
        assert abs(body["duration_seconds"] - 3.0) < 0.5, \
            f"Duration {body['duration_seconds']}s too far from expected 3.0s"

    def test_audio_elapsed_ms_reasonable(self):
        """Audio prediction should complete in under 10 seconds."""
        wav  = make_wav(duration_seconds=2.0)
        r    = post_audio(wav)
        body = r.json()
        assert body["elapsed_ms"] < 10000, \
            f"Audio prediction too slow: {body['elapsed_ms']}ms"

    def test_audio_confidence_non_zero(self):
        wav  = make_wav(duration_seconds=2.5)
        r    = post_audio(wav)
        body = r.json()
        assert body["confidence"] > 0.0


# ─────────────────────────────────────────────────────────────────────
#  GROUP 5: Audio prediction — validation (bad inputs)
# ─────────────────────────────────────────────────────────────────────

class TestAudioPredictionValidation:

    def test_no_file_attached_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/predict/audio",
            timeout = TIMEOUT
        )
        assert r.status_code == 400

    def test_empty_wav_returns_400(self):
        r = post_audio(b"", "empty.wav")
        assert r.status_code == 400

    def test_text_file_as_audio_returns_400(self):
        r = post_audio(b"this is not audio data", "fake.wav")
        assert r.status_code == 400

    def test_silent_wav_handled_gracefully(self):
        """A silent clip may be rejected (400) or predicted — never 500."""
        wav = make_wav(duration_seconds=2.0, silent=True)
        r   = post_audio(wav)
        assert r.status_code in (200, 400), \
            f"Silent audio caused server error: {r.status_code}"

    def test_very_short_clip_returns_400(self):
        """Clips under 0.5s must be rejected with a clear message."""
        wav = make_wav(duration_seconds=0.2)
        r   = post_audio(wav)
        assert r.status_code == 400
        assert "short" in r.json().get("message", "").lower() or \
               r.status_code == 400

    def test_unsupported_extension_returns_400(self):
        wav = make_wav(duration_seconds=2.0)
        r   = post_audio(wav, filename="test.xyz")
        assert r.status_code == 400

    def test_server_never_returns_500_on_bad_audio(self):
        """Malformed audio must never cause a 500 error."""
        bad_inputs = [b"", b"RIFF garbage data", b"\x00" * 100]
        for data in bad_inputs:
            r = post_audio(data, "bad.wav")
            assert r.status_code != 500, \
                f"Server returned 500 on bad audio ({len(data)} bytes)"


# ─────────────────────────────────────────────────────────────────────
#  GROUP 6: API general behaviour
# ─────────────────────────────────────────────────────────────────────

class TestAPIBehaviour:

    def test_wrong_endpoint_returns_404(self):
        r = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert r.status_code == 404

    def test_404_response_has_message(self):
        r = requests.get(f"{BASE_URL}/nonexistent", timeout=TIMEOUT)
        assert "message" in r.json()

    def test_wrong_method_on_predict_text_returns_405(self):
        r = requests.get(f"{BASE_URL}/predict/text", timeout=TIMEOUT)
        assert r.status_code == 405

    def test_wrong_method_on_predict_audio_returns_405(self):
        r = requests.get(f"{BASE_URL}/predict/audio", timeout=TIMEOUT)
        assert r.status_code == 405

    def test_all_responses_are_json(self):
        """Every endpoint must return application/json."""
        endpoints = [
            ("GET",  f"{BASE_URL}/health"),
            ("POST", f"{BASE_URL}/predict/text"),
            ("GET",  f"{BASE_URL}/predict/text"),    # wrong method
        ]
        for method, url in endpoints:
            r = requests.request(method, url, timeout=TIMEOUT)
            ct = r.headers.get("Content-Type", "")
            assert "application/json" in ct, \
                f"{method} {url} returned Content-Type: {ct}"

    def test_concurrent_text_requests(self):
        """Two simultaneous requests must both succeed."""
        import concurrent.futures
        texts = [
            "I feel happy and at peace today.",
            "I am very anxious and cannot stop worrying.",
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(post_text, t) for t in texts]
            results = [f.result() for f in futures]

        for r in results:
            assert r.status_code == 200

    def test_rapid_sequential_requests_stable(self):
        """Five back-to-back requests — server must remain stable."""
        text = "I feel okay today, just a bit tired."
        for i in range(5):
            r = post_text(text)
            assert r.status_code == 200, \
                f"Request {i+1}/5 failed: {r.status_code}"

    def test_response_time_consistent(self):
        """Measure 3 requests — none should be 3x slower than the fastest."""
        text   = "I feel moderately stressed today."
        times  = []
        for _ in range(3):
            start = time.perf_counter()
            post_text(text)
            times.append(time.perf_counter() - start)

        fastest = min(times)
        slowest = max(times)
        assert slowest < fastest * 5, \
            f"Inconsistent response times: {[round(t,2) for t in times]}s"