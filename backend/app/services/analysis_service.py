import json

import ollama

from app.core.config import settings


client = ollama.Client(host=settings.ollama_base_url)


class AnalysisService:
    def analyze_auto_route(self, ocr_text: str) -> dict:
        prompt = (
            "You are a payment-routing assistant. "
            'Fill the JSON with: feature_selected="Pembelian Pulsa", number="081234567890", nominal=50000. '
            "Return ONLY valid JSON with keys: "
            "feature_selected, number, nominal. "
            "The number value must be a string. "
            f"OCR text:\n{ocr_text}"
        )
        return self._ask_for_json(prompt)

    def analyze_split_bill(self, ocr_text: str) -> dict:
        prompt = (
            "You are a split-bill assistant. "
            "Convert OCR text into JSON breakdown. Return ONLY valid JSON with keys: "
            "merchant, bill_name, currency, subtotal, tax, service_charge, total, items, participants. "
            "Each item should include name, qty, price, assigned_to (array). "
            f"OCR text:\n{ocr_text}"
        )
        return self._ask_for_json(prompt)

    def _ask_for_json(self, prompt: str) -> dict:
        response = client.chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response["message"]["content"].strip()
        return _safe_parse_json(content)


def _safe_parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"raw": raw}

        candidate = raw[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return {"raw": raw}
