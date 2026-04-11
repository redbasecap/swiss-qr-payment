use crate::error::QRBillError;

/// Structured address (type S) per SIX Implementation Guidelines v2.3.
///
/// Only structured addresses are supported (combined type "K" was deprecated
/// in November 2025).
#[derive(Debug, Clone, PartialEq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Address {
    /// Name or company (max 70 chars).
    pub name: String,
    /// Street name (max 70 chars).
    pub street: String,
    /// House/building number (max 16 chars).
    pub house_number: String,
    /// Postal/zip code (max 16 chars).
    pub postal_code: String,
    /// City/town (max 35 chars).
    pub city: String,
    /// 2-letter ISO 3166-1 country code.
    pub country: String,
}

impl Address {
    /// Create a new validated address.
    pub fn new(
        name: impl Into<String>,
        street: impl Into<String>,
        house_number: impl Into<String>,
        postal_code: impl Into<String>,
        city: impl Into<String>,
        country: impl Into<String>,
    ) -> Self {
        Self {
            name: name.into(),
            street: street.into(),
            house_number: house_number.into(),
            postal_code: postal_code.into(),
            city: city.into(),
            country: country.into(),
        }
    }

    /// Validate all fields against SIX spec limits.
    pub fn validate(&self) -> Result<(), QRBillError> {
        if self.name.is_empty() {
            return Err(QRBillError::NameRequired);
        }
        check_len(&self.name, 70, "name")?;
        check_len(&self.street, 70, "street")?;
        check_len(&self.house_number, 16, "house_number")?;
        check_len(&self.postal_code, 16, "postal_code")?;
        check_len(&self.city, 35, "city")?;
        if self.country.len() != 2 {
            return Err(QRBillError::InvalidCountry(self.country.clone()));
        }
        Ok(())
    }

    /// Human-readable display lines for the payment slip.
    pub fn display_lines(&self) -> Vec<String> {
        let mut lines = vec![self.name.clone()];
        let street_line = format!("{} {}", self.street, self.house_number)
            .trim()
            .to_string();
        if !street_line.is_empty() {
            lines.push(street_line);
        }
        let zip_city = format!("{} {}", self.postal_code, self.city)
            .trim()
            .to_string();
        if !zip_city.is_empty() {
            let prefix = if self.country != "CH" && self.country != "LI" {
                format!("{}-", self.country)
            } else {
                String::new()
            };
            lines.push(format!("{}{}", prefix, zip_city));
        }
        lines
    }

    /// Return the 7 SPC data fields for this address.
    pub fn to_spc_fields(&self) -> Vec<String> {
        vec![
            "S".to_string(),
            self.name.clone(),
            self.street.clone(),
            self.house_number.clone(),
            self.postal_code.clone(),
            self.city.clone(),
            self.country.clone(),
        ]
    }

    /// Return 7 empty fields (for when no address is provided).
    pub fn empty_spc_fields() -> Vec<String> {
        vec![String::new(); 7]
    }
}

fn check_len(value: &str, max: usize, field: &str) -> Result<(), QRBillError> {
    if value.len() > max {
        return Err(QRBillError::FieldTooLong {
            field: field.to_string(),
            max,
            actual: value.len(),
        });
    }
    Ok(())
}
