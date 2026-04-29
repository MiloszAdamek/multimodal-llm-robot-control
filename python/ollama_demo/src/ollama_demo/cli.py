from __future__ import annotations

import argparse
from pathlib import Path

import requests

from .pipeline import run_inference_ollama, save_json
from .ollama_client import encode_bytes_b64


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Demo: image -> (door detection + motion command) via local Ollama"
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument(
        "--image",
        type=Path,
        default=None,
        help=(
            "Path to an image (jpg/png). Relative paths are resolved from the current working directory. "
            "If omitted, runs a text-only test."
        ),
    )
    src.add_argument(
        "--snapshot-url",
        type=str,
        default=None,
        help=(
            "Snapshot URL from a camera (e.g., ESP32-CAM). "
            "Typically: http://<ip>/capture or /jpg (depends on firmware)."
        ),
    )
    p.add_argument(
        "--task",
        type=str,
        default="Find the nearest door and decide whether the robot should move.",
        help="Task description.",
    )
    p.add_argument(
        "--model",
        type=str,
        default="gemma3",
        help="Model name in Ollama (e.g., gemma3, gemma3:latest, llava).",
    )
    p.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama base URL.",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Generation temperature.",
    )
    p.add_argument(
        "--snapshot-timeout",
        type=float,
        default=10.0,
        help="Timeout (seconds) for fetching the snapshot URL.",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional: write parsed result (JSON) to a file, e.g. outputs/result.json",
    )
    p.add_argument(
        "--raw-out",
        type=Path,
        default=None,
        help="Optional: write raw Ollama response to a file.",
    )
    return p


def main() -> int:
    args = build_arg_parser().parse_args()

    image_b64 = None
    if args.snapshot_url:
        try:
            resp = requests.get(args.snapshot_url, timeout=args.snapshot_timeout)
            resp.raise_for_status()
            image_b64 = encode_bytes_b64(resp.content)
        except requests.RequestException as e:
            print("ERROR: Failed to fetch snapshot:", e)
            return 2

    parsed, raw, err = run_inference_ollama(
        model=args.model,
        task=args.task,
        image_path=args.image,
        image_b64=image_b64,
        base_url=args.ollama_url,
        temperature=args.temperature,
    )

    if args.raw_out:
        save_json(args.raw_out, raw)

    if err:
        print("ERROR:", err)
        content = (raw.get("message") or {}).get("content")
        if isinstance(content, str):
            print("\n--- raw message.content ---\n")
            print(content)
        return 2

    assert parsed is not None
    data = parsed.model_dump()
    print(data)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        save_json(args.out, data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
