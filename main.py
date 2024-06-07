import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import datetime

# Convert PDF to images
pages = convert_from_path('./test/2024-05-02.pdf', 300)

# Regex pattern searching for details
pattern = r"(\d{2}\.\d{2}\.\d{2})\s+(\d{2}\.\d{2}\.\d{2})\s+([\w\s*]+)\s+(\d+,\d{2})"

# Function to parse the date and return a datetime object
def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%d.%m.%y")

# OCR each page
transactions = []
for i, page in enumerate(pages):
    text = pytesseract.image_to_string(page)

    # Find all matches in the text data
    matches = re.findall(pattern, text)

    # Collect all transactions
    for match in matches:
        transaction_date, processed_date, details, amount = match
        transactions.append((transaction_date, processed_date, details.strip(), amount.replace(',', '.')))

# Sort transactions by the transaction date
transactions.sort(key=lambda x: parse_date(x[0]))

# Print the results
print("Transaction Date | Processed Date | Transaction Details | Amount (SEK)")
for transaction in transactions:
    print(" | ".join(transaction))