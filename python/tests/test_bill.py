"""Tests for QRBill core."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from swiss_qr_payment import QRBill, Address


def _basic_bill(**kwargs):
    defaults = dict(
        account="CH93 0076 2011 6238 5295 7",
        creditor=Address("Max Muster & Söhne", "Musterstrasse", "123", "8000", "Seldwyla"),
        amount=1949.75,
        debtor=Address("Simon Muster", "Musterstrasse", "1", "8000", "Seldwyla"),
    )
    defaults.update(kwargs)
    return QRBill(**defaults)


class TestSPCFormat:
    def test_header(self):
        bill = _basic_bill()
        lines = bill.to_spc().split("\n")
        assert lines[0] == "SPC"
        assert lines[1] == "0200"
        assert lines[2] == "1"

    def test_creditor_structured(self):
        bill = _basic_bill()
        lines = bill.to_spc().split("\n")
        assert lines[3] == "CH9300762011623852957"
        assert lines[4] == "S"
        assert lines[5] == "Max Muster & Söhne"
        assert lines[6] == "Musterstrasse"
        assert lines[7] == "123"
        assert lines[8] == "8000"
        assert lines[9] == "Seldwyla"
        assert lines[10] == "CH"

    def test_ultimate_creditor_empty(self):
        bill = _basic_bill()
        lines = bill.to_spc().split("\n")
        for i in range(11, 18):
            assert lines[i] == ""

    def test_amount_and_currency(self):
        bill = _basic_bill(amount=256.30)
        lines = bill.to_spc().split("\n")
        assert lines[18] == "256.30"
        assert lines[19] == "CHF"

    def test_no_amount(self):
        bill = _basic_bill(amount=None)
        lines = bill.to_spc().split("\n")
        assert lines[18] == ""

    def test_debtor(self):
        bill = _basic_bill()
        lines = bill.to_spc().split("\n")
        assert lines[20] == "S"
        assert lines[21] == "Simon Muster"

    def test_no_debtor(self):
        bill = _basic_bill(debtor=None)
        lines = bill.to_spc().split("\n")
        for i in range(20, 27):
            assert lines[i] == ""

    def test_reference_non(self):
        bill = _basic_bill()
        lines = bill.to_spc().split("\n")
        assert lines[27] == "NON"
        assert lines[28] == ""

    def test_trailer(self):
        bill = _basic_bill()
        lines = bill.to_spc().split("\n")
        assert lines[30] == "EPD"

    def test_message(self):
        bill = _basic_bill(message="Bezahlung der Reise")
        lines = bill.to_spc().split("\n")
        assert lines[29] == "Bezahlung der Reise"

    def test_total_line_count_minimal(self):
        bill = _basic_bill()
        lines = bill.to_spc().split("\n")
        assert len(lines) == 32  # 31 fields + 1 billing_info

    def test_alt_procedures(self):
        bill = _basic_bill(alt_procedures=["eBill/B/simon@example.com"])
        lines = bill.to_spc().split("\n")
        assert lines[-1] == "eBill/B/simon@example.com"


class TestValidation:
    def test_invalid_currency(self):
        with pytest.raises(ValueError, match="CHF or EUR"):
            _basic_bill(currency="USD")

    def test_amount_too_low(self):
        with pytest.raises(ValueError, match="0.01"):
            _basic_bill(amount=0.001)

    def test_amount_too_high(self):
        with pytest.raises(ValueError, match="999"):
            _basic_bill(amount=9999999999.99)

    def test_qr_iban_needs_qrr(self):
        with pytest.raises(ValueError, match="QR-IBAN requires"):
            _basic_bill(account="CH44 3199 9123 0008 8901 2")

    def test_non_ref_must_be_empty(self):
        with pytest.raises(ValueError, match="empty reference"):
            _basic_bill(reference="12345")

    def test_message_too_long(self):
        with pytest.raises(ValueError, match="140"):
            _basic_bill(message="x" * 141)

    def test_too_many_alt_procedures(self):
        with pytest.raises(ValueError, match="2 alternative"):
            _basic_bill(alt_procedures=["a", "b", "c"])


class TestConvenience:
    def test_formatted_account(self):
        bill = _basic_bill()
        assert bill.formatted_account == "CH93 0076 2011 6238 5295 7"

    def test_formatted_amount(self):
        bill = _basic_bill(amount=1949.75)
        assert bill.formatted_amount == "1 949.75"

    def test_to_dict_roundtrip(self):
        bill = _basic_bill(message="test")
        d = bill.to_dict()
        bill2 = QRBill.from_dict(d)
        assert bill2.to_spc() == bill.to_spc()

    def test_qr_image(self):
        bill = _basic_bill()
        img = bill.qr_image()
        assert img is not None
