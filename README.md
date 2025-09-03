# PDF Transaction Parser

A Python script that extracts transaction data from PDF bank statements and converts them into a structured CSV format for easy analysis.

## Features

- **Automatic PDF Processing**: Processes all PDF files in the `assets/filesToProcess` folder
- **Multiple Transaction Types**: Handles card purchases, web payments, transfers, currency exchanges, and more
- **Detailed Extraction**: Extracts transaction details including dates, amounts, descriptions, and additional metadata
- **Robust Parsing**: Uses regex patterns to handle various transaction formats
- **CSV Output**: Generates clean, structured CSV files for data analysis
- **Comprehensive Logging**: Provides detailed processing information and error handling

## Supported Transaction Types

- **Card Purchase** (`ZAKUP PRZY UŻYCIU KARTY`)
- **Web Payment** (`PŁATNOŚĆ WEB - KOD MOBILNY`)
- **BLIK Refund** (`ZWROT BLIK`)
- **Outgoing Transfer** (`PRZELEW WYCHODZĄCY`)
- **Incoming Transfer** (`PRZELEW PRZYCHODZĄCY`)
- **Currency Exchange** (`WYMIANA W KANTORZE`)
- **Balance Transfer** (`Saldo z przeniesienia`)

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Place your PDF files** in the `assets/filesToProcess` folder

   > **Note**: The `assets/` folder is automatically ignored by git to keep your personal data private.

## Usage

### Quick Start

Run the parser with default settings:

```bash
python run_parser.py
```

Or run the main parser directly:

```bash
python transaction_parser.py
```

### Programmatic Usage

```python
from transaction_parser import TransactionParser

# Create parser instance
parser = TransactionParser("assets/filesToProcess")

# Parse all PDF files
transactions = parser.parse_all_files()

# Save to CSV (will generate timestamped filename)
parser.save_to_csv(transactions)

# Get summary statistics
summary = parser.get_summary(transactions)
print(f"Total transactions: {summary['total_transactions']}")
```

## Output Format

The parser generates timestamped CSV files in the `assets/` folder with the format `transactions_[epoch_timestamp].csv`. The following columns are included:

| Column | Description |
|--------|-------------|
| `date` | Transaction date (DD.MM.YYYY) |
| `transaction_id` | Unique transaction identifier |
| `type` | Transaction category |
| `description` | Transaction description |
| `amount` | Transaction amount (negative for debits) |
| `balance` | Account balance after transaction |
| `source_file` | Source PDF filename |
| `page` | Page number in PDF |
| `card_number` | Card number (for card transactions) |
| `location` | Transaction location |
| `phone` | Phone number (for web payments) |
| `time` | Transaction time (for web payments) |
| `original_amount` | Original amount in foreign currency |
| `currency_pair` | Currency exchange pair (e.g., USD/PLN) |
| `exchange_rate` | Exchange rate used |
| `pln_amount` | Amount in PLN |
| `foreign_amount` | Amount in foreign currency |
| `foreign_currency` | Foreign currency code |
| `account_number` | Account number (for transfers) |
| `recipient` | Transfer recipient |
| `reference` | Transaction reference number |
| `raw_line` | Original text line from PDF |
| `pattern_used` | Regex pattern that matched |

## Example Output

```csv
date;transaction_id;type;description;amount;balance;source_file;page;card_number;location;original_amount
27.11.2024;4832MX90890051722;Card Purchase;ZAKUP PRZY UŻYCIU KARTY;-36.12;1968.11;Wyciag_10_68102010130000020205204567_20241223646602137.pdf;2;425125******6482;MEET& EAT 03 WARSZAWA PL;36.12
27.11.2024;4832MX92420015159;Web Payment;PŁATNOŚĆ WEB - KOD MOBILNY;-776.95;1191.16;Wyciag_10_68102010130000020205204567_20241223646602137.pdf;2;;www.zalando.de;776.95
```

## File Structure

```
transaction_analyzer/
├── assets/
│   ├── filesToProcess/          # Place your PDF files here
│   │   ├── statement1.pdf
│   │   ├── statement2.pdf
│   │   └── ...
│   └── transactions_[timestamp].csv  # Generated output files
├── transaction_parser.py    # Main parser class
├── run_parser.py           # Simple runner script
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── .gitignore             # Git ignore file (excludes assets/)
```

## Configuration

You can customize the parser behavior by modifying the `TransactionParser` class:

- **Folder Path**: Change the default folder path in the constructor
- **Output File**: Output files are automatically named with timestamps in the `assets/` folder
- **Regex Patterns**: Modify patterns in the `__init__` method for different transaction formats

## Error Handling

The parser includes comprehensive error handling:

- **File Access Errors**: Logs and continues processing other files
- **PDF Parsing Errors**: Handles corrupted or unreadable PDFs gracefully
- **Data Validation**: Validates extracted data and logs warnings for invalid entries
- **Missing Dependencies**: Provides clear error messages for missing packages

## Troubleshooting

### Common Issues

1. **No transactions found**:
   - Check that PDF files are in the `assets/filesToProcess` folder
   - Verify PDF files contain text (not just images)
   - Check file permissions

2. **Parsing errors**:
   - Ensure PDF files are not password-protected
   - Check that the PDF format matches expected bank statement format

3. **Missing dependencies**:
   ```bash
   pip install pdfplumber pandas
   ```

### Debug Mode

For detailed debugging, you can modify the logging level in `transaction_parser.py`:

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## Performance

- **Processing Speed**: Typically processes 100-200 transactions per second
- **Memory Usage**: Low memory footprint, processes files one at a time
- **File Size**: Handles PDF files of any size

## Contributing

To extend the parser for different bank formats:

1. Add new regex patterns in the `__init__` method
2. Update the `_categorize_transaction` method for new transaction types
3. Add new detail extraction patterns as needed

## License

This project is open source and available under the MIT License.
