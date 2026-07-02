from pydantic import BaseModel


class AutoRouteResponse(BaseModel):
    success: bool
    message: str
    draft_id: str
    feature: str = "auto_route"
    ocr_text: str
    analysis: dict | None = None
    page_selected: int | None = None
    raw: dict | None = None

