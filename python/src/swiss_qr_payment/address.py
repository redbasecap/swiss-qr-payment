"""
Structured address (type S) per SIX Implementation Guidelines QR-Rechnung v2.3.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    """
    Swiss QR-bill structured address.

    Uses address type "S" with separate fields for street, house number,
    postal code, city, and country. This is the only address type allowed
    since November 2025 (combined type "K" was deprecated).

    Args:
        name: Name or company (max 70 chars).
        street: Street name (max 70 chars). Optional.
        house_number: House/building number (max 16 chars). Optional.
        postal_code: Postal/zip code (max 16 chars). Required if city given.
        city: City/town name (max 35 chars). Required if postal_code given.
        country: 2-letter ISO 3166-1 country code. Default: "CH".
    """
    name: str
    street: str = ""
    house_number: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = "CH"

    def __post_init__(self):
        _check_len(self.name, 70, "name")
        _check_len(self.street, 70, "street")
        _check_len(self.house_number, 16, "house_number")
        _check_len(self.postal_code, 16, "postal_code")
        _check_len(self.city, 35, "city")
        if len(self.country) != 2:
            raise ValueError(f"country must be 2-letter ISO code, got: {self.country!r}")
        if not self.name:
            raise ValueError("name is required")

    @classmethod
    def from_dict(cls, d: dict) -> "Address":
        """
        Create an Address from a dict.

        Accepts either separate postal_code/city fields or a combined
        zip_city field ("8400 Winterthur").
        """
        if "zip_city" in d and "postal_code" not in d:
            parts = d["zip_city"].strip().split(" ", 1)
            return cls(
                name=d["name"],
                street=d.get("street", ""),
                house_number=d.get("house_number", ""),
                postal_code=parts[0] if parts else "",
                city=parts[1] if len(parts) > 1 else "",
                country=d.get("country", "CH"),
            )
        return cls(
            name=d["name"],
            street=d.get("street", ""),
            house_number=d.get("house_number", ""),
            postal_code=d.get("postal_code", ""),
            city=d.get("city", ""),
            country=d.get("country", "CH"),
        )

    @property
    def display_lines(self) -> list[str]:
        """Human-readable address lines for printing on the payment slip."""
        lines = [self.name]
        street_line = f"{self.street} {self.house_number}".strip()
        if street_line:
            lines.append(street_line)
        zip_city = f"{self.postal_code} {self.city}".strip()
        if zip_city:
            prefix = f"{self.country}-" if self.country not in ("CH", "LI") else ""
            lines.append(f"{prefix}{zip_city}")
        return lines

    def to_spc_fields(self) -> list[str]:
        """Return the 7 SPC data fields for this address."""
        return [
            "S",
            self.name,
            self.street,
            self.house_number,
            self.postal_code,
            self.city,
            self.country,
        ]

    @staticmethod
    def empty_spc_fields() -> list[str]:
        """Return 7 empty fields (for when no address is provided)."""
        return ["", "", "", "", "", "", ""]


def _check_len(value: str, max_len: int, field: str):
    if len(value) > max_len:
        raise ValueError(f"{field} exceeds {max_len} chars ({len(value)}): {value!r}")
