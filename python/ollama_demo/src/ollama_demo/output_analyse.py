import json
from PIL import Image, ImageDraw

image_path = r".\outputs\snapshot_672x672.jpg"
parsed_path = r".\outputs\parsed.json"
out_path = r".\outputs\annotated.png"

with open(parsed_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

bbox = payload["door"]["bbox"]

img = Image.open(image_path).convert("RGB")

if bbox:
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = bbox["x_min"], bbox["y_min"], bbox["x_max"], bbox["y_max"]
    draw.rectangle([x1, y1, x2, y2], outline="red", width=4)

img.save(out_path)
print("saved:", out_path)