import pdfplumber
import re
import datetime
import csv

### Constants
pdf_input_file = './data/2024-05-02.pdf'
csv_output_file = './data/transactions.csv'
pattern = re.compile(r"""
    (\d{2}\.\d{2}\.\d{2})       # Transaction date (dd.mm.yy)
    \s+                         # One or more whitespace characters
    (\d{2}\.\d{2}\.\d{2})       # Processed date (dd.mm.yy)
    \s+                         # One or more whitespace characters
    (.+?)                       # Transaction details (non-greedy match)
    \s+                         # One or more whitespace characters
    (-?\d{1,3}(?:[.,]\d{3})*(?:,\d{2}|\.\d{2})) # Amount (e.g., 1.234,56 or 1234.56, with optional negative sign)
""", re.VERBOSE)

# Function to parse the date and return a datetime object
def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%d.%m.%y")

def clean_amount(amount_str):
    # Remove spaces, thousand separators and make commas into dots to allow python to process them
    amount_str = amount_str.replace(' ', '').replace('.','').replace(',', '.')

    return float(amount_str)

# Function to process each page and extract transactions
def process_page(page):
    text = page.extract_text()
    matches = pattern.findall(text)
    return [(match[0], match[1], match[2].replace('\n', ' ').strip(), clean_amount(match[3])) for match in matches]

def remove_previous_payments(transaction): 
    return "Betalning Mottagen, Tack" not in transaction[2]

# Open the PDF file
with pdfplumber.open(pdf_input_file) as pdf:
    transactions = []
    for page in pdf.pages:
        transactions.extend(process_page(page))

# Sort transactions by the transaction date
transactions.sort(key=lambda x: parse_date(x[0]))

# Print the results
print("Transaction Date | Processed Date | Transaction Details | Amount (SEK)")
for transaction in transactions:
    transaction_date, processed_date, details, amount = transaction
    transaction_string = f"{transaction_date} | {processed_date} | {details} | {amount}"
    print(transaction_string)


valid_transactions = list(filter(remove_previous_payments, transactions))
total_amount = sum(map(lambda x: x[3], valid_transactions))


line_num = 1
with open(csv_output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Transaction Date", "Processed Date", "Transaction Details", "Amount (SEK)", "Ida", "Mathias", "Gemensamt"])
    for i, transaction in enumerate(valid_transactions):
        # Add empty values for "Ida" and "Mathias" directly to the tuple
        new_transaction = transaction + ('', '', f"=SUM(D{i + 2}-E{i + 2}-F{i + 2})",)

        writer.writerow(new_transaction)
        line_num = i + 1
    
    writer.writerow(["", "", "", f"=SUM(D2:D{line_num + 1})", f"=SUM(E2:E{line_num + 1})", f"=SUM(F2:F{line_num + 1})", f"=SUM(G2:G{line_num + 1})"])
    line_num += 1
    writer.writerow(["", "", "", "", "", "", ""])
    line_num += 1
    writer.writerow(["", "", "", "", "", "", ""])
    line_num += 1
    writer.writerow(["", "", "", "Att betala", "Ida", "Mathias", "Totalt"])
    line_num += 1
    writer.writerow(["", "", "", "", 
                     f"=SUM(E{line_num - 2}+G{line_num - 2}/2)",
                     f"=SUM(F{line_num - 2}+G{line_num - 2}/2)"])
    

print(f"Total amount after only looking at positives: {total_amount}")

