from datetime import datetime

from pydantic import BaseModel


class OcrResult(BaseModel):
    text: str
    raw: dict


class OcrDraftResponse(BaseModel):
    success: bool
    message: str
    draft_id: str
    feature: str
    ocr_text: str
    raw: dict
    status: str = "ocr_completed"


class OcrDraftRecord(BaseModel):
    id: str
    feature: str
    owner_id: str | None = None
    image_filename: str | None = None
    ocr_text: str
    raw: dict
    analysis: dict | None = None
    page_selected: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime
