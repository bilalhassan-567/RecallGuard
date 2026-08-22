"""One-off generator for a synthetic 'photographed invoice' test image — simulates a
phone photo of a printed paper invoice (slight rotation, mild noise/blur) so the
multimodal extraction path has something real to run against. This is NOT a substitute
for a genuine photographed invoice before the actual demo recording (see docs/PHASES.md,
Phase 4) — it's here to validate the code works at all before that.

Run once: python generate_test_invoice_image.py
"""
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT_PATH = "invoices/photo_006_true_positive.jpg"

LINES = [
    "GARCIA WHOLESALE FOODS - DELIVERY RECEIPT",
    "Date: 08/19/2026      Account: 4471-B",
    "",
    "QTY   ITEM                              UNIT",
    "3     Selectos Latinos Requeson 16oz     case",
    "2     Corn Tortillas 12in 24ct           case",
    "5     Black Beans Canned 15oz            case",
    "1     Jalapeno Peppers Fresh 10lb        box",
    "4     Shredded Cheddar 5lb               bag",
    "",
    "Received by: _______________",
]


def main() -> None:
    img = Image.new("RGB", (900, 700), color=(250, 248, 244))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("cour.ttf", 22)  # Courier New on Windows — printed-receipt look
    except OSError:
        font = ImageFont.load_default()

    y = 40
    for line in LINES:
        draw.text((50, y), line, fill=(20, 20, 20), font=font)
        y += 34

    # Simulate photo conditions: slight rotation + mild blur + light noise.
    img = img.rotate(-2.5, expand=True, fillcolor=(250, 248, 244))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))

    pixels = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.02)):
        x, y = random.randint(0, w - 1), random.randint(0, h - 1)
        r, g, b = pixels[x, y]
        noise = random.randint(-15, 15)
        pixels[x, y] = (max(0, min(255, r + noise)), max(0, min(255, g + noise)), max(0, min(255, b + noise)))

    img.save(OUTPUT_PATH, quality=85)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
