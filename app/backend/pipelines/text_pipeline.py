# ══════════════════════════════════════════════════════
#  Text prediction pipeline
#  Applies the exact same cleaning steps as Phase 3
# ══════════════════════════════════════════════════════
import re
import logging
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from scipy import sparse
import numpy as np

log = logging.getLogger(__name__)

# Download required NLTK data (silent — already downloaded in Phase 3)
for pkg in ['punkt', 'punkt_tab', 'stopwords', 'wordnet', 'vader_lexicon']:
    nltk.download(pkg, quiet=True)

EXTRA_STOPWORDS = {
    "felt", "feeling", "feel", "would", "get", "got",
    "also", "one", "even", "although", "could", "said"
}

CONTRACTIONS = {
    r"won't": "will not", r"can't": "cannot",  r"n't": " not",
    r"'re":   " are",     r"'s":    " is",      r"'d":  " would",
    r"'ll":   " will",    r"'ve":   " have",    r"'m":  " am",
}

_stop_words  = None
_lemmatizer  = None
_sia         = None


def _init_nlp():
    """Lazy initialise NLP tools on first call."""
    global _stop_words, _lemmatizer, _sia
    if _stop_words is None:
        _stop_words = set(stopwords.words('english')) | EXTRA_STOPWORDS
        _lemmatizer = WordNetLemmatizer()
        _sia        = SentimentIntensityAnalyzer()
        log.info("NLP tools initialised.")


def clean_text(text: str) -> str:
    """
    Applies the exact same cleaning pipeline used in Phase 3.
    Must match perfectly — any difference will degrade predictions.
    """
    _init_nlp()

    if not isinstance(text, str) or not text.strip():
        return ""

    text = text.lower()

    for pattern, replacement in CONTRACTIONS.items():
        text = re.sub(pattern, replacement, text)

    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)

    tokens = word_tokenize(text)
    tokens = [
        _lemmatizer.lemmatize(w)
        for w in tokens
        if w not in _stop_words and len(w) > 1
    ]

    return " ".join(tokens)


def predict_text(text: str, text_model, tfidf, label_encoder) -> dict:
    """
    Full text prediction pipeline.

    Parameters
    ----------
    text         : raw user input string
    text_model   : loaded sklearn pipeline or model
    tfidf        : fitted TfidfVectorizer
    label_encoder: fitted LabelEncoder

    Returns
    -------
    dict with keys: risk_level, confidence, sentiment, cleaned_text
    """
    _init_nlp()

    # Step 1: Clean
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Text reduced to empty after cleaning.")

    # Step 2: Sentiment score
    sentiment = _sia.polarity_scores(cleaned)['compound']

    # Step 3: TF-IDF vectorise
    tfidf_vec = tfidf.transform([cleaned])

    # Step 4: Append sentiment as one extra feature
    sent_sparse = sparse.csr_matrix([[sentiment]])
    X = sparse.hstack([tfidf_vec, sent_sparse])

    # Step 5: Predict
    pred_encoded = text_model.predict(X)[0]
    pred_proba   = text_model.predict_proba(X)[0]

    risk_level  = label_encoder.inverse_transform([pred_encoded])[0]
    confidence  = float(round(pred_proba.max(), 4))

    # Per-class probabilities (useful for the frontend progress bars)
    class_probs = {
        label_encoder.inverse_transform([i])[0]: round(float(p), 4)
        for i, p in enumerate(pred_proba)
    }

    return {
        'risk_level'   : risk_level,
        'confidence'   : confidence,
        'sentiment'    : round(float(sentiment), 4),
        'class_probs'  : class_probs,
        'cleaned_text' : cleaned,
    }