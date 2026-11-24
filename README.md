# Phone Number Information Gathering Tool 📞✨

This tool provides comprehensive information about a given mobile phone number, including:
- Truecaller name
- Leaked names
- Country details
- Line type
- Carrier information
- Location
- WhatsApp/Telegram links
- MCC, MNC, and PLMN identifiers

## Features

- **Comprehensive Information**: Obtain detailed information about a phone number.
- **Easy to Use**: Simple CLI interface.
- **Fast and Efficient**: Quickly fetch information.
- **Error Handling**: Robust retry logic for Telegram operations.
- **Modern Packaging**: Supports PyPI and Docker.
- **Testing**: Unit tests for core functionality.
- **CI/CD**: Automated testing via GitHub Actions.

## Installation

### Prerequisites
- Python 3.8+
- Docker (optional)

### Install via pip
```bash
pip install -e .
```

### Install via Docker
```bash
docker build -t mobileinfoga .
docker run -it --rm mobileinfoga
```

## Configuration

1. Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your Telegram API credentials:
   ```env
   API_ID=123456
   API_HASH=your_api_hash_here
   PHONE=+1234567890
   ```

## Usage

```bash
python mobileinfoga.py

Enter the number with country code (e.g., +1234567890): +911234567890
```

## Testing

Run tests with:
```bash
pytest
```

## CI/CD

Automated testing via GitHub Actions:
- Runs on every push/pull request.
- Tests coverage, linting, and formatting.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0.

## Acknowledgements

- [Telethon](https://github.com/LonamiWebs/Telethon)
- [Phonenumbers](https://github.com/daviddrysdale/phonenumbers)
- [Mobile Codes](https://github.com/your-repo/mobile-codes)