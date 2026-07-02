from io import BytesIO

from PIL import Image
from fastapi import UploadFile
import pytesseract

from app.core.config import settings
from app.schemas.ocr import OcrResult


class OcrService:
    async def extract_text(self, image: UploadFile) -> OcrResult:
        content = await image.read()
        if not content:
            raise RuntimeError("Uploaded image is empty")

        try:
            img = Image.open(BytesIO(content))
        except Exception as exc:
            raise RuntimeError("Failed to read uploaded image") from exc

        text = pytesseract.image_to_string(img, lang=settings.tesseract_lang)
        payload = {
            "engine": "tesseract",
            "language": settings.tesseract_lang,
            "filename": image.filename,
            "text_length": len(text),
        }
        return OcrResult(text=text.strip(), raw=payload)
