from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.split_bill import (
    SplitBillCreateRequest,
    SplitBillExtractResponse,
    SplitBillRecord,
    SplitBillUpdateRequest,
)
from app.services.analysis_service import AnalysisService
from app.services.draft_service import DraftService
from app.services.ocr_service import OcrService
from app.services.split_bill_service import SplitBillService


router = APIRouter(prefix="/split-bill")
ocr_service = OcrService()
analysis_service = AnalysisService()
split_bill_service = SplitBillService()
draft_service = DraftService()
ANON_OWNER_ID = "anonymous"


@router.post("/extract", response_model=SplitBillExtractResponse)
async def extract_split_bill(
    image: UploadFile = File(...),
) -> SplitBillExtractResponse:
    try:
        ocr_result = await ocr_service.extract_text(image)
        draft = await draft_service.create_draft(
            feature="split_bill",
            owner_id=ANON_OWNER_ID,
            ocr_text=ocr_result.text,
            raw=ocr_result.raw,
            image_filename=image.filename,
        )
        return SplitBillExtractResponse(
            success=True,
            message="Split bill OCR draft saved.",
            draft_id=draft.id,
            feature=draft.feature,
            ocr_text=draft.ocr_text,
            breakdown=None,
            raw=draft.raw,
            status=draft.status,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze/{draft_id}", response_model=SplitBillExtractResponse)
async def analyze_split_bill(draft_id: str) -> SplitBillExtractResponse:
    try:
        draft = await draft_service.get_draft(draft_id, owner_id=ANON_OWNER_ID, feature="split_bill")
        breakdown = analysis_service.analyze_split_bill(draft.ocr_text)
        updated_draft = await draft_service.update_analysis(
            draft_id,
            owner_id=ANON_OWNER_ID,
            feature="split_bill",
            analysis=breakdown,
        )
        return SplitBillExtractResponse(
            success=True,
            message="Split bill analysis completed.",
            draft_id=updated_draft.id,
            feature=updated_draft.feature,
            ocr_text=updated_draft.ocr_text,
            breakdown=breakdown,
            raw=updated_draft.raw,
            status=updated_draft.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/from-image", response_model=SplitBillRecord)
async def create_split_bill_from_image(
    user_name: str = Form(..., min_length=1),
    admin_account: str = Form(..., min_length=1),
    image: UploadFile = File(...),
) -> SplitBillRecord:
    try:
        ocr_result = await ocr_service.extract_text(image)
        breakdown = analysis_service.analyze_split_bill(ocr_result.text)
        bill_name = _extract_bill_name(breakdown)
        currency = str(breakdown.get("currency") or "IDR")
        total_amount = _extract_total_amount(breakdown)

        create_payload = SplitBillCreateRequest(
            user_name=user_name,
            admin_account=admin_account,
            bill_name=bill_name,
            total_amount=total_amount,
            currency=currency,
            ocr_text=ocr_result.text,
            breakdown=breakdown,
        )
        return await split_bill_service.create(ANON_OWNER_ID, create_payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("", response_model=SplitBillRecord)
async def create_split_bill(payload: SplitBillCreateRequest) -> SplitBillRecord:
    try:
        return await split_bill_service.create(ANON_OWNER_ID, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[SplitBillRecord])
async def list_split_bills() -> list[SplitBillRecord]:
    return await split_bill_service.list_all(ANON_OWNER_ID)


@router.get("/{bill_id}", response_model=SplitBillRecord)
async def get_split_bill(bill_id: str) -> SplitBillRecord:
    try:
        return await split_bill_service.get_by_id(ANON_OWNER_ID, bill_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{bill_id}", response_model=SplitBillRecord)
async def update_split_bill(
    bill_id: str,
    payload: SplitBillUpdateRequest,
) -> SplitBillRecord:
    try:
        return await split_bill_service.update(ANON_OWNER_ID, bill_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{bill_id}")
async def delete_split_bill(bill_id: str) -> dict[str, str]:
    try:
        await split_bill_service.delete(ANON_OWNER_ID, bill_id)
        return {"message": f"Split bill {bill_id} deleted"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _extract_total_amount(breakdown: dict) -> float:
    for key in ("total", "grand_total", "amount", "final_total"):
        value = breakdown.get(key)
        if value is not None:
            return _to_float(value)
    return 0.0


def _extract_bill_name(breakdown: dict) -> str:
    for key in ("bill_name", "merchant", "store_name", "title"):
        value = breakdown.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Untitled Bill"


def _to_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0
