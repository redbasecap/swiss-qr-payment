/// Errors that can occur when building or validating a QR-bill.
#[derive(Debug, thiserror::Error)]
pub enum QRBillError {
    #[error("IBAN must be 21 characters, got {0}")]
    IbanLength(usize),

    #[error("Only CH/LI IBANs are allowed, got {0}")]
    IbanCountry(String),

    #[error("IBAN check digit is invalid")]
    IbanCheckDigit,

    #[error("Currency must be CHF or EUR, got {0}")]
    InvalidCurrency(String),

    #[error("Amount must be 0.01–999'999'999.99, got {0}")]
    InvalidAmount(f64),

    #[error("QR-IBAN requires reference_type QRR")]
    QrIbanNeedsQrr,

    #[error("QRR reference requires a QR-IBAN (IID 30000–31999)")]
    QrrNeedsQrIban,

    #[error("NON reference type must have empty reference")]
    NonRefNotEmpty,

    #[error("QR-Reference must be 27 digits, got {0}")]
    QrRefLength(usize),

    #[error("QR-Reference must be numeric")]
    QrRefNotNumeric,

    #[error("QR-Reference check digit invalid: expected {expected}, got {actual}")]
    QrRefCheckDigit { expected: u8, actual: u8 },

    #[error("Creditor Reference must start with 'RF'")]
    ScorPrefix,

    #[error("Creditor Reference must be 5–25 chars, got {0}")]
    ScorLength(usize),

    #[error("Creditor Reference check digits are invalid")]
    ScorCheckDigit,

    #[error("Message + billing_info must be ≤ 140 chars, got {0}")]
    InfoTooLong(usize),

    #[error("Maximum 2 alternative procedures allowed")]
    TooManyAltProcedures,

    #[error("Field '{field}' exceeds max length {max}: got {actual}")]
    FieldTooLong { field: String, max: usize, actual: usize },

    #[error("Name is required")]
    NameRequired,

    #[error("Country must be 2-letter ISO code, got {0}")]
    InvalidCountry(String),

    #[error("Invalid character in IBAN: {0}")]
    IbanInvalidChar(char),

    #[error("QR code generation failed: {0}")]
    QrCodeError(String),

    #[error("Image encoding failed: {0}")]
    ImageError(String),

    #[error("reference_type must be QRR, SCOR, or NON, got {0}")]
    InvalidReferenceType(String),
}
