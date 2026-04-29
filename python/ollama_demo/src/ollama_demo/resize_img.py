from pathlib import Path

from PIL import Image

inp = Path("outputs") / "snapshot.jpg"
out = Path("outputs") / "snapshot_224x224.jpg"

img = Image.open(inp).convert("RGB")
img = img.resize((224, 224), Image.BILINEAR)
img.save(out, quality=95)

print("saved:", out)