import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import re
import datetime


# Function to parse the date and return a datetime object
def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%d.%m.%y")

def preprocess_image(page):
    # Convert to grayscale
    page = page.convert('L')
    # Enhance the image to make it more clear
    page = ImageEnhance.Contrast(page).enhance(2)
    page = ImageEnhance.Sharpness(page).enhance(2)
    # Apply thresholding
    page = page.point(lambda p: p > 128 and 255)
    return page

# Convert PDF to images
pages = convert_from_path('./test/2024-05-02.pdf', 300)
pages = [preprocess_image(page) for page in pages]

# Regex pattern searching for details
pattern = r"(\d{2}\.\d{2}\.\d{2})\s+(\d{2}\.\d{2}\.\d{2})\s+([\w\s*]+)\s+(\d+,\d{2})"
# OCR each page
transactions = []
for i, page in enumerate(pages):
    # Specify the language as Swedish ('swe') along with English ('eng') if needed
    text = pytesseract.image_to_string(page, lang='swe+eng', config='--psm 3')

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