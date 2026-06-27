import pickle
import logging
import numpy as np
from pathlib import Path
from scipy.sparse import hstack

from src.utils import preprocess_text
from src.config import NB_PATH, LR_PATH, SVM_PATH, META_PATH, VEC_PATH

logger = logging.getLogger(__name__)


def _load(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {path!r}. "
            "Run src/train.py first to generate model files."
        )
    with open(p, "rb") as f:
        return pickle.load(f)


def _load_models():
    logger.info("Loading model artifacts …")
    nb   = _load(NB_PATH)
    lr   = _load(LR_PATH)
    svm  = _load(SVM_PATH)
    meta = _load(META_PATH)
    tfidf_word, tfidf_char = _load(VEC_PATH)
    logger.info("All models loaded successfully.")
    return nb, lr, svm, meta, tfidf_word, tfidf_char


# Module-level singletons — loaded once on first import
try:
    _nb, _lr, _svm, _meta, _tfidf_word, _tfidf_char = _load_models()
except FileNotFoundError as e:
    logger.error(str(e))
    raise


def predict(text: str, top_k: int = 3) -> dict:
    """
    Run the hybrid NB + LR + SVM + meta-model pipeline on a single text.

    Returns
    -------
    dict with keys:
        label       – top predicted topic
        confidence  – probability of top label (from best probabilistic model)
        top_k       – list of {label, score} dicts (length = top_k)
        model_votes – individual model predictions
        decided_by  – "majority_vote" or "meta_model"
    """
    text_clean = preprocess_text(text)

    X_word = _tfidf_word.transform([text_clean])
    X_char = _tfidf_char.transform([text_clean])
    X = hstack([X_word, X_char])

    nb_pred  = _nb.predict(X)[0]
    lr_pred  = _lr.predict(X)[0]
    svm_pred = _svm.predict(X)[0]

    nb_prob = _nb.predict_proba(X)[0]   # shape: (n_classes,)
    lr_prob = _lr.predict_proba(X)[0]

    nb_conf = float(np.max(nb_prob))
    lr_conf = float(np.max(lr_prob))

    # ── Majority vote ────────────────────────────────────────────────────────
    votes = [nb_pred, lr_pred, svm_pred]
    decided_by = "majority_vote"

    if votes.count(nb_pred) > 1:
        final_label = nb_pred
    elif votes.count(lr_pred) > 1:
        final_label = lr_pred
    else:
        # ── Meta-model tie-break ─────────────────────────────────────────────
        meta_feat = [[
            nb_conf,
            lr_conf,
            int(nb_pred == lr_pred),
            int(lr_pred == svm_pred),
        ]]
        choice = _meta.predict(meta_feat)[0]
        final_label = nb_pred if choice == 0 else lr_pred
        decided_by = "meta_model"

    # ── Build top-k from the richer probabilistic model (LR) ─────────────────
    classes = _lr.classes_
    # Blend NB and LR probabilities; LR is generally better calibrated after AL
    blended = 0.35 * nb_prob + 0.65 * lr_prob

    top_k = min(top_k, len(classes))
    top_indices = np.argsort(blended)[::-1][:top_k]

    top_k_results = [
        {"label": classes[i], "score": round(float(blended[i]), 4)}
        for i in top_indices
    ]

    # Use blended confidence for the winning label
    final_idx  = list(classes).index(final_label)
    confidence = round(float(blended[final_idx]), 4)

    return {
        "label":       final_label,
        "confidence":  confidence,
        "top_k":       top_k_results,
        "model_votes": {"nb": nb_pred, "lr": lr_pred, "svm": svm_pred},
        "decided_by":  decided_by,
    }