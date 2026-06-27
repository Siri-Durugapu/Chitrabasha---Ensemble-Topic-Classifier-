import os

# ── Data ──────────────────────────────────────────────────────────────────────
DATA_PATH        = "data/dataset_10M.parquet"
SAMPLE_SIZE      = 5_000        # ← change to 50_000 / 100_000 once confirmed working
RANDOM_STATE     = 42

# ── Split ratios (must sum to 1.0) ────────────────────────────────────────────
TEST_SIZE        = 0.20
VAL_SIZE         = 0.10

# ── TF-IDF ────────────────────────────────────────────────────────────────────
TFIDF_WORD_FEATURES  = 5_000
TFIDF_CHAR_FEATURES  = 2_000
TFIDF_WORD_NGRAM     = (1, 2)
TFIDF_CHAR_NGRAM     = (3, 5)

# ── Active learning ───────────────────────────────────────────────────────────
ACTIVE_POOL_RATIO    = 0.30
ACTIVE_UNCERTAIN_K   = 1_000
ACTIVE_DISAGREE_K    = 1_000

# ── Models ────────────────────────────────────────────────────────────────────
LR_MAX_ITER      = 300

# ── Paths ─────────────────────────────────────────────────────────────────────
MODEL_DIR        = "final_models"
NB_PATH          = os.path.join(MODEL_DIR, "nb.pkl")
LR_PATH          = os.path.join(MODEL_DIR, "lr.pkl")
SVM_PATH         = os.path.join(MODEL_DIR, "svm.pkl")
META_PATH        = os.path.join(MODEL_DIR, "meta.pkl")
VEC_PATH         = os.path.join(MODEL_DIR, "vectorizer.pkl")
CLASSES_PATH     = os.path.join(MODEL_DIR, "classes.pkl")