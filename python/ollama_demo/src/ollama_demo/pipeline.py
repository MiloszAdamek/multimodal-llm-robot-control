from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from .ollama_client import OllamaClient, encode_image_b64
from .schemas import PerceptionAndCommand


SYSTEM_PROMPT_PL = (
    "Jesteś modułem sterowania robotem mobilnym. "
    "Dostajesz obraz z kamery oraz opis zadania. "
    "Twoim celem jest: (1) oszacować położenie robota w obrazie (jeśli widoczny), "
    "(2) wydać bezpieczną komendę ruchu. "
    "Jeśli nie jesteś pewny/robot jest niewidoczny, ustaw action=stop i confidence nisko. "
    "Zwróć WYŁĄCZNIE poprawny JSON zgodny z tym schematem: "
    "{robot:{visible:bool,bbox:{x_min:int,y_min:int,x_max:int,y_max:int}|null,heading_deg:number|null}, "
    "command:{action:move|stop|turn_left|turn_right|unknown,linear_vel_mps:number,angular_vel_rps:number}, "
    "confidence:number, notes:string}."
)


def build_messages(task: str, image_b64: Optional[str]) -> list[dict[str, Any]]:
    user_content = (
        "ZADANIE: " + task.strip() + "\n\n" + "Jeśli na obrazie widać robota, "
        "podaj bbox w pikselach (x_min,y_min,x_max,y_max) oraz przybliżony heading."
    )

    if image_b64 is None:
        return [
            {"role": "system", "content": SYSTEM_PROMPT_PL},
            {"role": "user", "content": user_content},
        ]

    return [
        {"role": "system", "content": SYSTEM_PROMPT_PL},
        {
            "role": "user",
            "content": user_content,
            "images": [image_b64],
        },
    ]


def run_inference_ollama(
    *,
    model: str,
    task: str,
    image_path: Optional[str] = None,
    image_b64: Optional[str] = None,
    base_url: str,
    temperature: float = 0.2,
) -> tuple[Optional[PerceptionAndCommand], Dict[str, Any], Optional[str]]:
    client = OllamaClient(base_url=base_url)

    if image_path and image_b64:
        return None, {}, "Podaj tylko jedno z: image_path albo image_b64."

    resolved_image_b64 = image_b64 or (encode_image_b64(image_path) if image_path else None)
    messages = build_messages(task=task, image_b64=resolved_image_b64)

    raw = client.chat(
        model=model,
        messages=messages,
        format="json",
        temperature=temperature,
    )

    content = (raw.get("message") or {}).get("content")
    if not isinstance(content, str):
        return None, raw, "Brak pola message.content w odpowiedzi Ollama."

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as e:
        return None, raw, f"Model nie zwrócił poprawnego JSON: {e}"

    try:
        parsed = PerceptionAndCommand.model_validate(payload)
    except ValidationError as e:
        return None, raw, f"JSON nie pasuje do schematu: {e}"

    return parsed, raw, None


def save_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
