# ══════════════════════════════════════════════════════
#  Audio prediction pipeline
#  Applies the exact same preprocessing as Phase 3 & 4
# ══════════════════════════════════════════════════════
import io
import logging
import numpy as np
import librosa
import soundfile as sf

log = logging.getLogger(__name__)

TARGET_SR  = 22050
TOP_DB     = 20
TARGET_RMS = 0.1
N_MFCC     = 40
MIN_DURATION = 0.5    # seconds — clips shorter than this are rejected


def preprocess_audio(audio_bytes: bytes) -> np.ndarray:
    """
    Loads audio from raw bytes, trims silence, normalises volume.
    Returns a 1D numpy array of audio samples.
    """
    # Load from bytes without saving to disk
    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=TARGET_SR, mono=True)

    if len(audio) == 0:
        raise ValueError("Audio file is silent or unreadable.")

    duration = len(audio) / sr
    if duration < MIN_DURATION:
        raise ValueError(
            f"Audio clip is too short ({duration:.2f}s). "
            f"Minimum is {MIN_DURATION}s."
        )

    # Trim silence
    audio_trimmed, _ = librosa.effects.trim(audio, top_db=TOP_DB)

    # Guard against over-trimming
    if len(audio_trimmed) < sr * 0.1:
        audio_trimmed = audio

    # RMS normalisation
    rms = np.sqrt(np.mean(audio_trimmed ** 2))
    if rms > 0:
        audio_norm = audio_trimmed * (TARGET_RMS / rms)
    else:
        audio_norm = audio_trimmed

    return np.clip(audio_norm, -1.0, 1.0)


def extract_features(audio: np.ndarray) -> np.ndarray:
    """
    Extracts the same 122-feature vector used during Phase 4 training.
    Any difference here will silently degrade accuracy.
    """
    sr = TARGET_SR

    # MFCCs — 40 × (mean + std) = 80 features
    mfcc       = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean  = mfcc.mean(axis=1)
    mfcc_std   = mfcc.std(axis=1)

    # Chroma — 12 × (mean + std) = 24 features
    chroma      = librosa.feature.chroma_stft(y=audio, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    chroma_std  = chroma.std(axis=1)

    # Spectral contrast — 7 × (mean + std) = 14 features
    contrast      = librosa.feature.spectral_contrast(y=audio, sr=sr)
    contrast_mean = contrast.mean(axis=1)
    contrast_std  = contrast.std(axis=1)

    # Pitch — 2 features
    f0, _, _ = librosa.pyin(audio, fmin=50, fmax=400, sr=sr, fill_na=0.0)
    pitch_mean = np.mean(f0)
    pitch_std  = np.std(f0)

    # RMS energy — 2 features
    rms     = librosa.feature.rms(y=audio)
    rms_mean = rms.mean()
    rms_std  = rms.std()

    # Stack → 80 + 24 + 14 + 2 + 2 = 122 features
    features = np.concatenate([
        mfcc_mean, mfcc_std,
        chroma_mean, chroma_std,
        contrast_mean, contrast_std,
        [pitch_mean, pitch_std, rms_mean, rms_std]
    ]).astype(np.float32)

    # Validate — NaN/Inf will crash the scaler
    if np.isnan(features).any() or np.isinf(features).any():
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        log.warning("NaN/Inf found in audio features — replaced with 0.")

    return features


def predict_audio(audio_bytes: bytes, audio_pipeline, label_encoder) -> dict:
    """
    Full audio prediction pipeline.

    Parameters
    ----------
    audio_bytes    : raw bytes from the uploaded file
    audio_pipeline : loaded sklearn Pipeline (scaler + model)
    label_encoder  : fitted LabelEncoder

    Returns
    -------
    dict with keys: risk_level, confidence, class_probs, duration_seconds
    """
    # Step 1: Preprocess
    audio = preprocess_audio(audio_bytes)
    duration = len(audio) / TARGET_SR

    # Step 2: Extract features
    features = extract_features(audio)
    X = features.reshape(1, -1)         # model expects (1, 122)

    # Step 3: Predict
    pred_encoded = audio_pipeline.predict(X)[0]
    pred_proba   = audio_pipeline.predict_proba(X)[0]

    risk_level = label_encoder.inverse_transform([pred_encoded])[0]
    confidence = float(round(pred_proba.max(), 4))

    class_probs = {
        label_encoder.inverse_transform([i])[0]: round(float(p), 4)
        for i, p in enumerate(pred_proba)
    }

    return {
        'risk_level'      : risk_level,
        'confidence'      : confidence,
        'class_probs'     : class_probs,
        'duration_seconds': round(duration, 2),
    }