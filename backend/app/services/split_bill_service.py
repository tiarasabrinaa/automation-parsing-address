import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.schemas.split_bill import SplitBillCreateRequest, SplitBillRecord, SplitBillUpdateRequest
from datetime import datetime

from app.core.database import get_database
from app.schemas.split_bill import SplitBillCreateRequest, SplitBillRecord, SplitBillUpdateRequest
from app.utils.mongo import serialize_document, to_object_id


class SplitBillService:
    def __init__(self) -> None:
        pass

    @property
    def collection(self):
        return get_database().split_bills

    async def create(self, owner_id: str, payload: SplitBillCreateRequest) -> SplitBillRecord:
        now = datetime.utcnow()
        document = {
            "owner_id": owner_id,
            "user_name": payload.user_name,
            "admin_account": payload.admin_account,
            "bill_name": payload.bill_name,
            "total_amount": float(payload.total_amount),
            "currency": payload.currency,
            "ocr_text": payload.ocr_text,
            "breakdown": payload.breakdown,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(document)
        return await self.get_by_id(owner_id, str(result.inserted_id))

    async def list_all(self, owner_id: str) -> list[SplitBillRecord]:
        cursor = self.collection.find({"owner_id": owner_id}).sort("created_at", -1)
        records: list[SplitBillRecord] = []
        async for document in cursor:
            records.append(self._to_record(document))
        return records

    async def get_by_id(self, owner_id: str, bill_id: str) -> SplitBillRecord:
        document = await self.collection.find_one({"_id": to_object_id(bill_id), "owner_id": owner_id})
        if document is None:
            raise ValueError(f"Split bill with id {bill_id} not found")
        return self._to_record(document)

    async def update(self, owner_id: str, bill_id: str, payload: SplitBillUpdateRequest) -> SplitBillRecord:
        document = await self.collection.find_one({"_id": to_object_id(bill_id), "owner_id": owner_id})
        if document is None:
            raise ValueError(f"Split bill with id {bill_id} not found")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return self._to_record(document)

        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": document["_id"], "owner_id": owner_id},
            {"$set": update_data},
        )
        return await self.get_by_id(owner_id, bill_id)

    async def delete(self, owner_id: str, bill_id: str) -> None:
        result = await self.collection.delete_one({"_id": to_object_id(bill_id), "owner_id": owner_id})
        if result.deleted_count == 0:
            raise ValueError(f"Split bill with id {bill_id} not found")

    @staticmethod
    def _to_record(document: dict) -> SplitBillRecord:
        data = serialize_document(document)
        if data is None:
            raise ValueError("Split bill document is empty")
        return SplitBillRecord.model_validate(data)
