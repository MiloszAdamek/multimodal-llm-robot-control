from ollama_demo.schemas import PerceptionAndCommand


def test_denormalize_bbox_payload_converts_0_1_to_pixels():
    from ollama_demo.pipeline import denormalize_bbox_payload

    payload = {
        "door": {
            "visible": True,
            "bbox": {"x_min": 0.5, "y_min": 0.25, "x_max": 0.75, "y_max": 0.5},
            "heading_deg": None,
        },
        "command": {"action": "stop", "linear_vel_mps": 0.0, "angular_vel_rps": 0.0},
        "confidence": 0.5,
        "notes": "",
    }

    out = denormalize_bbox_payload(payload, width=640, height=480)
    bbox = out["door"]["bbox"]
    assert bbox["x_min"] == 320
    assert bbox["y_min"] == 120
    assert bbox["x_max"] == 480
    assert bbox["y_max"] == 240


def test_schema_validates_minimal_payload():
    payload = {
        "door": {"visible": False, "bbox": None, "heading_deg": None},
        "command": {
            "action": "stop",
            "linear_vel_mps": 0.0,
            "angular_vel_rps": 0.0,
        },
        "confidence": 0.1,
        "notes": "n/a",
    }

    parsed = PerceptionAndCommand.model_validate(payload)
    assert parsed.command.action == "stop"
