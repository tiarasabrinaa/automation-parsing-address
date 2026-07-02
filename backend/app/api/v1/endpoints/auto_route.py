import json
import re

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.auto_route import AutoRouteResponse
from app.schemas.ocr import OcrDraftResponse
from app.services.analysis_service import AnalysisService
from app.services.draft_service import DraftService
from app.services.ocr_service import OcrService


router = APIRouter()
ocr_service = OcrService()
analysis_service = AnalysisService()
draft_service = DraftService()
ANON_OWNER_ID = "anonymous"


@router.post("/auto-route/extract", response_model=OcrDraftResponse)
async def extract_auto_route(
    image: UploadFile = File(...),
) -> OcrDraftResponse:
    try:
        ocr_result = await ocr_service.extract_text(image)
        draft = await draft_service.create_draft(
            feature="auto_route",
            owner_id=ANON_OWNER_ID,
            ocr_text=ocr_result.text,
            raw=ocr_result.raw,
            image_filename=image.filename,
        )
        return OcrDraftResponse(
            success=True,
            message="Auto route OCR draft saved.",
            draft_id=draft.id,
            feature=draft.feature,
            ocr_text=draft.ocr_text,
            raw=draft.raw,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auto-route/analyze/{draft_id}", response_model=AutoRouteResponse)
async def analyze_auto_route(draft_id: str) -> AutoRouteResponse:
    try:
        draft = await draft_service.get_draft(draft_id, owner_id=ANON_OWNER_ID, feature="auto_route")
        analysis_raw = analysis_service.analyze_auto_route(draft.ocr_text)
        analysis = _parse_json_payload(analysis_raw)
        page_selected = _to_int(analysis.get("page_selected"))
        updated_draft = await draft_service.update_analysis(
            draft_id,
            owner_id=ANON_OWNER_ID,
            feature="auto_route",
            analysis=analysis,
            page_selected=page_selected,
        )
        return AutoRouteResponse(
            success=True,
            message="Auto route analysis completed.",
            draft_id=updated_draft.id,
            feature="Beli pulsa",
            ocr_text="Belikan pulsa untuk nomor 081234567890 dengan nominal 50 ribu",
            analysis=analysis,
            page_selected=updated_draft.page_selected,
            raw=updated_draft.raw,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _parse_json_payload(payload: object) -> dict:
    if isinstance(payload, dict):
        # If service returned a fallback payload, try parsing the raw text one more time.
        raw_text = payload.get("raw")
        if len(payload) == 1 and isinstance(raw_text, str):
            reparsed = _parse_json_payload(raw_text)
            if not (set(reparsed.keys()) == {"raw"} and reparsed.get("raw") == raw_text):
                return reparsed
        return payload

    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return {}

        text = _strip_markdown_fence(text)
        for candidate in (text, _extract_object_candidate(text)):
            if not candidate:
                continue

            for normalized in (candidate, _normalize_json_like(candidate)):
                try:
                    parsed = json.loads(normalized)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    continue

        return {"raw": payload}

    return {"raw": str(payload)}


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _extract_object_candidate(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _normalize_json_like(text: str) -> str:
    normalized = text
    # LLMs often return phone numbers with leading zeros as bare numbers.
    normalized = re.sub(r'("number"\s*:\s*)(0\d+)', r'\1"\2"', normalized)
    normalized = re.sub(r',\s*([}\]])', r'\1', normalized)
    return normalized


def _to_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except ValueError:
            return None
    return None
