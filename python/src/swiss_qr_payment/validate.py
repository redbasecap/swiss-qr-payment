"""
Validation utilities for Swiss QR-bill fields.

Implements IBAN validation, QR-reference check digit (Modulo 10 recursive),
and Creditor Reference (ISO 11649) validation.
"""

from __future__ import annotations


# ─── IBAN Validation ─────────────────────────────────────────────────────────

def validate_iban(iban: str) -> bool:
    """
    Validate a Swiss/Liechtenstein IBAN using ISO 13616 check digits.

    Returns True if valid, raises ValueError with reason if not.
    """
    clean = iban.replace(" ", "")

    if len(clean) != 21:
        raise ValueError(f"IBAN must be 21 characters, got {len(clean)}")

    if clean[:2] not in ("CH", "LI"):
        raise ValueError(f"Only CH/LI IBANs are allowed, got {clean[:2]}")

    if not clean[2:].replace(clean[:2], "").replace(" ", ""):
        pass  # just a prefix check

    # ISO 13616 modulo 97 check
    rearranged = clean[4:] + clean[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        elif ch.isalpha():
            numeric += str(ord(ch.upper()) - 55)
        else:
            raise ValueError(f"Invalid character in IBAN: {ch!r}")

    if int(numeric) % 97 != 1:
        raise ValueError("IBAN check digit is invalid")

    return True


def is_qr_iban(iban: str) -> bool:
    """Check if an IBAN is a QR-IBAN (IID range 30000–31999)."""
    clean = iban.replace(" ", "")
    try:
        iid = int(clean[4:9])
        return 30000 <= iid <= 31999
    except (ValueError, IndexError):
        return False


def format_iban(iban: str) -> str:
    """Format IBAN with spaces in groups of 4."""
    clean = iban.replace(" ", "")
    return " ".join(clean[i:i+4] for i in range(0, len(clean), 4))


# ─── QR-Reference (Modulo 10 recursive) ─────────────────────────────────────

_MOD10_TABLE = [
    [0, 9, 4, 6, 8, 2, 7, 1, 3, 5],
    [9, 4, 6, 8, 2, 7, 1, 3, 5, 0],
    [4, 6, 8, 2, 7, 1, 3, 5, 0, 9],
    [6, 8, 2, 7, 1, 3, 5, 0, 9, 4],
    [8, 2, 7, 1, 3, 5, 0, 9, 4, 6],
    [2, 7, 1, 3, 5, 0, 9, 4, 6, 8],
    [7, 1, 3, 5, 0, 9, 4, 6, 8, 2],
    [1, 3, 5, 0, 9, 4, 6, 8, 2, 7],
    [3, 5, 0, 9, 4, 6, 8, 2, 7, 1],
    [5, 0, 9, 4, 6, 8, 2, 7, 1, 3],
]


def _mod10_recursive(digits: str) -> int:
    """Calculate Modulo 10 recursive check digit."""
    carry = 0
    for ch in digits:
        carry = _MOD10_TABLE[carry][int(ch)]
    return (10 - carry) % 10


def validate_qr_reference(reference: str) -> bool:
    """
    Validate a QR-Reference (27 digits, Modulo 10 recursive check digit).

    Returns True if valid, raises ValueError if not.
    """
    clean = reference.replace(" ", "")

    if len(clean) != 27:
        raise ValueError(f"QR-Reference must be 27 digits, got {len(clean)}")

    if not clean.isdigit():
        raise ValueError("QR-Reference must be numeric")

    # Check digit is last digit; validate against first 26
    expected_check = _mod10_recursive(clean[:26])
    actual_check = int(clean[26])

    if expected_check != actual_check:
        raise ValueError(
            f"QR-Reference check digit invalid: expected {expected_check}, got {actual_check}"
        )

    return True


def calculate_qr_reference_check_digit(reference_26: str) -> str:
    """
    Calculate the check digit for a 26-digit QR-Reference.

    Returns the complete 27-digit reference.
    """
    clean = reference_26.replace(" ", "")
    if len(clean) != 26 or not clean.isdigit():
        raise ValueError("Input must be exactly 26 digits")
    check = _mod10_recursive(clean)
    return clean + str(check)


def format_qr_reference(reference: str) -> str:
    """Format QR-Reference with spaces: 2 + groups of 5 from right."""
    clean = reference.replace(" ", "")
    groups = []
    rev = clean[::-1]
    for i in range(0, len(rev), 5):
        groups.append(rev[i:i+5][::-1])
    return " ".join(reversed(groups))


# ─── Creditor Reference (ISO 11649, Modulo 97-10) ───────────────────────────

def validate_creditor_reference(reference: str) -> bool:
    """
    Validate a Creditor Reference (ISO 11649).

    Format: RF + 2 check digits + 1–21 alphanumeric reference chars.
    Returns True if valid, raises ValueError if not.
    """
    clean = reference.replace(" ", "")

    if not clean.upper().startswith("RF"):
        raise ValueError("Creditor Reference must start with 'RF'")

    if len(clean) < 5 or len(clean) > 25:
        raise ValueError(f"Creditor Reference must be 5–25 chars, got {len(clean)}")

    # ISO 11649 modulo 97 check
    rearranged = clean[4:] + clean[:4]
    numeric = ""
    for ch in rearranged.upper():
        if ch.isdigit():
            numeric += ch
        elif ch.isalpha():
            numeric += str(ord(ch) - 55)
        else:
            raise ValueError(f"Invalid character: {ch!r}")

    if int(numeric) % 97 != 1:
        raise ValueError("Creditor Reference check digits are invalid")

    return True


def format_creditor_reference(reference: str) -> str:
    """Format Creditor Reference with spaces in groups of 4."""
    clean = reference.replace(" ", "")
    return " ".join(clean[i:i+4] for i in range(0, len(clean), 4))


# ─── Amount Formatting ───────────────────────────────────────────────────────

def format_amount(amount: float) -> str:
    """Format amount with space as thousands separator: 1 234.50."""
    parts = f"{amount:,.2f}".split(".")
    integer_part = parts[0].replace(",", " ")
    return f"{integer_part}.{parts[1]}"
