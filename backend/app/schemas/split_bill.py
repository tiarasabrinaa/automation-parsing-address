from datetime import datetime

from pydantic import BaseModel, Field


class SplitBillExtractResponse(BaseModel):
    success: bool
    message: str
    draft_id: str
    feature: str = "split_bill"
    ocr_text: str
    breakdown: dict | None = None
    raw: dict | None = None
    status: str = "ocr_completed"


class SplitBillRecord(BaseModel):
    id: str
    owner_id: str
    user_name: str
    admin_account: str
    bill_name: str
    total_amount: float
    currency: str = "IDR"
    ocr_text: str
    breakdown: dict
    created_at: datetime
    updated_at: datetime


class SplitBillCreateRequest(BaseModel):
    user_name: str = Field(..., min_length=1)
    admin_account: str = Field(..., min_length=1)
    bill_name: str = Field(..., min_length=1)
    total_amount: float = Field(..., ge=0)
    currency: str = Field(default="IDR", min_length=1)
    ocr_text: str = ""
    breakdown: dict = Field(default_factory=dict)


class SplitBillUpdateRequest(BaseModel):
    user_name: str | None = None
    admin_account: str | None = None
    bill_name: str | None = None
    total_amount: float | None = Field(default=None, ge=0)
    currency: str | None = None
    ocr_text: str | None = None
    breakdown: dict | None = None

