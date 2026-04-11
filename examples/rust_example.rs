// Example: Generate Swiss QR-bill payment codes in Rust.
//
// Run from the rust/ directory:
//     cargo run --example rust_example
//
// (Requires symlinking or copying this file to rust/examples/)

use swiss_qr_payment::{QRBill, Address};

fn main() {
    // --- 1. QR-Reference bill (QRR) with QR-IBAN ---
    let bill_qrr = QRBill::new(
        "CH4431999123000889012",  // QR-IBAN (IID 31999)
        Address::new(
            "Max Muster & Soehne",
            "Musterstrasse", "123",
            "8000", "Seldwyla", "CH",
        ),
    )
    .amount(1949.75)
    .reference_type("QRR")
    .reference("210000000003139471430009017")
    .debtor(Address::new(
        "Simon Muster",
        "Musterstrasse", "1",
        "8000", "Seldwyla", "CH",
    ))
    .message("Invoice 2026-001")
    .build()
    .unwrap();

    println!("=== QRR Bill (QR-Reference) ===");
    println!("{}", bill_qrr.to_spc());
    bill_qrr.save_png("example_qrr.png", 400).unwrap();
    println!("Saved: example_qrr.png\n");

    // --- 2. Creditor Reference bill (SCOR) with regular IBAN ---
    let bill_scor = QRBill::new(
        "CH9300762011623852957",  // Regular IBAN
        Address::new(
            "Max Muster & Soehne",
            "Musterstrasse", "123",
            "8000", "Seldwyla", "CH",
        ),
    )
    .amount(199.95)
    .reference_type("SCOR")
    .reference("RF18539007547034")
    .build()
    .unwrap();

    println!("=== SCOR Bill (Creditor Reference) ===");
    println!("{}", bill_scor.to_spc());
    bill_scor.save_png("example_scor.png", 400).unwrap();
    println!("Saved: example_scor.png\n");

    // --- 3. Minimal bill (no reference, no amount) ---
    let bill_minimal = QRBill::new(
        "CH9300762011623852957",
        Address::new(
            "Max Muster & Soehne",
            "Musterstrasse", "123",
            "8000", "Seldwyla", "CH",
        ),
    )
    .build()
    .unwrap();

    println!("=== Minimal Bill (no reference, no amount) ===");
    println!("{}", bill_minimal.to_spc());
    bill_minimal.save_png("example_minimal.png", 400).unwrap();
    println!("Saved: example_minimal.png");
}
