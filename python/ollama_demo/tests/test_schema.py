from ollama_demo.schemas import PerceptionAndCommand


def test_schema_validates_minimal_payload():
    payload = {
        "robot": {"visible": False, "bbox": None, "heading_deg": None},
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
