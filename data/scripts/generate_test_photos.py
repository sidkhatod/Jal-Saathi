import os
from PIL import Image, ImageDraw

out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web", "public", "test_assets"))
os.makedirs(out_dir, exist_ok=True)

# 1. Good sharp photo (high contrast edges, leaf texture, good brightness)
for i in range(1, 4):
    img = Image.new('RGB', (300, 300), color=(110, 160, 120))
    draw = ImageDraw.Draw(img)
    for x in range(0, 300, 20):
        draw.line([(x, 0), (x, 300)], fill=(30, 80, 40), width=3)
    for y in range(0, 300, 20):
        draw.line([(0, y), (300, y)], fill=(40, 100, 50), width=2)
    img.save(os.path.join(out_dir, f"good_photo_{i}.jpg"), quality=95)

# 2. Blurry / Dark photo (uniform dark gray, no high-frequency edges)
dark_img = Image.new('RGB', (300, 300), color=(20, 25, 20))
dark_img.save(os.path.join(out_dir, "blurry_dark.jpg"), quality=95)

print(f"[OK] Generated test photos in {out_dir}")
