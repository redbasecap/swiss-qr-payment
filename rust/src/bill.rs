use crate::address::Address;
use crate::error::QRBillError;
use crate::validate::{validate_iban, is_qr_iban, validate_qr_reference, validate_creditor_reference};

/// Reference type for the QR-bill.
#[derive(Debug, Clone, PartialEq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum ReferenceType {
    /// QR-Reference (27-digit, Modulo 10 recursive). Requires QR-IBAN.
    QRR,
    /// Creditor Reference (ISO 11649). Requires regular IBAN.
    SCOR,
    /// No reference.
    NON,
}

impl ReferenceType {
    fn as_str(&self) -> &str {
        match self {
            Self::QRR => "QRR",
            Self::SCOR => "SCOR",
            Self::NON => "NON",
        }
    }

    /// Parse from string.
    pub fn from_str(s: &str) -> Result<Self, QRBillError> {
        match s {
            "QRR" => Ok(Self::QRR),
            "SCOR" => Ok(Self::SCOR),
            "NON" => Ok(Self::NON),
            _ => Err(QRBillError::InvalidReferenceType(s.to_string())),
        }
    }
}

/// A validated Swiss QR-bill payment slip.
///
/// Use [`QRBill::new`] to start building, chain methods, then call `.build()`.
#[derive(Debug, Clone)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct QRBill {
    pub account: String,
    pub creditor: Address,
    pub amount: Option<f64>,
    pub currency: String,
    pub debtor: Option<Address>,
    pub reference_type: ReferenceType,
    pub reference: String,
    pub message: String,
    pub billing_info: String,
    pub alt_procedures: Vec<String>,
    pub language: String,
}

/// Builder for constructing a QRBill step by step.
pub struct QRBillBuilder {
    account: String,
    creditor: Address,
    amount: Option<f64>,
    currency: String,
    debtor: Option<Address>,
    reference_type: ReferenceType,
    reference: String,
    message: String,
    billing_info: String,
    alt_procedures: Vec<String>,
    language: String,
}

impl QRBill {
    /// Start building a new QR-bill with required fields.
    pub fn new(account: impl Into<String>, creditor: Address) -> QRBillBuilder {
        QRBillBuilder {
            account: account.into().replace(' ', ""),
            creditor,
            amount: None,
            currency: "CHF".to_string(),
            debtor: None,
            reference_type: ReferenceType::NON,
            reference: String::new(),
            message: String::new(),
            billing_info: String::new(),
            alt_procedures: Vec::new(),
            language: "de".to_string(),
        }
    }

    /// Build the SPC (Swiss Payments Code) data string for the QR code.
    pub fn to_spc(&self) -> String {
        let mut lines: Vec<String> = Vec::new();

        // Header
        lines.push("SPC".to_string());
        lines.push("0200".to_string());
        lines.push("1".to_string());

        // Creditor
        lines.push(self.account.clone());
        lines.extend(self.creditor.to_spc_fields());

        // Ultimate creditor (empty)
        lines.extend(Address::empty_spc_fields());

        // Amount
        lines.push(match self.amount {
            Some(amt) => format!("{:.2}", amt),
            None => String::new(),
        });
        lines.push(self.currency.clone());

        // Debtor
        match &self.debtor {
            Some(d) => lines.extend(d.to_spc_fields()),
            None => lines.extend(Address::empty_spc_fields()),
        }

        // Reference
        lines.push(self.reference_type.as_str().to_string());
        lines.push(self.reference.clone());

        // Additional info
        lines.push(self.message.clone());
        lines.push("EPD".to_string());
        lines.push(self.billing_info.clone());

        // Alt procedures
        for ap in &self.alt_procedures {
            lines.push(ap.clone());
        }

        lines.join("\n")
    }

    /// Generate QR code as PNG bytes.
    pub fn to_png(&self, size: u32) -> Result<Vec<u8>, QRBillError> {
        use qrcode::QrCode;
        use qrcode::types::QrError;
        use image::Luma;

        let spc = self.to_spc();
        let code = QrCode::with_error_correction_level(spc.as_bytes(), qrcode::EcLevel::M)
            .map_err(|e: QrError| QRBillError::QrCodeError(e.to_string()))?;

        let img = code.render::<Luma<u8>>()
            .quiet_zone(false)
            .min_dimensions(size, size)
            .build();

        let mut buf: Vec<u8> = Vec::new();
        let mut cursor = std::io::Cursor::new(&mut buf);
        img.write_to(&mut cursor, image::ImageFormat::Png)
            .map_err(|e| QRBillError::ImageError(e.to_string()))?;

        Ok(buf)
    }

    /// Save QR code as PNG file.
    pub fn save_png(&self, path: &str, size: u32) -> Result<(), QRBillError> {
        let bytes = self.to_png(size)?;
        std::fs::write(path, bytes).map_err(|e| QRBillError::ImageError(e.to_string()))
    }
}

impl QRBillBuilder {
    /// Set the payment amount (0.01–999'999'999.99).
    pub fn amount(mut self, amount: f64) -> Self {
        self.amount = Some(amount);
        self
    }

    /// Set the currency ("CHF" or "EUR").
    pub fn currency(mut self, currency: impl Into<String>) -> Self {
        self.currency = currency.into();
        self
    }

    /// Set the debtor (payable by).
    pub fn debtor(mut self, debtor: Address) -> Self {
        self.debtor = Some(debtor);
        self
    }

    /// Set the reference type and reference number.
    pub fn reference(mut self, ref_type: ReferenceType, reference: impl Into<String>) -> Self {
        self.reference_type = ref_type;
        self.reference = reference.into();
        self
    }

