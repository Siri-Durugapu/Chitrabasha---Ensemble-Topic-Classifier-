"""
Training pipeline for Chitrabasha hybrid text classifier.

    python -m src.train
"""

import os
import time
import pickle
import logging

import numpy as np
import pandas as pd
from scipy.sparse import hstack, vstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from src.utils import load_data, preprocess_text
from src.model import train_nb, train_lr, train_svm
from src.config import (
    RANDOM_STATE, TEST_SIZE, VAL_SIZE,
    TFIDF_WORD_FEATURES, TFIDF_CHAR_FEATURES,
    TFIDF_WORD_NGRAM, TFIDF_CHAR_NGRAM,
    ACTIVE_POOL_RATIO, ACTIVE_UNCERTAIN_K, ACTIVE_DISAGREE_K,
    MODEL_DIR,
    NB_PATH, LR_PATH, SVM_PATH, META_PATH, VEC_PATH, CLASSES_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── 1. Load & preprocess ──────────────────────────────────────────────────────

logger.info("Loading data …")
df = load_data()
df["DATA"] = df["DATA"].apply(preprocess_text)
y = df["TOPIC"]

# ── 2. TF-IDF vectorisation ───────────────────────────────────────────────────

logger.info("Fitting TF-IDF vectorisers …")
tfidf_word = TfidfVectorizer(
    max_features=TFIDF_WORD_FEATURES,
    ngram_range=TFIDF_WORD_NGRAM,
)
tfidf_char = TfidfVectorizer(
    analyzer="char",
    ngram_range=TFIDF_CHAR_NGRAM,
    max_features=TFIDF_CHAR_FEATURES,
)

X_word = tfidf_word.fit_transform(df["DATA"])
X_char = tfidf_char.fit_transform(df["DATA"])
X = hstack([X_word, X_char])

# ── 3. Stratified train / val / test split ────────────────────────────────────

X_dev, X_test, y_dev, y_test = train_test_split(
    X, y,
    test_size=TEST_SIZE,
    stratify=y,
    random_state=RANDOM_STATE,
)

val_frac = VAL_SIZE / (1 - TEST_SIZE)
X_trainpool, X_val, y_trainpool, y_val = train_test_split(
    X_dev, y_dev,
    test_size=val_frac,
    stratify=y_dev,
    random_state=RANDOM_STATE,
)

X_train, X_pool, y_train, y_pool = train_test_split(
    X_trainpool, y_trainpool,
    test_size=ACTIVE_POOL_RATIO,
    stratify=y_trainpool,
    random_state=RANDOM_STATE,
)

logger.info(
    "Split → train: %d | pool: %d | val: %d | test: %d",
    X_train.shape[0], X_pool.shape[0], X_val.shape[0], X_test.shape[0],
)

# ── 4. Base model training ────────────────────────────────────────────────────

logger.info("Training base models …")
t0  = time.time()
nb  = train_nb(X_train, y_train)
lr  = train_lr(X_train, y_train)
svm = train_svm(X_train, y_train)
logger.info("Base models trained in %.2f s", time.time() - t0)

for name, model in [("Naive Bayes", nb), ("Logistic Regression", lr), ("SVM", svm)]:
    print(f"\n── {name} ──")
    print(classification_report(y_test, model.predict(X_test), zero_division=0))

# ── 5. Active learning (uncertainty + disagreement sampling) ──────────────────

logger.info("Running active learning …")
lr_probs_pool = lr.predict_proba(X_pool)
nb_pred_pool  = nb.predict(X_pool)
lr_pred_pool  = lr.predict(X_pool)

uncertainty   = 1 - np.max(lr_probs_pool, axis=1)
disagreement  = nb_pred_pool != lr_pred_pool

uncertain_idx = np.argsort(uncertainty)[-ACTIVE_UNCERTAIN_K:]
disagree_idx  = np.where(disagreement)[0][:ACTIVE_DISAGREE_K]
hard_idx      = np.unique(np.concatenate([uncertain_idx, disagree_idx]))

X_train_al = vstack([X_train, X_pool[hard_idx]])
y_train_al = np.concatenate([y_train, y_pool.iloc[hard_idx]])

lr = train_lr(X_train_al, y_train_al)

print("\n── LR after active learning ──")
print(classification_report(y_test, lr.predict(X_test), zero_division=0))

# ── 6. Meta-model (trained on val predictions — no leakage) ──────────────────

logger.info("Building meta-model on validation set …")
nb_probs_val = nb.predict_proba(X_val)
lr_probs_val = lr.predict_proba(X_val)
nb_pred_val  = nb.predict(X_val)
lr_pred_val  = lr.predict(X_val)
svm_pred_val = svm.predict(X_val)

meta_X = [
    [
        float(np.max(nb_probs_val[i])),
        float(np.max(lr_probs_val[i])),
        int(nb_pred_val[i] == lr_pred_val[i]),
        int(lr_pred_val[i] == svm_pred_val[i]),
    ]
    for i in range(len(nb_pred_val))
]
meta_y = [
    1 if lr_pred_val[i] == y_val.iloc[i] else 0
    for i in range(len(nb_pred_val))
]

meta = train_lr(np.array(meta_X), meta_y)

# ── 7. Final hybrid evaluation on test set ────────────────────────────────────

logger.info("Evaluating final hybrid on test set …")
nb_probs_test = nb.predict_proba(X_test)
lr_probs_test = lr.predict_proba(X_test)
nb_pred_test  = nb.predict(X_test)
lr_pred_test  = lr.predict(X_test)
svm_pred_test = svm.predict(X_test)

final_preds = []
for i in range(len(nb_pred_test)):
    votes = [nb_pred_test[i], lr_pred_test[i], svm_pred_test[i]]

    if votes.count(nb_pred_test[i]) > 1:
        final_preds.append(nb_pred_test[i])
    elif votes.count(lr_pred_test[i]) > 1:
        final_preds.append(lr_pred_test[i])
    else:
        nb_conf = float(np.max(nb_probs_test[i]))
        lr_conf = float(np.max(lr_probs_test[i]))
        choice  = meta.predict([[
            nb_conf, lr_conf,
            int(nb_pred_test[i] == lr_pred_test[i]),
            int(lr_pred_test[i] == svm_pred_test[i]),
        ]])[0]
        final_preds.append(nb_pred_test[i] if choice == 0 else lr_pred_test[i])

print("\n── Final hybrid results ──")
print(classification_report(y_test, final_preds, zero_division=0))

# ── 8. Save test results ──────────────────────────────────────────────────────

os.makedirs(MODEL_DIR, exist_ok=True)

results_path = os.path.join(MODEL_DIR, "test_results.csv")
pd.DataFrame({"actual": y_test, "predicted": final_preds}).to_csv(results_path, index=False)
logger.info("Test results saved to %s", results_path)

# ── 9. Save model artefacts ───────────────────────────────────────────────────

logger.info("Saving model artefacts …")
for obj, path in [
    (nb,                     NB_PATH),
    (lr,                     LR_PATH),
    (svm,                    SVM_PATH),
    (meta,                   META_PATH),
    ((tfidf_word, tfidf_char), VEC_PATH),
    (list(y.unique()),       CLASSES_PATH),
]:
    with open(path, "wb") as f:
        pickle.dump(obj, f)

logger.info("All artefacts saved to %s/", MODEL_DIR)