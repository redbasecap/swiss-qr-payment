use crate::error::QRBillError;

// ─── IBAN ────────────────────────────────────────────────────────────────────

/// Validate a Swiss/Liechtenstein IBAN (ISO 13616).
pub fn validate_iban(iban: &str) -> Result<(), QRBillError> {
    let clean: String = iban.chars().filter(|c| !c.is_whitespace()).collect();

    if clean.len() != 21 {
        return Err(QRBillError::IbanLength(clean.len()));
    }

    let prefix = &clean[..2];
    if prefix != "CH" && prefix != "LI" {
        return Err(QRBillError::IbanCountry(prefix.to_string()));
    }

    // ISO 13616 modulo 97 check
    let rearranged = format!("{}{}", &clean[4..], &clean[..4]);
    let mut numeric = String::new();
    for ch in rearranged.chars() {
        if ch.is_ascii_digit() {
            numeric.push(ch);
        } else if ch.is_ascii_alphabetic() {
            let val = ch.to_ascii_uppercase() as u32 - 55;
            numeric.push_str(&val.to_string());
        } else {
            return Err(QRBillError::IbanInvalidChar(ch));
        }
    }

    // Large number modulo — process in chunks
    let remainder = mod97(&numeric);
    if remainder != 1 {
        return Err(QRBillError::IbanCheckDigit);
    }

    Ok(())
}

fn mod97(digits: &str) -> u64 {
    let mut remainder: u64 = 0;
    for ch in digits.chars() {
        remainder = (remainder * 10 + ch.to_digit(10).unwrap() as u64) % 97;
    }
    remainder
}

/// Check if an IBAN is a QR-IBAN (IID range 30000–31999).
pub fn is_qr_iban(iban: &str) -> bool {
    let clean: String = iban.chars().filter(|c| !c.is_whitespace()).collect();
    if clean.len() < 9 {
        return false;
    }
    clean[4..9].parse::<u32>().map_or(false, |iid| (30000..=31999).contains(&iid))
}

/// Format IBAN with spaces in groups of 4.
pub fn format_iban(iban: &str) -> String {
    let clean: String = iban.chars().filter(|c| !c.is_whitespace()).collect();
    clean
        .as_bytes()
        .chunks(4)
        .map(|chunk| std::str::from_utf8(chunk).unwrap())
        .collect::<Vec<_>>()
        .join(" ")
}

// ─── QR-Reference (Modulo 10 recursive) ─────────────────────────────────────

const MOD10_TABLE: [[u8; 10]; 10] = [
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
];

fn mod10_recursive(digits: &str) -> u8 {
    let mut carry: usize = 0;
    for ch in digits.chars() {
        let digit = ch.to_digit(10).unwrap() as usize;
        carry = MOD10_TABLE[carry][digit] as usize;
    }
    ((10 - carry) % 10) as u8
}

/// Validate a QR-Reference (27 digits, Modulo 10 recursive check digit).
pub fn validate_qr_reference(reference: &str) -> Result<(), QRBillError> {
    let clean: String = reference.chars().filter(|c| !c.is_whitespace()).collect();

    if clean.len() != 27 {
        return Err(QRBillError::QrRefLength(clean.len()));
    }

    if !clean.chars().all(|c| c.is_ascii_digit()) {
        return Err(QRBillError::QrRefNotNumeric);
    }

    let expected = mod10_recursive(&clean[..26]);
    let actual = clean[26..].parse::<u8>().unwrap();

    if expected != actual {
        return Err(QRBillError::QrRefCheckDigit { expected, actual });
    }

    Ok(())
}

/// Calculate the check digit for a 26-digit QR-Reference, returning the full 27 digits.
pub fn calculate_qr_reference_check_digit(reference_26: &str) -> Result<String, QRBillError> {
    let clean: String = reference_26.chars().filter(|c| !c.is_whitespace()).collect();
    if clean.len() != 26 || !clean.chars().all(|c| c.is_ascii_digit()) {
        return Err(QRBillError::QrRefLength(clean.len()));
    }
    let check = mod10_recursive(&clean);
    Ok(format!("{}{}", clean, check))
}

/// Format QR-Reference with spaces (2 + groups of 5 from right).
pub fn format_qr_reference(reference: &str) -> String {
    let clean: String = reference.chars().filter(|c| !c.is_whitespace()).collect();
    let bytes = clean.as_bytes();
    let mut groups: Vec<String> = Vec::new();
    let mut i = bytes.len();
    while i > 0 {
        let start = if i >= 5 { i - 5 } else { 0 };
        groups.push(std::str::from_utf8(&bytes[start..i]).unwrap().to_string());
        i = start;
    }
    groups.reverse();
    groups.join(" ")
}

