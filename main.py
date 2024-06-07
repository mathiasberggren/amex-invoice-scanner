import pdfplumber
import re
import datetime
import csv

### Constants
PDF_INPUT_FILE = './data/2024-05-02.pdf'
CSV_OUTPUT_FILE = './data/transactions.csv'
PATTERN = re.compile(r"""
    (\d{2}\.\d{2}\.\d{2})       # Transaction date (dd.mm.yy)
    \s+                         # One or more whitespace characters
    (\d{2}\.\d{2}\.\d{2})       # Processed date (dd.mm.yy)
    \s+                         # One or more whitespace characters
    (.+?)                       # Transaction details (non-greedy match)
    \s+                         # One or more whitespace characters
    (-?\d{1,3}(?:[.,]\d{3})*(?:,\d{2}|\.\d{2})) # Amount (e.g., 1.234,56 or 1234.56, with optional negative sign)
""", re.VERBOSE)

def parse_date(date_str):
    """Parse the date and return a datetime object."""
    return datetime.datetime.strptime(date_str, "%d.%m.%y")

def clean_amount(amount_str):
    """Remove spaces, thousand separators and make commas into dots to allow python to process them"""
    amount_str = amount_str.replace(' ', '').replace('.','').replace(',', '.')

    return float(amount_str)

def process_page(page):
    """Process a page and return a list of transactions."""
    text = page.extract_text()
    matches = PATTERN.findall(text)
    return [(match[0], match[1], match[2].replace('\n', ' ').strip(), clean_amount(match[3])) for match in matches]

def remove_previous_payments(transaction): 
    """Filter out transactions with 'Betalning Mottagen, Tack' in the details."""
    return "Betalning Mottagen, Tack" not in transaction[2]

def read_pdf_transactions(pdf_file):
    """Read transactions from a PDF file. Returns a list of transactions."""
    transactions = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            transactions.extend(process_page(page))
    return transactions

def write_transactions_to_csv(transactions, csv_file):
    """Write transactions to a CSV file with additional formulas."""
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Transaction Date", "Processed Date", "Transaction Details", "Amount (SEK)", "Ida", "Mathias", "Gemensamt"])
        
        for i, transaction in enumerate(transactions, start=2):
            new_transaction = transaction + ('', '', f"=SUM(D{i}-E{i}-F{i})")
            writer.writerow(new_transaction)
        
        total_sums_row = ["", "", "", f"=SUM(D2:D{i})", f"=SUM(E2:E{i})", f"=SUM(F2:F{i})", f"=SUM(G2:G{i})"]
        writer.writerow(total_sums_row)
        
        # For spacing
        empty_row = ["", "", "", "", "", "", ""]

        writer.writerow(empty_row)
        writer.writerow(empty_row)
        
        summary_header_row = ["", "", "", "Att betala", "Ida", "Mathias", "Totalt"]
        writer.writerow(summary_header_row)
        
        summary_values_row = [
            "", "", "", "",
            f"=SUM(E{i + 1}+G{i + 1}/2)",
            f"=SUM(F{i + 1}+G{i + 1}/2)"
        ]
        writer.writerow(summary_values_row)

def main():
    transactions = read_pdf_transactions(PDF_INPUT_FILE)
    transactions.sort(key=lambda x: parse_date(x[0]))

    print("Transaction Date | Processed Date | Transaction Details | Amount (SEK)")
    for transaction in transactions:
        print(" | ".join(map(str, transaction)))

    valid_transactions = list(filter(remove_previous_payments, transactions))
    total_amount = sum(map(lambda x: x[3], valid_transactions))

    write_transactions_to_csv(valid_transactions, CSV_OUTPUT_FILE)
    print(f"Total amount after only considering relevant transactions: {total_amount}")

if __name__ == "__main__":
    main()

