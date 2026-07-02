from datetime import datetime

from app.core.database import get_database
from app.schemas.ocr import OcrDraftRecord
from app.utils.mongo import serialize_document, to_object_id


class DraftService:
    def __init__(self) -> None:
        pass

    @property
    def collection(self):
        return get_database().ocr_drafts

    async def create_draft(
        self,
        *,
        feature: str,
        ocr_text: str,
        raw: dict,
        owner_id: str | None = None,
        image_filename: str | None = None,
    ) -> OcrDraftRecord:
        now = datetime.utcnow()
        document = {
            "feature": feature,
            "owner_id": owner_id,
            "image_filename": image_filename,
            "ocr_text": ocr_text,
            "raw": raw,
            "analysis": None,
            "page_selected": None,
            "status": "ocr_completed",
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(document)
        created_document = await self.collection.find_one({"_id": result.inserted_id})
        return self._to_record(created_document)

    async def get_draft(self, draft_id: str, *, owner_id: str | None = None, feature: str | None = None) -> OcrDraftRecord:
        query: dict = {"_id": to_object_id(draft_id)}
        if owner_id is not None:
            query["owner_id"] = owner_id
        if feature is not None:
            query["feature"] = feature

        document = await self.collection.find_one(query)
        if document is None:
            raise ValueError(f"Draft {draft_id} not found")
        return self._to_record(document)

    async def update_analysis(
        self,
        draft_id: str,
        *,
        analysis: dict,
        page_selected: int | None = None,
        owner_id: str | None = None,
        feature: str | None = None,
    ) -> OcrDraftRecord:
        query: dict = {"_id": to_object_id(draft_id)}
        if owner_id is not None:
            query["owner_id"] = owner_id
        if feature is not None:
            query["feature"] = feature

        update_fields = {
            "analysis": analysis,
            "status": "analysis_completed",
            "updated_at": datetime.utcnow(),
        }
        if page_selected is not None:
            update_fields["page_selected"] = page_selected

        result = await self.collection.update_one(query, {"$set": update_fields})
        if result.matched_count == 0:
            raise ValueError(f"Draft {draft_id} not found")

        return await self.get_draft(draft_id, owner_id=owner_id, feature=feature)

    @staticmethod
    def _to_record(document: dict | None) -> OcrDraftRecord:
        data = serialize_document(document)
        if data is None:
            raise ValueError("Draft document is empty")
        return OcrDraftRecord.model_validate(data)
