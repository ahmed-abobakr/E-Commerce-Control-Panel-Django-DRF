# app/services/embeddings.py
from __future__ import annotations
import os, time, math
from dotenv import load_dotenv
from typing import Iterable, List
from openai import OpenAI, RateLimitError, APIConnectionError, APITimeoutError

load_dotenv()

# ---------- Config ----------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")  # 1536 dims
EXPECTED_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#modify value to latest batch
MAX_BATCH = int(os.getenv("EMBEDDING_MAX_BATCH", "128"))

# ---------- Client ----------
_client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Utils ----------
def _normalize_text(t: str) -> str:
    # OpenAI works better without extra newlines
    return (t or "").replace("\r", " ").replace("\n", " ").strip()

def _check_dim(vec: List[float]) -> None:
    if EXPECTED_DIM and len(vec) != EXPECTED_DIM:
        raise ValueError(
            f"Embedding dimension mismatch: got {len(vec)}, expected {EXPECTED_DIM}. "
            f"Model='{EMBEDDING_MODEL}'. تأكد إن جدول pgvector عامل vector({EXPECTED_DIM})."
        )

def to_sql_vector(vec: Iterable[float]) -> str:
    """Convert list of floats into a SQL ARRAY[] literal for pgvector"""
    return "ARRAY[" + ",".join(str(float(x)) for x in vec) + "]"

# ---------- Core (single) ----------
def get_embedding(text: str, *, max_retries: int = 5, timeout: float = 20.0) -> List[float]:
    """
    return embedding as a List[float] to one text.
    - Retries بزيادة أسّية
    - assert EXPECTED_DIM
    """
    payload = _normalize_text(text)
    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            resp = _client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=payload,
                timeout=timeout,  # openai>=1.40 يدعم timeout في بعض البيئات
            )
            vec = resp.data[0].embedding
            _check_dim(vec)
            return vec
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            if attempt == max_retries:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 16)  # exponential backoff
        except Exception as e:
            # other errors return in logs
            print(e.message)
            raise

# ---------- Core (batch) ----------
def get_embeddings(texts: List[str], *, max_retries: int = 5, timeout: float = 60.0, batch_size: int | None = None) -> List[List[float]]:
    """
    Batch embedding keeps order of text.
    """
    if batch_size is None:
        batch_size = min(MAX_BATCH, 128)

    # Normalize
    payloads = [_normalize_text(t) for t in texts]
    outputs: List[List[float]] = []
    total = len(payloads)
    n_batches = math.ceil(total / batch_size) if total else 0

    for i in range(n_batches):
        chunk = payloads[i * batch_size : (i + 1) * batch_size]
        delay = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                resp = _client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=chunk,
                    timeout=timeout,
                )
                vectors = [d.embedding for d in resp.data]
                for v in vectors:
                    _check_dim(v)
                outputs.extend(vectors)
                break
            except (RateLimitError, APITimeoutError, APIConnectionError):
                if attempt == max_retries:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 16)
            except Exception:
                raise

    return outputs
