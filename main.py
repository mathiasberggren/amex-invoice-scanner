import pdfplumber
import re
import datetime

# Function to parse the date and return a datetime object
def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%d.%m.%y")

def clean_amount(amount_str):
    # Remove spaces, thousand separators and make commas into dots to allow python to process them
    amount_str = amount_str.replace(' ', '').replace('.','').replace(',', '.')

    return float(amount_str)

pattern = re.compile(r"""
    (\d{2}\.\d{2}\.\d{2})       # Transaction date (dd.mm.yy)
    \s+                         # One or more whitespace characters
    (\d{2}\.\d{2}\.\d{2})       # Processed date (dd.mm.yy)
    \s+                         # One or more whitespace characters
    (.+?)                       # Transaction details (non-greedy match)
    \s+                         # One or more whitespace characters
    (-?\d{1,3}(?:[.,]\d{3})*(?:,\d{2}|\.\d{2})) # Amount (e.g., 1.234,56 or 1234.56, with optional negative sign)
""", re.VERBOSE)
# Function to process each page and extract transactions
def process_page(page, file):
    text = page.extract_text()
    file.write(text + "\n\n")  # Write the text to the file with some spacing
    matches = pattern.findall(text)
    return [(match[0], match[1], match[2].replace('\n', ' ').strip(), match[3]) for match in matches]

def remove_previous_payments(transaction): 
    return "Betalning Mottagen, Tack" not in transaction[2]

# Open the PDF file
with pdfplumber.open('./test/2024-05-02.pdf') as pdf, open('extracted_text.txt', 'w', encoding='utf-8') as file:
    transactions = []
    for page in pdf.pages:
        transactions.extend(process_page(page, file))

# Sort transactions by the transaction date
transactions.sort(key=lambda x: parse_date(x[0]))

# Print the results
print("Transaction Date | Processed Date | Transaction Details | Amount (SEK)")
total_amount = 0
for transaction in transactions:
    transaction_date, processed_date, details, amount = transaction
    try:
        total_amount += clean_amount(amount)
    except ValueError as e:
        print(f"Error converting amount: {amount} - {e}")
    # total_amount += float(amount)
    print(" | ".join(transaction))


positive_transactions = list(filter(remove_previous_payments, transactions))

total_amount = sum(clean_amount(t[3]) for t in positive_transactions)
print(f"Total amount after only looking at positives: {total_amount}")