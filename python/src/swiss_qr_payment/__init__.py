"""
Swiss QR Payment — Generate Swiss QR-bill payment codes (SIX IG v2.3).

Pure Python library for creating standards-compliant Swiss QR payment slips.
No invoice logic, no PDF layout opinions — just the QR-bill data and rendering.

Usage:
    from swiss_qr_payment import QRBill, Address

    bill = QRBill(
        account="CH44 3199 9123 0008 8901 2",
        creditor=Address("Max Muster", "Musterstrasse", "123", "8000", "Seldwyla"),
        amount=1949.75,
        debtor=Address("Simon Muster", "Musterstrasse", "1", "8000", "Seldwyla"),
        reference_type="QRR",
        reference="210000000003139471430009017",
        message="Bezahlung der Reise",
    )

    # Get SPC payload string
    spc = bill.to_spc()

    # Generate QR code image
    bill.to_png("qr.png")

    # Render full payment slip as PDF (A6 or A4-bottom)
    bill.to_pdf("slip.pdf")
"""

__version__ = "1.0.0"

from .bill import QRBill  # noqa: F401
from .address import Address  # noqa: F401
from .validate import validate_iban, validate_qr_reference, validate_creditor_reference  # noqa: F401