    /// Set the unstructured message (max 140 chars combined with billing_info).
    pub fn message(mut self, message: impl Into<String>) -> Self {
        self.message = message.into();
        self
    }

    /// Set structured billing information.
    pub fn billing_info(mut self, info: impl Into<String>) -> Self {
        self.billing_info = info.into();
        self
    }

    /// Add an alternative procedure parameter (max 2).
    pub fn alt_procedure(mut self, param: impl Into<String>) -> Self {
        self.alt_procedures.push(param.into());
        self
    }

    /// Set the display language (de/fr/it/en).
    pub fn language(mut self, lang: impl Into<String>) -> Self {
        self.language = lang.into();
        self
    }

    /// Validate and build the QRBill.
    pub fn build(self) -> Result<QRBill, QRBillError> {
        // Validate IBAN
        validate_iban(&self.account)?;

        // Validate addresses
        self.creditor.validate()?;
        if let Some(ref d) = self.debtor {
            d.validate()?;
        }

        // Currency
        if self.currency != "CHF" && self.currency != "EUR" {
            return Err(QRBillError::InvalidCurrency(self.currency));
        }

        // Amount
        if let Some(amt) = self.amount {
            if !(0.01..=999_999_999.99).contains(&amt) {
                return Err(QRBillError::InvalidAmount(amt));
            }
        }

        // Reference type vs IBAN
        let is_qr = is_qr_iban(&self.account);
        match self.reference_type {
            ReferenceType::QRR if !is_qr => return Err(QRBillError::QrrNeedsQrIban),
            _ if is_qr && self.reference_type != ReferenceType::QRR => {
                return Err(QRBillError::QrIbanNeedsQrr)
            }
            _ => {}
        }

        // Validate reference
        match self.reference_type {
            ReferenceType::QRR if !self.reference.is_empty() => {
                validate_qr_reference(&self.reference)?;
            }
            ReferenceType::SCOR if !self.reference.is_empty() => {
                validate_creditor_reference(&self.reference)?;
            }
            ReferenceType::NON if !self.reference.is_empty() => {
                return Err(QRBillError::NonRefNotEmpty);
            }
            _ => {}
        }

        // Info length
        let info_len = self.message.len() + self.billing_info.len();
        if info_len > 140 {
            return Err(QRBillError::InfoTooLong(info_len));
        }

        // Alt procedures
        if self.alt_procedures.len() > 2 {
            return Err(QRBillError::TooManyAltProcedures);
        }

        Ok(QRBill {
            account: self.account,
            creditor: self.creditor,
            amount: self.amount,
            currency: self.currency,
            debtor: self.debtor,
            reference_type: self.reference_type,
            reference: self.reference,
            message: self.message,
            billing_info: self.billing_info,
            alt_procedures: self.alt_procedures,
            language: self.language,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn basic_bill() -> Result<QRBill, QRBillError> {
        QRBill::new(
            "CH9300762011623852957",
            Address::new("Max Muster & Söhne", "Musterstrasse", "123", "8000", "Seldwyla", "CH"),
        )
        .amount(1949.75)
        .debtor(Address::new("Simon Muster", "Musterstrasse", "1", "8000", "Seldwyla", "CH"))
        .message("Bezahlung der Reise")
        .build()
    }

    #[test]
    fn test_spc_header() {
        let bill = basic_bill().unwrap();
        let spc = bill.to_spc();
        let lines: Vec<&str> = spc.lines().collect();
        assert_eq!(lines[0], "SPC");
        assert_eq!(lines[1], "0200");
        assert_eq!(lines[2], "1");
    }

    #[test]
    fn test_spc_creditor() {
        let bill = basic_bill().unwrap();
        let spc = bill.to_spc();
        let lines: Vec<&str> = spc.lines().collect();
        assert_eq!(lines[3], "CH9300762011623852957");
        assert_eq!(lines[4], "S");
        assert_eq!(lines[5], "Max Muster & Söhne");
        assert_eq!(lines[6], "Musterstrasse");
        assert_eq!(lines[7], "123");
    }

    #[test]
    fn test_spc_amount() {
        let bill = basic_bill().unwrap();
        let spc = bill.to_spc();
        let lines: Vec<&str> = spc.lines().collect();
        assert_eq!(lines[18], "1949.75");
        assert_eq!(lines[19], "CHF");
    }

    #[test]
    fn test_spc_no_amount() {
        let bill = QRBill::new(
            "CH9300762011623852957",
            Address::new("Test", "Street", "", "1234", "City", "CH"),
        ).build().unwrap();
        let spc = bill.to_spc();
        let lines: Vec<&str> = spc.lines().collect();
        assert_eq!(lines[18], "");
    }

    #[test]
    fn test_spc_trailer() {
        let bill = basic_bill().unwrap();
        let spc = bill.to_spc();
        let lines: Vec<&str> = spc.lines().collect();
        assert_eq!(lines[30], "EPD");
    }

    #[test]
    fn test_invalid_currency() {
        let result = QRBill::new(
            "CH9300762011623852957",
            Address::new("Test", "", "", "", "", "CH"),
        ).currency("USD").build();
        assert!(matches!(result, Err(QRBillError::InvalidCurrency(_))));
    }

    #[test]
    fn test_qr_iban_needs_qrr() {
        let result = QRBill::new(
            "CH4431999123000889012",
            Address::new("Test", "", "", "", "", "CH"),
        ).build();
        assert!(matches!(result, Err(QRBillError::QrIbanNeedsQrr)));
    }

    #[test]
    fn test_png_generation() {
        let bill = basic_bill().unwrap();
        let png = bill.to_png(200);
        assert!(png.is_ok());
        assert!(!png.unwrap().is_empty());
    }
}
