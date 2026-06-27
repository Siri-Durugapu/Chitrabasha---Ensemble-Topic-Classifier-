import re
import random
import logging

import pandas as pd
import pyarrow.parquet as pq

from src.config import DATA_PATH, SAMPLE_SIZE, RANDOM_STATE

logger = logging.getLogger(__name__)
random.seed(RANDOM_STATE)


def load_data(
    path: str = DATA_PATH,
    sample_size: int = SAMPLE_SIZE,
) -> pd.DataFrame:
    """
    Stream-read the Parquet dataset row-group by row-group until we have
    at least `sample_size` rows, then random-sample down to exactly that
    number.  This keeps peak memory low even for multi-GB files.
    """
    parquet_file = pq.ParquetFile(path)
    n_row_groups = parquet_file.num_row_groups
    logger.info("Parquet file has %d row groups.", n_row_groups)

    chunks, total_rows = [], 0
    for rg in range(n_row_groups):
        chunk = parquet_file.read_row_group(rg, columns=["DATA", "TOPIC"]).to_pandas()
        chunks.append(chunk)
        total_rows += len(chunk)
        if total_rows >= sample_size:
            break

    df = pd.concat(chunks, ignore_index=True)

    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=RANDOM_STATE).reset_index(drop=True)

    logger.info("Loaded %d samples across %d classes.", len(df), df["TOPIC"].nunique())
    logger.info("Class distribution:\n%s", df["TOPIC"].value_counts().to_string())
    return df


# ── Text cleaning ─────────────────────────────────────────────────────────────

_URL_RE    = re.compile(r"https?://\S+|www\.\S+")
_NONALPHA  = re.compile(r"[^a-z ]")
_SPACES    = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = _URL_RE.sub(" ", text)
    text = _NONALPHA.sub(" ", text)
    text = _SPACES.sub(" ", text).strip()
    return text


def preprocess_text(text: str) -> str:
    return clean_text(text)