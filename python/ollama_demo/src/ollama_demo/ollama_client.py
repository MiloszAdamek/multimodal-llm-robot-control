from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


@dataclass(frozen=True)
class OllamaClient:
    base_url: str = "http://localhost:11434"
    timeout_s: int = 120

    def chat(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        format: Optional[str] = "json",
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if format is not None:
            payload["format"] = format

        resp = requests.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        return resp.json()


def encode_image_b64(image_path: str | Path) -> str:
    p = Path(image_path)
    return encode_bytes_b64(p.read_bytes())


def encode_bytes_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
