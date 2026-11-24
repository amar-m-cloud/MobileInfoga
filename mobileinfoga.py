"""
MobileInfoga - Enhanced with error handling, retry logic, and validation.

Key improvements:
- Config validation
- Retry logic for Telegram operations
- Better error messages
- Type hints
- Logging
"""

import os
import sys
import json
import re
import logging
from typing import Optional, Dict, Any, List

# Import dependencies
from telethon import events, sync, exceptions as telethon_exceptions
from telethon.tl.types import InputPeerUser
from config import API_HASH, API_ID, PHONE, validate_credentials
from phonenumbers import carrier, geocoder, timezone
import phonenumbers
from mobile_codes import alpha2, operators

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataConverter:
    """Converts raw Telegram response data into structured JSON."""
    def __init__(self, text_data: str):
        self.lines = text_data.split('\n')
        self.data: Dict[str, Any] = {
            "Number": "",
            "Country": "",
            "TrueCaller": {},
            "Unknown": {},
            "Unknown2": {},
            "WhatsApp": "",
            "Telegram": ""
        }

    def clean_line(self, line: str) -> str:
        """Remove special characters and whitespace."""
        line = re.sub(r'[*`️]', '', line)
        return line.strip()

    def extract_links(self, line: str) -> List[str]:
        """Extract WhatsApp/Telegram links from formatted text."""
        links = re.findall(r'\[(.*?)\](.*?)', line)
        link_strings = [f"{text}: {url}" for text, url in links]
        return link_strings

    def parse_lines(self) -> None:
        """Parse raw text into structured data."""
        current_section: Optional[str] = None
        for line in self.lines:
            line = self.clean_line(line)
            links = self.extract_links(line)

            if line.startswith("Number:"):
                self.data["Number"] = line.split(": ", 1)[1]
            elif line.startswith("Country:"):
                self.data["Country"] = line.split(": ", 1)[1]
            elif line.startswith("🔍 TrueCaller Says:"):
                current_section = "TrueCaller"
            elif line.startswith("🔍 Unknown Says:"):
                current_section = "Unknown"
            elif line.startswith("🔍 Unknown2 Says:"):
                current_section = "Unknown2"
            elif current_section and ": " in line:
                key, value = line.split(": ", 1)
                self.data[current_section][key] = value

            for link in links:
                if link.startswith("WhatsApp:"):
                    self.data["WhatsApp"] = link.split(": ", 1)[1]
                elif link.startswith("Telegram:"):
                    self.data["Telegram"] = link.split(": ", 1)[1]

    def convert_to_json(self) -> str:
        """Convert structured data to JSON."""
        return json.dumps(self.data, indent=4)

    def process(self) -> str:
        """Parse and return JSON output."""
        self.parse_lines()
        return self.convert_to_json()


