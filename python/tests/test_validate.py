"""Tests for validation utilities."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from swiss_qr_payment.validate import (
    validate_iban, is_qr_iban, format_iban,
    validate_qr_reference, calculate_qr_reference_check_digit, format_qr_reference,
    validate_creditor_reference, format_creditor_reference,
    format_amount,
)


class TestIBAN:
    def test_valid_iban(self):
        assert validate_iban("CH93 0076 2011 6238 5295 7") is True

    def test_valid_iban_no_spaces(self):
        assert validate_iban("CH9300762011623852957") is True

    def test_invalid_length(self):
        with pytest.raises(ValueError, match="21 characters"):
            validate_iban("CH1234")

    def test_invalid_country(self):
        with pytest.raises(ValueError, match="CH/LI"):
            validate_iban("DE8937040044053201300")  # 21 chars but DE prefix

    def test_invalid_check_digit(self):
        with pytest.raises(ValueError, match="check digit"):
            validate_iban("CH0000762011623852957")

    def test_li_iban(self):
        assert validate_iban("LI21 0881 0000 2324 013A A") is True

    def test_qr_iban_detected(self):
        assert is_qr_iban("CH44 3199 9123 0008 8901 2") is True

    def test_regular_iban_not_qr(self):
        assert is_qr_iban("CH93 0076 2011 6238 5295 7") is False

    def test_format_iban(self):
        assert format_iban("CH9300762011623852957") == "CH93 0076 2011 6238 5295 7"


class TestQRReference:
    def test_valid_reference(self):
        # From SIX spec example: 21 00000 00003 13947 14300 09017
        assert validate_qr_reference("210000000003139471430009017") is True

    def test_invalid_length(self):
        with pytest.raises(ValueError, match="27 digits"):
            validate_qr_reference("12345")

    def test_invalid_check_digit(self):
        with pytest.raises(ValueError, match="check digit"):
            validate_qr_reference("210000000003139471430009010")

    def test_calculate_check_digit(self):
        result = calculate_qr_reference_check_digit("21000000000313947143000901")
        assert result == "210000000003139471430009017"

    def test_format(self):
        formatted = format_qr_reference("210000000003139471430009017")
        assert formatted == "21 00000 00003 13947 14300 09017"


class TestCreditorReference:
    def test_valid_scor(self):
        assert validate_creditor_reference("RF18539007547034") is True

    def test_invalid_prefix(self):
        with pytest.raises(ValueError, match="start with 'RF'"):
            validate_creditor_reference("XX18539007547034")

    def test_invalid_check(self):
        with pytest.raises(ValueError, match="check digits"):
            validate_creditor_reference("RF00539007547034")

    def test_format(self):
        assert format_creditor_reference("RF18539007547034") == "RF18 5390 0754 7034"


class TestFormatAmount:
    def test_simple(self):
        assert format_amount(50.00) == "50.00"

    def test_thousands(self):
        assert format_amount(1949.75) == "1 949.75"

    def test_millions(self):
        assert format_amount(1234567.89) == "1 234 567.89"
