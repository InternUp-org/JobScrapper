# Job Scraper System

A modular job scraping system that supports multiple job platforms including JobRight and Wellfound.

## Project Structure

The project is organized into the following structure:

```
job-scraper/
├── config/              # Configuration files
│   ├── config.ini       # General settings
│   └── credentials.json # Scraper credentials
├── logs/                # Log files
├── output/              # Scraped data output
└── src/                 # Source code
    ├── config/          # Configuration management
    ├── scrapers/        # Scraper modules
    │   ├── core/        # Shared utilities
    │   ├── jobright/    # JobRight scraper
    │   ├── wellfound/   # Wellfound scraper
    │   └── run_scrapers.py # CLI interface
    └── tests/           # Unit tests
```

## Features

- Modular design that supports multiple job platforms
- Unified CLI interface to run one or all scrapers
- Shared utilities for browser management, logging, and data handling
- Configurable settings
- Test coverage for core components

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd job-scraper
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your credentials:

Edit `config/credentials.json` to add your JobRight and Wellfound login details:

```json
{
  "jobright": {
    "username": "your_email@example.com",
    "password": "your_password"
  },
  "wellfound": {
    "username": "your_email@example.com",
    "password": "your_password"
  }
}
```

## Usage

### Command Line Interface

Run both scrapers:

```bash
python src/scrapers/run_scrapers.py --all
```

Run only the JobRight scraper:

```bash
python src/scrapers/run_scrapers.py --jobright
```

Run only the Wellfound scraper:

```bash
python src/scrapers/run_scrapers.py --wellfound
```

### Options

- `--headless`: Run in headless mode (no browser UI)
- `--output-dir PATH`: Specify a custom output directory
- `--no-proxy`: Disable the MITM proxy for Wellfound scraper

Example:

```bash
python src/scrapers/run_scrapers.py --all --headless --output-dir ./my_results
```

## Wellfound Proxy Requirements

The Wellfound scraper uses mitmproxy to capture GraphQL API responses. To use this feature:

1. Install mitmproxy:

```bash
pip install mitmproxy
```

2. Ensure mitmproxy is in your PATH and can be run with `mitmdump`

## Development

### Running Tests

To run the test suite:

```bash
python -m unittest discover -s src/tests
```

### Adding a New Scraper

To add a new scraper:

1. Create a new directory under `src/scrapers/`
2. Implement the scraper using the shared utilities from `src/scrapers/core/`
3. Add an entry point in `src/scrapers/run_scrapers.py`

## Troubleshooting

### Common Issues

- **Browser initialization fails**: Make sure you have Chrome installed and accessible in the default location
- **Proxy doesn't start**: Check that mitmproxy is installed and available in your PATH
- **Login fails**: Verify your credentials in `config/credentials.json`

### Logs

Check the log files in the `logs/` directory for detailed error information.

## License

[MIT License](LICENSE)
