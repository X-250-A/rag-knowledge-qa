import os

# 模型权重已在本地缓存，强制离线可避免导入时联网检查 huggingface.co 而挂起。
# 注意：这里不能 True 拉死——CI 需要 HF_HUB_OFFLINE=0 覆盖来首次下载权重，
# 所以用 setdefault 只提供默认值，环境变量可从外部覆盖。
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer

# 惰性加载：import 本模块不再触发 2.3GB 权重下载/加载，
# 首次调用 get_embedding 才初始化。这让测试可以只 mock get_embedding
# 而无需真的碰模型，也让模块导入在无网环境（CI lint job）下安全。
model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global model
    if model is None:
        model = SentenceTransformer("BAAI/bge-m3")
    return model


def get_embedding(chunks: list):
    return _get_model().encode(chunks)
