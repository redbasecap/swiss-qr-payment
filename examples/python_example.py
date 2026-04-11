#!/usr/bin/env python3
"""
Example: Generate Swiss QR-bill payment codes.

Run:
    cd python
    pip install -e ".[all]"
    python ../examples/python_example.py
"""

from swiss_qr_payment import QRBill, Address

# --- 1. QR-Reference bill (QRR) with QR-IBAN ---
bill_qrr = QRBill(
    account="CH44 3199 9123 0008 8901 2",  # QR-IBAN (IID 31999)
    creditor=Address(
        name="Max Muster & Soehne",
        street="Musterstrasse",
        house_number="123",
        postal_code="8000",
        city="Seldwyla",
        country="CH",
    ),
    amount=1949.75,
    currency="CHF",
    reference_type="QRR",
    reference="210000000003139471430009017",
    debtor=Address(
        name="Simon Muster",
        street="Musterstrasse",
        house_number="1",
        postal_code="8000",
        city="Seldwyla",
        country="CH",
    ),
    message="Invoice 2026-001",
)

print("=== QRR Bill (QR-Reference) ===")
print(bill_qrr.to_spc())
print()

# Save QR code as PNG
bill_qrr.to_png("example_qrr.png")
print("Saved: example_qrr.png")

# Render full payment slip PDF (requires reportlab)
try:
    bill_qrr.to_pdf("example_qrr.pdf")
    print("Saved: example_qrr.pdf")
except ImportError:
    print("Skipped PDF (install reportlab: pip install swiss-qr-payment[pdf])")

print()

# --- 2. Creditor Reference bill (SCOR) with regular IBAN ---
bill_scor = QRBill(
    account="CH93 0076 2011 6238 5295 7",  # Regular IBAN
    creditor=Address(
        name="Max Muster & Soehne",
        street="Musterstrasse",
        house_number="123",
        postal_code="8000",
        city="Seldwyla",
        country="CH",
    ),
    amount=199.95,
    currency="CHF",
    reference_type="SCOR",
    reference="RF18539007547034",
)

print("=== SCOR Bill (Creditor Reference) ===")
print(bill_scor.to_spc())
print()

bill_scor.to_png("example_scor.png")
print("Saved: example_scor.png")

# --- 3. Minimal bill (no reference, no amount) ---
bill_minimal = QRBill(
    account="CH93 0076 2011 6238 5295 7",
    creditor=Address(
        name="Max Muster & Soehne",
        street="Musterstrasse",
        house_number="123",
        postal_code="8000",
        city="Seldwyla",
        country="CH",
    ),
    currency="CHF",
)

print("=== Minimal Bill (no reference, no amount) ===")
print(bill_minimal.to_spc())
print()

bill_minimal.to_png("example_minimal.png")
print("Saved: example_minimal.png")