// ─── Creditor Reference (ISO 11649) ─────────────────────────────────────────

/// Validate a Creditor Reference (ISO 11649, Modulo 97-10).
pub fn validate_creditor_reference(reference: &str) -> Result<(), QRBillError> {
    let clean: String = reference.chars().filter(|c| !c.is_whitespace()).collect();
    let upper = clean.to_uppercase();

    if !upper.starts_with("RF") {
        return Err(QRBillError::ScorPrefix);
    }

    if upper.len() < 5 || upper.len() > 25 {
        return Err(QRBillError::ScorLength(upper.len()));
    }

    let rearranged = format!("{}{}", &upper[4..], &upper[..4]);
    let mut numeric = String::new();
    for ch in rearranged.chars() {
        if ch.is_ascii_digit() {
            numeric.push(ch);
        } else if ch.is_ascii_alphabetic() {
            let val = ch.to_ascii_uppercase() as u32 - 55;
            numeric.push_str(&val.to_string());
        } else {
            return Err(QRBillError::IbanInvalidChar(ch));
        }
    }

    if mod97(&numeric) != 1 {
        return Err(QRBillError::ScorCheckDigit);
    }

    Ok(())
}

/// Format Creditor Reference with spaces in groups of 4.
pub fn format_creditor_reference(reference: &str) -> String {
    let clean: String = reference.chars().filter(|c| !c.is_whitespace()).collect();
    clean
        .as_bytes()
        .chunks(4)
        .map(|chunk| std::str::from_utf8(chunk).unwrap())
        .collect::<Vec<_>>()
        .join(" ")
}

// ─── Amount ─────────────────────────────────────────────────────────────────

/// Format amount with space as thousands separator: 1 234.50
pub fn format_amount(amount: f64) -> String {
    let formatted = format!("{:.2}", amount);
    let parts: Vec<&str> = formatted.split('.').collect();
    let integer = parts[0];
    let decimal = parts[1];

    let chars: Vec<char> = integer.chars().collect();
    let mut result = String::new();
    for (i, ch) in chars.iter().enumerate() {
        if i > 0 && (chars.len() - i) % 3 == 0 {
            result.push(' ');
        }
        result.push(*ch);
    }

    format!("{}.{}", result, decimal)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_iban() {
        assert!(validate_iban("CH93 0076 2011 6238 5295 7").is_ok());
    }

    #[test]
    fn test_invalid_iban_length() {
        assert!(matches!(validate_iban("CH1234"), Err(QRBillError::IbanLength(_))));
    }

    #[test]
    fn test_invalid_iban_country() {
        let result = validate_iban("DE8937040044053201300");  // 21 chars, DE prefix
        assert!(matches!(result, Err(QRBillError::IbanCountry(_))));
    }

    #[test]
    fn test_invalid_iban_check() {
        assert!(matches!(
            validate_iban("CH0000762011623852957"),
            Err(QRBillError::IbanCheckDigit)
        ));
    }

    #[test]
    fn test_qr_iban() {
        assert!(is_qr_iban("CH44 3199 9123 0008 8901 2"));
        assert!(!is_qr_iban("CH93 0076 2011 6238 5295 7"));
    }

    #[test]
    fn test_format_iban() {
        assert_eq!(format_iban("CH9300762011623852957"), "CH93 0076 2011 6238 5295 7");
    }

    #[test]
    fn test_valid_qr_reference() {
        assert!(validate_qr_reference("210000000003139471430009017").is_ok());
    }

    #[test]
    fn test_invalid_qr_reference_check() {
        assert!(matches!(
            validate_qr_reference("210000000003139471430009010"),
            Err(QRBillError::QrRefCheckDigit { .. })
        ));
    }

    #[test]
    fn test_calculate_qr_check_digit() {
        let result = calculate_qr_reference_check_digit("21000000000313947143000901").unwrap();
        assert_eq!(result, "210000000003139471430009017");
    }

    #[test]
    fn test_format_qr_reference() {
        assert_eq!(
            format_qr_reference("210000000003139471430009017"),
            "21 00000 00003 13947 14300 09017"
        );
    }

    #[test]
    fn test_valid_creditor_reference() {
        assert!(validate_creditor_reference("RF18539007547034").is_ok());
    }

    #[test]
    fn test_invalid_creditor_reference() {
        assert!(matches!(
            validate_creditor_reference("RF00539007547034"),
            Err(QRBillError::ScorCheckDigit)
        ));
    }

    #[test]
    fn test_format_amount() {
        assert_eq!(format_amount(50.0), "50.00");
        assert_eq!(format_amount(1949.75), "1 949.75");
        assert_eq!(format_amount(1234567.89), "1 234 567.89");
    }
}
