//! # Swiss QR Payment
//!
//! Generate Swiss QR-bill payment codes compliant with
//! [SIX Implementation Guidelines QR-Rechnung v2.3](https://www.six-group.com/dam/download/banking-services/standardization/qr-bill/ig-qr-bill-v2.3-de.pdf).
//!
//! ## Features
//!
//! - Build SPC (Swiss Payments Code) data strings
//! - Generate QR code images (PNG)
//! - Validate IBAN, QR-Reference (Modulo 10), Creditor Reference (ISO 11649)
//! - Structured addresses (type S) only (type K deprecated since Nov 2025)
//! - Full field validation per SIX spec
//!
//! ## Quick Start
//!
//! ```rust
//! use swiss_qr_payment::{QRBill, Address};
//!
//! let bill = QRBill::new(
//!     "CH9300762011623852957",
//!     Address::new("Max Muster", "Musterstrasse", "123", "8000", "Seldwyla", "CH"),
//! )
//! .amount(1949.75)
//! .debtor(Address::new("Simon Muster", "Musterstrasse", "1", "8000", "Seldwyla", "CH"))
//! .message("Bezahlung der Reise")
//! .build()
//! .unwrap();
//!
//! // Get SPC payload
//! let spc = bill.to_spc();
//!
//! // Generate QR code PNG bytes
//! let png_bytes = bill.to_png(1000).unwrap();
//! ```

mod address;
mod bill;
mod validate;
mod error;

pub use address::Address;
pub use bill::{QRBill, QRBillBuilder, ReferenceType};
pub use validate::{
    validate_iban, is_qr_iban, format_iban,
    validate_qr_reference, calculate_qr_reference_check_digit, format_qr_reference,
    validate_creditor_reference, format_creditor_reference,
    format_amount,
};
pub use error::QRBillError;
