import os
from dotenv import load_dotenv
import pdfplumber
import re
import datetime
import csv
import locale

# Load environment variables
load_dotenv()

# Set the locale to Swedish
locale.setlocale(locale.LC_ALL, 'sv_SE.UTF-8')

### Constants
PDF_INPUT_FILE = './data/2024-10-02.pdf'
CSV_OUTPUT_FILE = './data/transactions.csv'

# Salary constants from environment variables
try:
    MATHIAS_SALARY_BEFORE_TAX = float(os.getenv('MATHIAS_SALARY_BEFORE_TAX'))
    MATHIAS_SALARY_AFTER_TAX = float(os.getenv('MATHIAS_SALARY_AFTER_TAX'))
    IDA_SALARY_BEFORE_TAX = float(os.getenv('IDA_SALARY_BEFORE_TAX'))
    IDA_SALARY_AFTER_TAX = float(os.getenv('IDA_SALARY_AFTER_TAX'))
except (TypeError, ValueError):
    raise ValueError("One or more salary environment variables are not set or are not valid numbers.")

# Calculate percentages
TOTAL_AFTER_TAX = MATHIAS_SALARY_AFTER_TAX + IDA_SALARY_AFTER_TAX
MATHIAS_PERCENTAGE = MATHIAS_SALARY_AFTER_TAX / TOTAL_AFTER_TAX
IDA_PERCENTAGE = IDA_SALARY_AFTER_TAX / TOTAL_AFTER_TAX

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
    """Write transactions to a CSV file with additional formulas and salary information in Swedish."""
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write salary information
        writer.writerow(["Löneinformation", "Före skatt", "Efter skatt"])
        writer.writerow(["Mathias", MATHIAS_SALARY_BEFORE_TAX, MATHIAS_SALARY_AFTER_TAX])
        writer.writerow(["Ida", IDA_SALARY_BEFORE_TAX, IDA_SALARY_AFTER_TAX])
        writer.writerow([])  # Empty row for spacing
        
        # Write percentages
        writer.writerow(["Fördelningsprocent", f"Ida: {IDA_PERCENTAGE:.2%}", f"Mathias: {MATHIAS_PERCENTAGE:.2%}"])
        writer.writerow([])  # Empty row for spacing
        
        # Write transaction headers
        writer.writerow(["Transaktionsdatum", "Behandlingsdatum", "Transaktionsdetaljer", "Belopp (SEK)", "Ida", "Mathias", "Gemensamt"])
        
        for i, transaction in enumerate(transactions, start=8):  # Start from row 8 due to added information
            new_transaction = transaction + ('', '', f'=SUM(D{i}-E{i}-F{i})')
            writer.writerow(new_transaction)
        
        total_sums_row = [
            "", "", "Totalt", 
            f'=SUM(D8:D{i})', 
            f'=SUM(E8:E{i})', 
            f'=SUM(F8:F{i})', 
            f'=SUM(G8:G{i})'
        ]
        writer.writerow(total_sums_row)
        
        # For spacing
        empty_row = ["", "", "", "", "", "", ""]
        writer.writerow(empty_row)
        writer.writerow(empty_row)
        
        summary_header_row = ["", "", "", "Att betala", f"Ida ({IDA_PERCENTAGE:.2%})", f"Mathias ({MATHIAS_PERCENTAGE:.2%})", "Totalt"]
        writer.writerow(summary_header_row)
        
        summary_values_row = [
            "", "", "", "",
            f'=E{i+1}+G{i+1}*{IDA_PERCENTAGE}',  # Ida's share
            f'=F{i+1}+G{i+1}*{MATHIAS_PERCENTAGE}',  # Mathias's share
            f'=D{i+1}'  # Total
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
    print(f"Total amount after only considering relevant transactions: {total_amount:.2f}")

if __name__ == "__main__":
    main()

