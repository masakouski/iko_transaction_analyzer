#!/usr/bin/env python3
"""
Simple script to run the PDF transaction parser.
This is a convenience script that imports and runs the main parser.
"""

from transaction_parser import TransactionParser

def main():
    """Run the transaction parser with default settings."""
    print("Starting PDF Transaction Parser...")
    print("=" * 50)
    
    # Create parser instance
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
        print(f"\n✅ Successfully parsed {len(transactions)} transactions!")
        print("📄 Results saved to: assets/transactions_[timestamp].csv")
        
    else:
        print("❌ No transactions found. Please check your PDF files and folder path.")

if __name__ == "__main__":
    main()
