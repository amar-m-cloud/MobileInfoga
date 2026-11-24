"""
Tests for OsintNumber class.
"""

import pytest
from phonenumbers import parse, is_possible_number
from mobileinfoga import OsintNumber


@pytest.fixture
def valid_number():
    return "+1234567890"


class TestOsintNumber:
    """Test OsintNumber class."""

    def test_validate_phone_number(self, valid_number):
        """Test phone number validation."""
        program = OsintNumber()
        assert program.validate_phone_number(valid_number) == True

    def test_invalid_phone_number(self):
        """Test invalid phone number."""
        program = OsintNumber()
        assert program.validate_phone_number("1234567890") == False

    def test_grab_data(self, valid_number):
        """Test data extraction."""
        program = OsintNumber()
        program.formatted_number = valid_number
        program.grab_data()
        assert program.valid == True
        assert program.country_prefix == "+1"
        assert program.country_code == "US"
        assert program.local_format == "1234567890"
        assert program.international_format == "+1 1234567890"


@pytest.fixture
def mock_telegram_data():
    return {
        "TrueCaller": {"Name": "John Doe", "Location": "California"},
        "Unknown": {"Name": "Leaked1"},
        "Unknown2": {"Name": "Leaked2"},
        "WhatsApp": "https://wa.me/1234567890",
        "Telegram": "https://t.me/1234567890"
    }


class TestFormatting:
    """Test Formatting_data function."""

    def test_formatting(self, valid_number, mock_telegram_data):
        """Test data formatting."""
        program = OsintNumber()
        program.formatted_number = valid_number
        program.grab_data()
        osint_data = {
            "fetching_number": valid_number,
            "valid": True,
            "country_prefix": "+1",
            "country_code": "US",
            "local_format": "1234567890",
            "international_format": "+1 1234567890",
            "line_type": "Mobile",
            "time_zone": ["America/Los_Angeles"],
            "carrier": "AT&T",
            "country_name": "United States",
            "location": "California"
        }

        # Mock the function call
        import io
        import sys

        original_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            from mobileinfoga import Formating_data
            Formating_data(osint_data, mock_telegram_data)
            output = sys.stdout.getvalue()
            assert "Fetching Phone Number" in output
            assert "Valid: True" in output
            assert "Truecaller Name: John Doe" in output
            assert "Leaked Name 1: Leaked1" in output
            assert "MCC: 242" in output  # Example MCC for AT&T
            assert "PLMN Identifier: 242f12" in output  # Example PLMN
        finally:
            sys.stdout = original_stdout