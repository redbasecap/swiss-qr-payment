"""
PDF renderer for Swiss QR-bill payment slips.

Generates norm-compliant payment slips (Zahlteil + Empfangsschein)
per SIX Implementation Guidelines QR-Rechnung v2.3.

Layout:
- Total width: 210 mm (A4 width)
- Total height: 105 mm
- Empfangsschein: 62 mm wide (left)
- Zahlteil: 148 mm wide (right)
- QR code: 46 × 46 mm, Swiss cross 7 × 7 mm centered
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

if TYPE_CHECKING:
    from .bill import QRBill

# ─── Layout Constants ────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4
RECEIPT_W = 62 * mm
SECTION_H = 105 * mm
QR_SIZE = 46 * mm
CROSS_SIZE = 7 * mm

# Multilingual labels (SIX IG v2.3, Anhang C)
LABELS = {
    "de": {
        "receipt": "Empfangsschein", "payment": "Zahlteil",
        "account": "Konto / Zahlbar an", "reference": "Referenz",
        "additional_info": "Zusätzliche Informationen",
        "payable_by": "Zahlbar durch",
        "payable_by_box": "Zahlbar durch (Name/Adresse)",
        "currency": "Währung", "amount": "Betrag",
        "acceptance": "Annahmestelle",
    },
    "fr": {
        "receipt": "Récépissé", "payment": "Section paiement",
        "account": "Compte / Payable à", "reference": "Référence",
        "additional_info": "Informations supplémentaires",
        "payable_by": "Payable par",
        "payable_by_box": "Payable par (nom/adresse)",
        "currency": "Monnaie", "amount": "Montant",
        "acceptance": "Point de dépôt",
    },
    "it": {
        "receipt": "Ricevuta", "payment": "Sezione pagamento",
        "account": "Conto / Pagabile a", "reference": "Riferimento",
        "additional_info": "Informazioni supplementari",
        "payable_by": "Pagabile da",
        "payable_by_box": "Pagabile da (nome/indirizzo)",
        "currency": "Valuta", "amount": "Importo",
        "acceptance": "Punto di accettazione",
    },
    "en": {
        "receipt": "Receipt", "payment": "Payment part",
        "account": "Account / Payable to", "reference": "Reference",
        "additional_info": "Additional information",
        "payable_by": "Payable by",
        "payable_by_box": "Payable by (name/address)",
        "currency": "Currency", "amount": "Amount",
        "acceptance": "Acceptance point",
    },
}


def render_qr_bill_pdf(bill: "QRBill", path: str, full_page: bool = True):
    """Render a QR-bill payment slip as PDF."""
    from .validate import format_iban, format_amount, format_qr_reference, format_creditor_reference

    labels = LABELS.get(bill.language, LABELS["de"])

    if full_page:
        c = canvas.Canvas(path, pagesize=A4)
    else:
        # A6 landscape: 148 × 105 mm (just the slip)
        c = canvas.Canvas(path, pagesize=(210 * mm, SECTION_H))

    # ── Perforation lines ──
    c.setStrokeColor(black)
    c.setLineWidth(0.4)
    c.setDash(2, 2)
    if full_page:
        c.line(0, SECTION_H, PAGE_W, SECTION_H)
    c.line(RECEIPT_W, 0, RECEIPT_W, SECTION_H)
    c.setDash()

    # Scissors
    c.setFont("Helvetica", 8)
    c.setFillColor(black)
    c.drawString(RECEIPT_W - 3, SECTION_H + 2, "\u2702")
    if full_page:
        c.drawRightString(PAGE_W - 3 * mm, SECTION_H + 2, "\u2702")

    # ── Empfangsschein (Receipt, left 62mm) ──
    _draw_receipt(c, bill, labels)

    # ── Zahlteil (Payment part, right 148mm) ──
    _draw_payment(c, bill, labels)

    c.save()


def _draw_receipt(c, bill, labels):
    x = 5 * mm
    y = SECTION_H - 12 * mm

    # Title
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(black)
    c.drawString(x, y, labels["receipt"])

    # Account / Payable to
    y -= 14
    c.setFont("Helvetica-Bold", 6)
    c.drawString(x, y, labels["account"])
    y -= 9
    c.setFont("Helvetica", 8)
    c.drawString(x, y, bill.formatted_account)
    for line in bill.creditor.display_lines:
        y -= 9
        c.drawString(x, y, line)

    # Reference
    if bill.reference and bill.reference_type != "NON":
        y -= 12
        c.setFont("Helvetica-Bold", 6)
        c.drawString(x, y, labels["reference"])
        y -= 9
        c.setFont("Helvetica", 8)
        c.drawString(x, y, bill.formatted_reference)

    # Payable by
    if bill.debtor:
        y -= 12
        c.setFont("Helvetica-Bold", 6)
        c.drawString(x, y, labels["payable_by"])
        y -= 9
        c.setFont("Helvetica", 8)
        for line in bill.debtor.display_lines:
            c.drawString(x, y, line)
            y -= 9
    else:
        y -= 12
        c.setFont("Helvetica-Bold", 6)
        c.drawString(x, y, labels["payable_by_box"])
        y -= 2
        _draw_corner_box(c, x, y - 25 * mm, 52 * mm, 25 * mm)

    # Currency + Amount
    by = 15 * mm
    c.setFont("Helvetica-Bold", 6)
    c.drawString(x, by + 10, labels["currency"])
    c.drawString(x + 18 * mm, by + 10, labels["amount"])
    c.setFont("Helvetica", 8)
    c.drawString(x, by, bill.currency)
    if bill.amount is not None:
        c.drawString(x + 18 * mm, by, bill.formatted_amount)
    else:
        _draw_corner_box(c, x + 18 * mm, by - 2, 30 * mm, 10 * mm)

    # Acceptance point
    c.setFont("Helvetica-Bold", 6)
    c.drawRightString(RECEIPT_W - 5 * mm, 15 * mm, labels["acceptance"])


def _draw_payment(c, bill, labels):
    bx = RECEIPT_W + 5 * mm
    y = SECTION_H - 12 * mm

    # Title
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(black)
    c.drawString(bx, y, labels["payment"])

    # QR Code
    qr_img = _make_qr_image(bill)
    qr_x = bx
    qr_y = y - 15 * mm - QR_SIZE
    c.drawImage(qr_img, qr_x, qr_y, QR_SIZE, QR_SIZE)

    # Swiss cross
    _draw_swiss_cross(c, qr_x + QR_SIZE / 2, qr_y + QR_SIZE / 2)

    # Details (right of QR)
    dx = bx + QR_SIZE + 5 * mm
    dy = y - 15 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(dx, dy, labels["account"])
    dy -= 11
    c.setFont("Helvetica", 10)
    c.drawString(dx, dy, bill.formatted_account)
    for line in bill.creditor.display_lines:
        dy -= 11
        c.drawString(dx, dy, line)

    # Reference
    if bill.reference and bill.reference_type != "NON":
        dy -= 14
        c.setFont("Helvetica-Bold", 8)
        c.drawString(dx, dy, labels["reference"])
        dy -= 11
        c.setFont("Helvetica", 10)
        c.drawString(dx, dy, bill.formatted_reference)

    # Additional info
    if bill.message:
        dy -= 14
        c.setFont("Helvetica-Bold", 8)
        c.drawString(dx, dy, labels["additional_info"])
        dy -= 11
        c.setFont("Helvetica", 10)
        for msg_line in bill.message.split("\n"):
            c.drawString(dx, dy, msg_line)
            dy -= 11

    # Payable by
    if bill.debtor:
        dy -= 8
        c.setFont("Helvetica-Bold", 8)
        c.drawString(dx, dy, labels["payable_by"])
        dy -= 11
        c.setFont("Helvetica", 10)
        for line in bill.debtor.display_lines:
            c.drawString(dx, dy, line)
            dy -= 11
    else:
        dy -= 8
        c.setFont("Helvetica-Bold", 8)
        c.drawString(dx, dy, labels["payable_by_box"])
        dy -= 2
        max_w = PAGE_W - 10 * mm - dx
        _draw_corner_box(c, dx, dy - 35 * mm, max_w, 35 * mm)

    # Currency + Amount
    by = 15 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(bx, by + 12, labels["currency"])
    c.drawString(bx + 22 * mm, by + 12, labels["amount"])
    c.setFont("Helvetica", 10)
    c.drawString(bx, by, bill.currency)
    if bill.amount is not None:
        c.drawString(bx + 22 * mm, by, bill.formatted_amount)
    else:
        _draw_corner_box(c, bx + 22 * mm, by - 2, 40 * mm, 12 * mm)

    # Alternative procedures
    if bill.alt_procedures:
        alt_y = 5 * mm
        c.setFont("Helvetica", 7)
        for ap in bill.alt_procedures[:2]:
            c.drawString(bx, alt_y, ap)
            alt_y -= 8


def _make_qr_image(bill) -> ImageReader:
    """Generate QR code image for embedding in PDF."""
    import qrcode

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=0,
    )
    qr.add_data(bill.to_spc())
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _draw_swiss_cross(c, cx: float, cy: float):
    """Draw the Swiss cross at the center of the QR code."""
    s = CROSS_SIZE
    x, y = cx - s / 2, cy - s / 2

    c.setFillColor(black)
    c.rect(x, y, s, s, fill=1, stroke=0)

    c.setFillColor(white)
    bw, bh = s * 0.35, s * 0.7
    c.rect(x + (s - bw) / 2, y + (s - bh) / 2, bw, bh, fill=1, stroke=0)
    c.rect(x + (s - bh) / 2, y + (s - bw) / 2, bh, bw, fill=1, stroke=0)


def _draw_corner_box(c, x: float, y: float, w: float, h: float):
    """Draw corner marks for empty input fields per SIX spec."""
    c.saveState()
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    m = 3 * mm

    c.line(x, y + h, x + m, y + h)
    c.line(x, y + h, x, y + h - m)
    c.line(x + w - m, y + h, x + w, y + h)
    c.line(x + w, y + h, x + w, y + h - m)
    c.line(x, y, x + m, y)
    c.line(x, y, x, y + m)
    c.line(x + w - m, y, x + w, y)
    c.line(x + w, y, x + w, y + m)

    c.restoreState()
