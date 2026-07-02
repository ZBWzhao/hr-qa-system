import os

from sentence_transformers import SentenceTransformer
from app.core.config import settings

_model = None

# 本地模型目录（无需下载）
LOCAL_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "models", "text2vec-base-chinese")


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_path = os.path.abspath(LOCAL_MODEL_DIR)
        if os.path.exists(model_path):
            _model = SentenceTransformer(model_path)
        else:
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def encode_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def encode_text(text: str) -> list[float]:
    return encode_texts([text])[0]
