from datetime import datetime

from pydantic import BaseModel

# ---------- 请求 ----------


class DocumentUpload(BaseModel):
    """文件上传用 multipart/form-data，不需要这个 schema，
    但保留作为接口文档说明：上传时字段 = file(UploadFile)"""

    pass


# ---------- 响应 ----------


class DocumentOut(BaseModel):
    """单个文档的返回结构"""

    id: int
    file_name: str
    file_type: str
    file_size: float
    status: str  # pending / parsing / chunking / embedding / ready / failed
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListOut(BaseModel):
    """文档列表（带分页信息）"""

    total: int
    page: int
    page_size: int
    items: list[DocumentOut]
