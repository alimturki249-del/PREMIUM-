import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
import urllib.parse


def generate_upi_qr(upi_id: str, amount: float, name: str, note: str) -> io.BytesIO:
    """
    Generates a UPI QR code image with a styled border and returns a BytesIO buffer.
    """
    # Build UPI deep-link URI
    params = {
        "pa": upi_id,
        "pn": name,
        "am": f"{amount:.2f}",
        "cu": "INR",
        "tn": note,
    }
    upi_uri = "upi://pay?" + urllib.parse.urlencode(params)

    # Generate QR
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="#1a1a2e", back_color="white").convert("RGB")
    qr_size = qr_img.size[0]

    # Canvas dimensions
    padding = 40
    header_h = 80
    footer_h = 100
    canvas_w = qr_size + padding * 2
    canvas_h = qr_size + padding * 2 + header_h + footer_h

    # Dark background canvas
    canvas = Image.new("RGB", (canvas_w, canvas_h), color="#1a1a2e")
    draw = ImageDraw.Draw(canvas)

    # Header gradient bar (simulated with rectangle)
    draw.rectangle([0, 0, canvas_w, header_h], fill="#16213e")

    # Title text
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_amount = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_amount = font_title
        font_small = font_title

    title_text = "Scan & Pay"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((canvas_w - tw) / 2, 15), title_text, fill="#e0e0ff", font=font_title)

    plan_text = note
    bbox2 = draw.textbbox((0, 0), plan_text, font=font_sub)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((canvas_w - tw2) / 2, 48), plan_text, fill="#a0a0cc", font=font_sub)

    # White card behind QR
    card_x = padding - 10
    card_y = header_h + padding - 10
    card_w = qr_size + 20
    card_h = qr_size + 20
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=16,
        fill="white"
    )

    # Paste QR onto canvas
    canvas.paste(qr_img, (padding, header_h + padding))

    # Footer area
    footer_y = header_h + qr_size + padding * 2

    # Amount
    amount_text = f"₹{amount:.2f}"
    bbox3 = draw.textbbox((0, 0), amount_text, font=font_amount)
    tw3 = bbox3[2] - bbox3[0]
    draw.text(((canvas_w - tw3) / 2, footer_y + 8), amount_text, fill="#00d4aa", font=font_amount)

    # UPI ID
    upi_text = f"UPI: {upi_id}"
    bbox4 = draw.textbbox((0, 0), upi_text, font=font_small)
    tw4 = bbox4[2] - bbox4[0]
    draw.text(((canvas_w - tw4) / 2, footer_y + 50), upi_text, fill="#a0a0cc", font=font_small)

    # Accent line at bottom
    draw.rectangle([20, canvas_h - 6, canvas_w - 20, canvas_h - 2], fill="#00d4aa")

    # Output to bytes
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf
