from __future__ import annotations

import json
import base64
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from .ollama_client import OllamaClient, encode_image_b64
from .schemas import PerceptionAndCommand


SYSTEM_PROMPT = (
    "You are a mobile robot control module. "
    "You receive a camera image mounted on the robot and a task description. "
    "Your goal is: (1) find the nearest door in the image (if visible), "
    "(2) output a safe motion command. "
    "If you are unsure, set action=stop and keep confidence low. "
    "Return ONLY valid JSON matching this schema. "
    "IMPORTANT: bbox coordinates MUST be integer pixel coordinates in the input image (NOT 0..1 normalized). "
    "Schema: "
    "{door:{visible:bool,bbox:{x_min:int,y_min:int,x_max:int,y_max:int}|null,heading_deg:number|null}, "
    "command:{action:move|stop|turn_left|turn_right|unknown,linear_vel_mps:number,angular_vel_rps:number}, "
    "confidence:number, notes:string}."
)


def denormalize_bbox_payload(payload: Dict[str, Any], *, width: int, height: int) -> Dict[str, Any]:
    """Convert normalized bbox coords (0..1 floats) into pixel ints in-place.

    Some VLMs (e.g., LLaVA) may output normalized coordinates even if prompted for pixels.
    This helper detects that case and converts to integer pixel coordinates.
    """

    door = payload.get("door")
    if not isinstance(door, dict):
        return payload

    bbox = door.get("bbox")
    if bbox is None or not isinstance(bbox, dict):
        return payload

    keys = ("x_min", "y_min", "x_max", "y_max")
    values: list[float] = []
    for k in keys:
        v = bbox.get(k)
        if not isinstance(v, (int, float)):
            return payload
        values.append(float(v))

    # Heuristic: treat as normalized if all values are between 0 and 1 (inclusive).
    # If the model returns pixel coordinates, they will typically be > 1.
    if not all(0.0 <= v <= 1.0 for v in values):
        return payload

    def clamp_int(n: int, lo: int, hi: int) -> int:
        return max(lo, min(hi, n))

    x1 = clamp_int(int(round(values[0] * width)), 0, max(0, width - 1))
    y1 = clamp_int(int(round(values[1] * height)), 0, max(0, height - 1))
    x2 = clamp_int(int(round(values[2] * width)), 0, max(0, width - 1))
    y2 = clamp_int(int(round(values[3] * height)), 0, max(0, height - 1))

    # Ensure min/max ordering
    bbox["x_min"], bbox["x_max"] = sorted((x1, x2))
    bbox["y_min"], bbox["y_max"] = sorted((y1, y2))
    return payload


def _get_image_size(
    *,
    image_path: Optional[str | Path],
    image_b64: Optional[str],
) -> Optional[tuple[int, int]]:
    try:
        from PIL import Image
    except Exception:
        return None

    if image_path:
        try:
            with Image.open(image_path) as img:
                w, h = img.size
            return int(w), int(h)
        except Exception:
            return None

    if image_b64:
        try:
            raw_bytes = base64.b64decode(image_b64)
            from io import BytesIO

            with Image.open(BytesIO(raw_bytes)) as img:
                w, h = img.size
            return int(w), int(h)
        except Exception:
            return None

    return None


def build_messages(task: str, image_b64: Optional[str]) -> list[dict[str, Any]]:

    user_content = (
        "TASK: " + task.strip() + "\n\n" + "The robot's first goal is to leave the room;"
        " locate the nearest door (if visible) and estimate the heading to drive through it."
    )

    if image_b64 is None:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
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
    image_path: Optional[str | Path] = None,
    image_b64: Optional[str] = None,
    base_url: str,
    temperature: float = 0.2,
) -> tuple[Optional[PerceptionAndCommand], Dict[str, Any], Optional[str]]:
    client = OllamaClient(base_url=base_url)

    if image_path and image_b64:
        return None, {}, "Provide only one of: image_path or image_b64."

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
        return None, raw, "Missing message.content in the Ollama response."

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as e:
        return None, raw, f"Model did not return valid JSON: {e}"

    size = _get_image_size(image_path=image_path, image_b64=resolved_image_b64)
    if size is not None:
        w, h = size
        payload = denormalize_bbox_payload(payload, width=w, height=h)

    try:
        parsed = PerceptionAndCommand.model_validate(payload)
    except ValidationError as e:
        return None, raw, f"JSON does not match schema: {e}"

    return parsed, raw, None


def save_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
