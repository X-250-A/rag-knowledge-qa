import os

# 模型权重已在本地缓存，强制离线可避免导入时联网检查 huggingface.co 而挂起
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")


def get_embedding(chunks: list):
    return model.encode(chunks)
