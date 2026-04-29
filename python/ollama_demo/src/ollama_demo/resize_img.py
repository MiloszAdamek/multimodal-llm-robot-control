from PIL import Image

inp = r".\outputs\snapshot.jpg"
out = r".\outputs\snapshot_224x224.jpg"

img = Image.open(inp).convert("RGB")
img = img.resize((224, 224), Image.BILINEAR)
img.save(out, quality=95)

print("saved:", out)