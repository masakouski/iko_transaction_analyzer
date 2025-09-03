#!/usr/bin/env python3
"""
PDF Transaction Parser for Bank Statements

This script parses PDF bank statements and extracts transaction data into CSV format.
It handles various transaction types including card purchases, transfers, and currency exchanges.
"""

import pdfplumber
import pandas as pd
import re
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TransactionParser:
    """Parser for extracting transaction data from PDF bank statements."""
    
    def __init__(self, folder_path: str = "assets/filesToProcess"):
        self.folder_path = Path(folder_path)
        self.transactions = []
        
        # Regex patterns for different transaction types
        self.patterns = {
            # Main transaction pattern: Date ID Description Amount Balance
            'main_transaction': re.compile(
                r'^(\d{2}\.\d{2}\.\d{4})\s+([A-Z0-9]+)\s+(.+?)\s+(-?\d{1,3}(?:\s?\d{3})*,\d{2})\s+(\d{1,3}(?:\s?\d{3})*,\d{2})$'
            ),
            # Card transaction with additional details
            'card_transaction': re.compile(
                r'^(\d{2}\.\d{2}\.\d{4})\s+([A-Z0-9]+)\s+(ZAKUP PRZY UŻYCIU KARTY|PŁATNOŚĆ WEB|ZWROT BLIK)\s+(-?\d{1,3}(?:\s?\d{3})*,\d{2})\s+(\d{1,3}(?:\s?\d{3})*,\d{2})$'
            ),
            # Transfer transaction
            'transfer_transaction': re.compile(
                r'^(\d{2}\.\d{2}\.\d{4})\s+([A-Z0-9]+)\s+(PRZELEW WYCHODZĄCY|PRZELEW PRZYCHODZĄCY)\s+(-?\d{1,3}(?:\s?\d{3})*,\d{2})\s+(\d{1,3}(?:\s?\d{3})*,\d{2})$'
            ),
            # Currency exchange
            'currency_exchange': re.compile(
                r'^(\d{2}\.\d{2}\.\d{4})\s+([A-Z0-9]+)\s+(WYMIANA W KANTORZE - UZNANIE|WYMIANA W KANTORZE - OBCIĄŻENIE)\s+(-?\d{1,3}(?:\s?\d{3})*,\d{2})\s+(\d{1,3}(?:\s?\d{3})*,\d{2})$'
            ),
            # Balance transfer
            'balance_transfer': re.compile(
                r'^Saldo z przeniesienia\s+(\d{1,3}(?:\s?\d{3})*,\d{2})$'
            )
        }
        
        # Additional detail patterns
        self.detail_patterns = {
            'card_details': re.compile(r'^(\d{2}\.\d{2}\.\d{4})\s+Karta:(\d{4}\d{2}\*{4}\d{4})\s+Lokalizacja:\s*(.+?)\s+Nr ref:'),
            'web_payment_details': re.compile(r'^(\d{2}\.\d{2}\.\d{4})\s+Tel:(\d+)\s+Godz\.(\d{2}:\d{2}:\d{2})\s+Lokalizacja:\s*(.+?)\s+Nr ref:'),
            'original_amount': re.compile(r'^Kwota oryg\.:\s+(\d{1,3}(?:\s?\d{3})*,\d{2})\s+PLN'),
            'currency_details': re.compile(r'^(\d{2}\.\d{2}\.\d{4})\s+([A-Z0-9]+)\s+([A-Z]{3}/[A-Z]{3})\s+(\d+\.\d+)\s+(-?\d{1,3}(?:\s?\d{3})*,\d{2})\s+PLN\s+(-?\d{1,3}(?:\s?\d{3})*,\d{2})\s+([A-Z]{3})'),
            'transfer_details': re.compile(r'^(\d{10,})\s+(.+?)\s+Ref\. wł\. zlec\.:\s+(\d+)')
        }

    def clean_amount(self, amount_str: str) -> float:
        """Convert Polish number format to float."""
        if not amount_str:
            return 0.0
        # Remove spaces and replace comma with dot
        cleaned = amount_str.replace(' ', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"Could not parse amount: {amount_str}")
            return 0.0

    def parse_transaction_line(self, line: str, context_lines: List[str] = None) -> Optional[Dict]:
        """Parse a single transaction line and extract transaction data."""
        line = line.strip()
        if not line:
            return None
            
        # Try each pattern
        for pattern_name, pattern in self.patterns.items():
            match = pattern.match(line)
            if match:
                if pattern_name == 'balance_transfer':
                    return {
                        'date': None,
                        'transaction_id': 'BALANCE_TRANSFER',
                        'type': 'Saldo z przeniesienia',
                        'description': 'Balance transfer from previous period',
                        'amount': 0.0,
                        'balance': self.clean_amount(match.group(1)),
                        'raw_line': line,
                        'pattern_used': pattern_name
                    }
                else:
                    date, trans_id, description, amount, balance = match.groups()
                    return {
                        'date': date,
                        'transaction_id': trans_id,
                        'type': self._categorize_transaction(description),
                        'description': description,
                        'amount': self.clean_amount(amount),
                        'balance': self.clean_amount(balance),
                        'raw_line': line,
                        'pattern_used': pattern_name
                    }
        
        return None

    def _categorize_transaction(self, description: str) -> str:
        """Categorize transaction based on description."""
        description_lower = description.lower()
        
        if 'zakup przy użyciu karty' in description_lower:
            return 'Card Purchase'
        elif 'płatność web' in description_lower:
            return 'Web Payment'
        elif 'zwrot blik' in description_lower:
            return 'BLIK Refund'
        elif 'przelew wychodzący' in description_lower:
            return 'Outgoing Transfer'
        elif 'przelew przychodzący' in description_lower:
            return 'Incoming Transfer'
        elif 'wymiana w kantorze' in description_lower:
            return 'Currency Exchange'
        else:
            return 'Other'

    def extract_additional_details(self, lines: List[str], transaction_index: int) -> Dict:
        """Extract additional details for a transaction from surrounding lines."""
        details = {}
        
        # Look at the next few lines for additional details
        for i in range(transaction_index + 1, min(transaction_index + 5, len(lines))):
            line = lines[i].strip()
            
            # Card details
            card_match = self.detail_patterns['card_details'].match(line)
            if card_match:
                details['card_number'] = card_match.group(2)
                details['location'] = card_match.group(3)
                continue
                
            # Web payment details
            web_match = self.detail_patterns['web_payment_details'].match(line)
            if web_match:
                details['phone'] = web_match.group(2)
                details['time'] = web_match.group(3)
                details['location'] = web_match.group(4)
                continue
                
            # Original amount
            orig_match = self.detail_patterns['original_amount'].match(line)
            if orig_match:
                details['original_amount'] = self.clean_amount(orig_match.group(1))
                continue
                
            # Currency details
            curr_match = self.detail_patterns['currency_details'].match(line)
            if curr_match:
                details['currency_pair'] = curr_match.group(3)
                details['exchange_rate'] = float(curr_match.group(4))
                details['pln_amount'] = self.clean_amount(curr_match.group(5))
                details['foreign_amount'] = self.clean_amount(curr_match.group(6))
                details['foreign_currency'] = curr_match.group(7)
                continue
                
            # Transfer details
            trans_match = self.detail_patterns['transfer_details'].match(line)
            if trans_match:
                details['account_number'] = trans_match.group(1)
                details['recipient'] = trans_match.group(2)
                details['reference'] = trans_match.group(3)
                continue
        
        return details

    def parse_pdf_file(self, pdf_path: Path) -> List[Dict]:
        """Parse a single PDF file and extract all transactions."""
        transactions = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Processing {pdf_path.name} - {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        continue
                        
                    lines = text.split('\n')
                    
                    for i, line in enumerate(lines):
                        transaction = self.parse_transaction_line(line)
                        if transaction:
                            # Add file and page information
                            transaction['source_file'] = pdf_path.name
                            transaction['page'] = page_num
                            
                            # Extract additional details
                            details = self.extract_additional_details(lines, i)
                            transaction.update(details)
                            
                            transactions.append(transaction)
                            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            
        return transactions

    def parse_all_files(self) -> List[Dict]:
        """Parse all PDF files in the specified folder."""
        if not self.folder_path.exists():
            logger.error(f"Folder {self.folder_path} does not exist")
            return []
            
        pdf_files = list(self.folder_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.folder_path}")
            return []
            
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        all_transactions = []
        for pdf_file in sorted(pdf_files):
            transactions = self.parse_pdf_file(pdf_file)
            all_transactions.extend(transactions)
            logger.info(f"Extracted {len(transactions)} transactions from {pdf_file.name}")
            
        return all_transactions

    def save_to_csv(self, transactions: List[Dict], output_file: str = None):
        """Save transactions to CSV file."""
        if not transactions:
            logger.warning("No transactions to save")
            return
            
        # Generate filename with epoch timestamp if not provided
        if output_file is None:
            epoch_time = int(time.time())
            output_file = f"assets/transactions_{epoch_time}.csv"
        
        # Ensure assets directory exists
        assets_dir = Path("assets")
        assets_dir.mkdir(exist_ok=True)
            
        df = pd.DataFrame(transactions)
        
        # Reorder columns for better readability
        column_order = [
            'date', 'transaction_id', 'type', 'description', 'amount', 'balance',
            'source_file', 'page', 'card_number', 'location', 'phone', 'time',
            'original_amount', 'currency_pair', 'exchange_rate', 'pln_amount',
            'foreign_amount', 'foreign_currency', 'account_number', 'recipient',
            'reference', 'raw_line', 'pattern_used'
        ]
        
        # Only include columns that exist in the dataframe
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        df.to_csv(output_file, index=False, sep=';', encoding='utf-8')
        logger.info(f"Saved {len(transactions)} transactions to {output_file}")

    def get_summary(self, transactions: List[Dict]) -> Dict:
        """Get summary statistics of the transactions."""
        if not transactions:
            return {}
            
        df = pd.DataFrame(transactions)
        
        # Filter out transactions without dates for date range calculation
        dated_transactions = df[df['date'].notna()] if 'date' in df.columns else pd.DataFrame()
        
        summary = {
            'total_transactions': len(transactions),
            'total_amount': df['amount'].sum(),
            'date_range': {
                'start': dated_transactions['date'].min() if not dated_transactions.empty else None,
                'end': dated_transactions['date'].max() if not dated_transactions.empty else None
            },
            'transaction_types': df['type'].value_counts().to_dict() if 'type' in df.columns else {},
            'files_processed': df['source_file'].nunique() if 'source_file' in df.columns else 0
        }
        
        return summary

def main():
    """Main function to run the transaction parser."""
    parser = TransactionParser()
    
    # Parse all PDF files
    transactions = parser.parse_all_files()
    
    if transactions:
        # Save to CSV
        parser.save_to_csv(transactions)
        
        # Print summary
        summary = parser.get_summary(transactions)
        print("\n" + "="*50)
        print("TRANSACTION PARSING SUMMARY")
        print("="*50)
        print(f"Total transactions: {summary['total_transactions']}")
        print(f"Total amount: {summary['total_amount']:,.2f} PLN")
        print(f"Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"Files processed: {summary['files_processed']}")
        print("\nTransaction types:")
        for trans_type, count in summary['transaction_types'].items():
            print(f"  {trans_type}: {count}")
        print("="*50)
        
    else:
        print("No transactions found. Please check your PDF files and folder path.")

if __name__ == "__main__":
    main()
