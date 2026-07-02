from bson import ObjectId


def to_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid identifier")
    return ObjectId(value)


def serialize_document(document: dict | None) -> dict | None:
    if document is None:
        return None

    result = dict(document)
    result["id"] = str(result.pop("_id"))
    return result