class TelethonBot:
    """Handles Telegram bot operations with retry logic."""
    def __init__(self):
        self.client = None
        self.username: str = '@TrueCaller1Bot'
        self.user_entity = None
        self.message_text: str = ""
        self.max_retries: int = 3

    async def _authenticate_with_retry(self) -> None:
        """Authenticate with Telegram with retry logic."""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} of {self.max_retries} for authentication")
                os.makedirs('session', exist_ok=True)
                self.client = sync.TelegramClient(
                    'session/session', API_ID, API_HASH
                )
                self.client.connect()
                if not self.client.is_user_authorized():
                    self.client.send_code_request(PHONE)
                    # In production, use asyncio.run for OTP input
                    self.client.sign_in(PHONE, "123456")  # Mock OTP
                return
            except telethon_exceptions.FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"Flood wait: {wait_time} seconds. Retrying...")
                await asyncio.sleep(wait_time)
            except telethon_exceptions.TelegramError as e:
                logger.error(f"Telegram error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def _get_user_entity(self) -> None:
        """Fetch user entity with retry logic."""
        for attempt in range(self.max_retries):
            try:
                self.user_entity = await self.client.get_entity(self.username)
                return
            except telethon_exceptions.TelegramError as e:
                logger.error(f"Entity fetch error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def _send_message(self, message: str) -> None:
        """Send message with retry logic."""
        for attempt in range(self.max_retries):
            try:
                user_id = self.user_entity.id
                user_hash = self.user_entity.access_hash
                receiver = InputPeerUser(user_id, user_hash)
                await self.client.send_message(receiver, message, parse_mode='html')
                return
            except telethon_exceptions.TelegramError as e:
                logger.error(f"Send message error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def run_telegram_bot(self, number: str) -> str:
        """Run the Telegram bot with retry logic."""
        try:
            await self._authenticate_with_retry()
            await self._get_user_entity()
            await self._send_message(number)
            return "Telegram bot executed successfully"
        except Exception as e:
            logger.error(f"Telegram bot failed: {e}")
            raise

    def run(self, number: str) -> str:
        """Run the bot in synchronous mode with error handling."""
        try:
            import asyncio
            async def run_async():
                await self.run_telegram_bot(number)
            asyncio.run(run_async())
            return "Telegram bot executed"
        except Exception as e:
            logger.error(f"Error in run(): {e}")
            return f"Error: {str(e)}"


class OsintNumber:
    """Handles phone number OSINT operations."""
    def __init__(self):
        self.formatted_number: Optional[str] = None
        self.phone_number: Optional[phonenumbers.PhoneNumber] = None
        self.phone_number_national: Optional[str] = None
        self.phone_number_international: Optional[str] = None
        self.carrier: Optional[str] = None
        self.country_prefix: Optional[str] = None
        self.local_format: Optional[str] = None
        self.time_zone: Optional[List[str]] = None
        self.country_name: Optional[str] = None
        self.country_code: Optional[str] = None
        self.location: Optional[str] = None
        self.valid: bool = False

    @staticmethod
    def validate_phone_number(input_number: str) -> bool:
        """Validate phone number format."""
        try:
            parsed_number = phonenumbers.parse(input_number, None)
            return phonenumbers.is_possible_number(parsed_number)
        except phonenumbers.phonenumberutil.NumberParseException:
            return False

    def get_line_type(self) -> str:
        """Determine line type."""
        if not self.phone_number:
            return "Unknown"
        number_type = phonenumbers.number_type(self.phone_number)

        if number_type == phonenumbers.PhoneNumberType.FIXED_LINE:
            return "Fixed Line"
        elif number_type == phonenumbers.PhoneNumberType.MOBILE:
            return "Mobile"
        elif number_type == phonenumbers.PhoneNumberType.TOLL_FREE:
            return "Toll Free"
        elif number_type == phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE:
            return "Fixed Line or Mobile"
        elif number_type == phonenumbers.PhoneNumberType.PREMIUM_RATE:
            return "Premium Rate"
        elif number_type == phonenumbers.PhoneNumberType.SHARED_COST:
            return "Shared Cost"
        elif number_type == phonenumbers.PhoneNumberType.VOIP:
            return "VoIP"
        elif number_type == phonenumbers.PhoneNumberType.PERSONAL_NUMBER:
            return "Personal Number"
        elif number_type == phonenumbers.PhoneNumberType.PAGER:
            return "Pager"
        elif number_type == phonenumbers.PhoneNumberType.UAN:
            return "Universal Access Number"
        else:
            return "Unknown"

    def grab_data(self) -> None:
        """Extract phone number data."""
        if not self.formatted_number:
            return

        try:
            self.phone_number = phonenumbers.parse(self.formatted_number)
            self.phone_number_national = phonenumbers.format_number(
                self.phone_number, phonenumbers.PhoneNumberFormat.NATIONAL
            )
            self.phone_number_international = phonenumbers.format_number(
                self.phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            self.carrier = carrier.name_for_number(self.phone_number, 'en')
            self.time_zone = timezone.time_zones_for_number(self.phone_number)
            self.location = geocoder.description_for_number(self.phone_number, "en")
            self.country_name = geocoder.country_name_for_number(self.phone_number, "en")
            self.country_prefix = self.phone_number.country_code
            self.country_code = phonenumbers.region_code_for_country_code(self.country_prefix)
            self.valid = phonenumbers.is_valid_number(self.phone_number)
            self.local_format = self.phone_number.national_number
        except phonenumbers.phonenumberutil.NumberParseException as e:
            logger.error(f"Error parsing phone number: {e}")
            self.valid = False

    def output(self) -> Dict[str, Any]:
        """Return formatted data as a dictionary."""
        data = {
            "fetching_number": self.formatted_number,
            "valid": self.valid,
            "country_prefix": f"+{self.country_prefix}" if self.country_prefix else "",
            "country_code": self.country_code,
            "local_format": self.local_format,
            "international_format": self.phone_number_international,
            "national_format": self.phone_number_national,
            "line_type": self.get_line_type(),
            "time_zone": self.time_zone,
            "carrier": self.carrier,
            "country_name": self.country_name,
            "location": self.location
        }
        return data


def EncodePLMN(mcc: str, mnc: str) -> str:
    """Encode MCC/MNC into PLMN format."""
    if mcc is None or mnc is None:
        raise ValueError("MCC and MNC must not be None")

    def Reverse(s: str) -> str:
        return s[::-1]

    mcc_reversed = Reverse(mcc)
    mnc_reversed = Reverse(mnc)

    plmn = list('XXXXXX')
    if len(mnc) == 2:
        plmn[0] = mcc_reversed[1]
        plmn[1] = mcc_reversed[2]
        plmn[2] = "f"
        plmn[3] = mcc_reversed[0]
        plmn[4] = mnc_reversed[0]
        plmn[5] = mnc_reversed[1]
    else:
        plmn[0] = mcc_reversed[1]
        plmn[1] = mcc_reversed[2]
        plmn[2] = mnc_reversed[0]
        plmn[3] = mcc_reversed[0]
        plmn[4] = mnc_reversed[1]
        plmn[5] = mnc_reversed[2]

    encoded_plmn = ''.join(plmn)
    return encoded_plmn


def mncmcc(country_code: str, location: str, carrier: str) -> tuple:
    """Determine MCC/MNC from country code, location, and carrier."""
    country_code = country_code.strip().upper()
    location = location.strip().lower()
    carrier = carrier.strip().lower()

    info = alpha2(country_code)
    if not info:
        raise ValueError(f"No information found for country code: {country_code}")

    mcc_list = info.mcc
    mcc_number = None
    mnc_number = None

    for mcc in mcc_list:
        operators = operators(mcc)
        for operator in operators:
            if location in operator.operator.lower() and carrier in operator.brand.lower():
                mcc_number = operator.mcc
                mnc_number = operator.mnc
                return mcc_number, mnc_number
    return None, None


def Formating_data(osintData: Dict[str, Any], telegramData: Dict[str, Any]) -> None:
    """Format and print the final output."""
    try:
        if isinstance(telegramData, str):
            telegramData = json.loads(telegramData)
        if isinstance(osintData, str):
            osintData = json.loads(osintData)

        if not isinstance(telegramData, dict):
            raise ValueError("telegramData must be a dictionary after parsing JSON.")
        if not isinstance(osintData, dict):
            raise ValueError("osintData must be a dictionary after parsing JSON.")

        fetching_number = osintData['fetching_number']
        valid = osintData['valid']
        truecallerName = telegramData.get('TrueCaller', {}).get('Name')
        leaked_data1 = telegramData.get('Unknown', {}).get('Name')
        leaked_data2 = telegramData.get('Unknown2', {}).get('Name')
        country_prefix = osintData['country_prefix']
        country_code = osintData['country_code']
        local_format = osintData['local_format']
        international_format = osintData['international_format']
        national_format = osintData['national_format']
        line_type = osintData['line_type']
        time_zone = osintData['time_zone']
        carrier = osintData['carrier']
        location = telegramData.get('TrueCaller', {}).get('Location')
        whatsapp = telegramData.get('WhatsApp')
        telegram = telegramData.get('Telegram')

        mcc, mnc = mncmcc(country_code, location, carrier)
        plmn = EncodePLMN(mcc, mnc)

        print("Fetching Phone Number :", fetching_number)
        print("Valid:", valid)
        print("Truecaller Name:", truecallerName)
        print("Leaked Name 1:", leaked_data1)
        print("Leaked Name 2:", leaked_data2)
        print("Country Prefix:", country_prefix)
        print("Country Code:", country_code)
        print("Local Format:", local_format)
        print("International Format:", international_format)
        print("National Format:", national_format)
        print("Line Type:", line_type)
        print("Time Zone:", time_zone)
        print("Carrier:", carrier)
        print("Location:", location)
        print("WhatsApp Link:", whatsapp)
        print("Telegram Link:", telegram)
        print("MCC:", mcc)
        print("MNC:", mnc)
        print("PLMN Identifier:", plmn)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
    except KeyError as e:
        logger.error(f"Key error: {e}")
    except ValueError as e:
        logger.error(f"Value error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def run_telegram_bot(number: str) -> str:
    """Run the Telegram bot."""
    bot = TelethonBot()
    bot.message = number
    return bot.run(number)


def main() -> None:
    """Main entry point."""
    # Validate credentials
    cred_error = validate_credentials()
    if cred_error:
        logger.error(cred_error)
        sys.exit(1)

    program = OsintNumber()
    number = input("Enter the number with country code (e.g., +1234567890): ").strip()

    if not program.validate_phone_number(number):
        print("Invalid phone number format.")
        sys.exit(1)

    program.formatted_number = number
    program.grab_data()

    if not program.valid:
        print("Invalid phone number.")
        sys.exit(1)

    try:
        telegram_data = run_telegram_bot(number)
        osint_data = program.output()
        Formating_data(osint_data, telegram_data)
    except Exception as e:
        logger.error(f"Error in main(): {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()