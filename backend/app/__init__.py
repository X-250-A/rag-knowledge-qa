# app 包出口：统一导出配置与版本信息
# 注意：这里只放“轻量、无副作用”的导入，避免把 main/app 拉进来。
# main.py 里构建 FastAPI 实例，若 __init__ 再导入它会造成循环导入。
from backend.app.config import settings

__version__ = "0.1.0"

__all__ = ["settings", "__version__"]
