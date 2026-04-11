# swiss-qr-payment

Swiss QR-bill payment library — compliant with [SIX Implementation Guidelines v2.3](https://www.six-group.com/dam/download/banking-services/standardization/qr-bill/ig-qr-bill-v2.3-en.pdf).

Available in **Python** and **Rust**.

## Features

- IBAN validation (CH/LI, ISO 13616 Modulo 97)
- QR-IBAN detection (IID range 30000–31999)
- QR-Reference validation & check digit calculation (27-digit, Modulo 10 recursive)
- Creditor Reference validation (ISO 11649, Modulo 97-10)
- Structured address handling (type S per SIX spec)
- Swiss Payments Code (SPC) payload generation
- QR code output (PNG)
- PDF payment slip rendering (Python only, via reportlab)
- Builder pattern API (Rust) / dataclass API (Python)
- Full test coverage

## Quick Start

### Python

```bash
pip install swiss-qr-payment
# For PDF rendering:
pip install swiss-qr-payment[pdf]
```

```python
from swiss_qr_payment import QRBill, Address

bill = QRBill(
    account="CH93 0076 2011 6238 5295 7",
    creditor=Address(
        name="Max Muster & Söhne",
        street="Musterstrasse",
        house_number="123",
        postal_code="8000",
        city="Seldwyla",
        country="CH",
    ),
    amount=1949.75,
    currency="CHF",
)

# SPC payload for QR code
print(bill.to_spc())

# Save QR code as PNG
bill.to_png("qr.png")

# Render full payment slip PDF (requires reportlab)
bill.to_pdf("slip.pdf")
```

### Rust

```toml
[dependencies]
swiss-qr-payment = "1.0"
```

```rust
use swiss_qr_payment::{QRBill, Address};

let bill = QRBill::new(
    "CH9300762011623852957",
    Address::new("Max Muster & Söhne", "Musterstrasse", "123", "8000", "Seldwyla", "CH"),
)
.amount(1949.75)
.build()
.unwrap();

// SPC payload
println!("{}", bill.to_spc());

// Save QR code PNG
bill.save_png("qr.png", 400).unwrap();
```

## Examples

See [`examples/`](examples/) for complete working examples (QRR, SCOR, minimal bill).

```bash
# Python
cd python
pip install -e ".[all]"
python ../examples/python_example.py
```

## Development

### Python

```bash
cd python
pip install -e ".[all]"

# Run tests
pytest tests/

# Lint
ruff check src/ tests/
```

### Rust

```bash
cd rust

# Run tests
cargo test

# Clippy lint
cargo clippy
```

## Reference Types

| Type | Description | IBAN requirement |
|------|-------------|------------------|
| QRR  | QR-Reference (27-digit) | QR-IBAN (IID 30000–31999) |
| SCOR | Creditor Reference (ISO 11649) | Regular IBAN |
| NON  | No reference | Regular IBAN |

## Project Structure

```
swiss-qr-payment/
├── python/          # Python package
│   ├── src/swiss_qr_payment/
│   └── tests/
├── rust/            # Rust crate
│   └── src/
├── LICENSE          # MIT
└── README.md
```

## License

MIT
