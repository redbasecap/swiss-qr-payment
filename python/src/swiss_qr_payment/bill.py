"""
Core QR-bill data container and output generator.

Implements the Swiss Payment Code (SPC) data format per SIX IG v2.3
and provides output methods for QR images, PDFs, and SVGs.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from .address import Address
from .validate import (
    validate_iban,
    is_qr_iban,
    validate_qr_reference,
    validate_creditor_reference,
    format_iban,
    format_amount,
    format_qr_reference,
    format_creditor_reference,
)


@dataclass
class QRBill:
    """
    Swiss QR-bill payment data.

    Validates all fields according to SIX IG v2.3, builds the SPC
    (Swiss Payments Code) payload, and generates QR code images
    and PDF payment slips.

    Args:
        account: CH/LI IBAN (21 chars, spaces allowed).
        creditor: Creditor address (payable to).
        amount: Payment amount (0.01–999999999.99). None for open amount.
        currency: "CHF" or "EUR".
        debtor: Debtor address (payable by). None for open debtor.
        reference_type: "QRR" (QR-Reference), "SCOR" (Creditor Ref), or "NON".
        reference: Reference number (required for QRR/SCOR).
        message: Unstructured message (max 140 chars).
        billing_info: Structured billing info (max 140 chars).
        alt_procedures: Alternative procedure parameters (max 2, each max 100 chars).
        language: Display language: "de", "fr", "it", or "en".
    """
    account: str
    creditor: Address
    amount: Optional[float] = None
    currency: str = "CHF"
    debtor: Optional[Address] = None
    reference_type: str = "NON"
    reference: str = ""
    message: str = ""
    billing_info: str = ""
    alt_procedures: list[str] = field(default_factory=list)
    language: str = "de"

    def __post_init__(self):
        # Normalize and validate IBAN
        self.account = self.account.replace(" ", "")
        validate_iban(self.account)

        # Currency
        if self.currency not in ("CHF", "EUR"):
            raise ValueError(f"Currency must be CHF or EUR, got: {self.currency!r}")

        # Amount
        if self.amount is not None:
            if not (0.01 <= self.amount <= 999999999.99):
                raise ValueError(f"Amount must be 0.01–999'999'999.99, got: {self.amount}")

        # Reference type vs IBAN type
        if self.reference_type not in ("QRR", "SCOR", "NON"):
            raise ValueError(f"reference_type must be QRR/SCOR/NON, got: {self.reference_type!r}")

        if is_qr_iban(self.account):
            if self.reference_type != "QRR":
                raise ValueError("QR-IBAN requires reference_type='QRR'")
        else:
            if self.reference_type == "QRR":
                raise ValueError("QRR reference requires a QR-IBAN (IID 30000–31999)")

        # Validate reference
        if self.reference_type == "QRR" and self.reference:
            validate_qr_reference(self.reference)
        elif self.reference_type == "SCOR" and self.reference:
            validate_creditor_reference(self.reference)
        elif self.reference_type == "NON" and self.reference:
            raise ValueError("NON reference_type must have empty reference")

        # Message length
        total_info = len(self.message) + len(self.billing_info)
        if total_info > 140:
            raise ValueError(f"message + billing_info must be ≤ 140 chars, got: {total_info}")

        # Alt procedures
        if len(self.alt_procedures) > 2:
            raise ValueError("Maximum 2 alternative procedures allowed")
        for ap in self.alt_procedures:
            if len(ap) > 100:
                raise ValueError(f"Alt procedure parameter exceeds 100 chars: {len(ap)}")

        # Language
        if self.language not in ("de", "fr", "it", "en"):
            raise ValueError(f"language must be de/fr/it/en, got: {self.language!r}")

    # ─── SPC Data ─────────────────────────────────────────────────────────

    def to_spc(self) -> str:
        """
        Build the Swiss Payments Code (SPC) data string.

        This is the data encoded in the QR code. Format per SIX IG v2.3,
        Chapter 4.2.2 "Datenelemente in der QR-Rechnung".
        """
        lines: list[str] = []

        # Header (3 lines)
        lines.append("SPC")                                # QRType
        lines.append("0200")                               # Version
        lines.append("1")                                  # Coding (UTF-8)

        # Creditor information (8 lines: IBAN + 7 address fields)
        lines.append(self.account)
        lines.extend(self.creditor.to_spc_fields())

        # Ultimate creditor — must not be filled (7 empty lines)
        lines.extend(Address.empty_spc_fields())

        # Payment amount (2 lines)
        lines.append(f"{self.amount:.2f}" if self.amount is not None else "")
        lines.append(self.currency)

        # Debtor (7 lines)
        if self.debtor:
            lines.extend(self.debtor.to_spc_fields())
        else:
            lines.extend(Address.empty_spc_fields())

        # Reference (2 lines)
        lines.append(self.reference_type)
        lines.append(self.reference)

        # Additional information (2 lines)
        lines.append(self.message)
        lines.append("EPD")                                # Trailer

        # Billing info (1 line)
        lines.append(self.billing_info)

        # Alternative procedures (0–2 lines)
        for ap in self.alt_procedures:
            lines.append(ap)

        return "\n".join(lines)

    # ─── QR Code Output ──────────────────────────────────────────────────

    def qr_image(self, box_size: int = 10):
        """
        Generate QR code as a PIL Image object.

        Returns a PIL Image (requires qrcode[pil] package).
        """
        import qrcode

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=0,
        )
        qr.add_data(self.to_spc())
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")

    def to_png(self, path: Union[str, Path], size: int = 1000):
        """Save QR code as PNG file."""
        img = self.qr_image(box_size=10)
        img = img.resize((size, size))
        img.save(str(path), format="PNG")

    def to_svg(self, path: Union[str, Path]):
        """Save QR code as SVG file."""
        import qrcode
        import qrcode.image.svg

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=0,
        )
        qr.add_data(self.to_spc())
        qr.make(fit=True)
        img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        img.save(str(path))

    def to_bytes(self, format: str = "png", size: int = 1000) -> bytes:
        """Get QR code as bytes (for embedding in web apps, APIs, etc.)."""
        buf = io.BytesIO()
        img = self.qr_image(box_size=10)
        if format.lower() == "png":
            img = img.resize((size, size))
        img.save(buf, format=format.upper())
        return buf.getvalue()

    # ─── PDF Payment Slip ────────────────────────────────────────────────

    def to_pdf(self, path: Union[str, Path], full_page: bool = True):
        """
        Generate a PDF with the complete QR-bill payment slip.

        Args:
            path: Output PDF file path.
            full_page: If True, renders on A4 at the bottom (105mm).
                       If False, renders as standalone A6-landscape slip.
        """
        from .pdf_renderer import render_qr_bill_pdf
        render_qr_bill_pdf(self, str(path), full_page=full_page)

    # ─── Convenience Properties ──────────────────────────────────────────

    @property
    def formatted_account(self) -> str:
        """IBAN formatted with spaces."""
        return format_iban(self.account)

    @property
    def formatted_amount(self) -> Optional[str]:
        """Amount formatted with space thousands separator."""
        return format_amount(self.amount) if self.amount is not None else None

    @property
    def formatted_reference(self) -> str:
        """Reference formatted with spaces."""
        if self.reference_type == "QRR":
            return format_qr_reference(self.reference)
        elif self.reference_type == "SCOR":
            return format_creditor_reference(self.reference)
        return self.reference

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        d = {
            "account": self.account,
            "creditor": {
                "name": self.creditor.name,
                "street": self.creditor.street,
                "house_number": self.creditor.house_number,
                "postal_code": self.creditor.postal_code,
                "city": self.creditor.city,
                "country": self.creditor.country,
            },
            "currency": self.currency,
            "reference_type": self.reference_type,
            "language": self.language,
        }
        if self.amount is not None:
            d["amount"] = self.amount
        if self.debtor:
            d["debtor"] = {
                "name": self.debtor.name,
                "street": self.debtor.street,
                "house_number": self.debtor.house_number,
                "postal_code": self.debtor.postal_code,
                "city": self.debtor.city,
                "country": self.debtor.country,
            }
        if self.reference:
            d["reference"] = self.reference
        if self.message:
            d["message"] = self.message
        if self.billing_info:
            d["billing_info"] = self.billing_info
        if self.alt_procedures:
            d["alt_procedures"] = self.alt_procedures
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "QRBill":
        """Create a QRBill from a dictionary."""
        creditor = Address.from_dict(d["creditor"])
        debtor = Address.from_dict(d["debtor"]) if "debtor" in d else None
        return cls(
            account=d["account"],
            creditor=creditor,
            amount=d.get("amount"),
            currency=d.get("currency", "CHF"),
            debtor=debtor,
            reference_type=d.get("reference_type", "NON"),
            reference=d.get("reference", ""),
            message=d.get("message", ""),
            billing_info=d.get("billing_info", ""),
            alt_procedures=d.get("alt_procedures", []),
            language=d.get("language", "de"),
        )
