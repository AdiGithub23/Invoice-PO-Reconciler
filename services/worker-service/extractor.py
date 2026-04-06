import csv
import io
import re
import fitz  # PyMuPDF

def extract_from_csv(content: bytes) -> dict:
    """Parses CSV bytes into a dictionary of fields."""
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    
    # Normalize headers to lowercase/stripped
    reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
    row = next(reader)
    
    return {
        "invoice_number": row.get("invoice_number", "").strip(),
        "vendor_name": row.get("vendor_name", "").strip(),
        "invoice_amount": float(row.get("invoice_amount", 0)),
        "invoice_date": row.get("invoice_date", "").strip(),
        "po_number": row.get("po_number", "").strip()
    }

def extract_from_pdf(content: bytes) -> dict:
    """Uses Regex to find fields in PDF text."""
    doc = fitz.open(stream=content, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)

    def search(pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    # Common patterns for invoices
    inv_num = search(r"Invoice\s*#?\s*[:\-]?\s*(\S+)")
    vendor = search(r"Vendor\s*[:\-]?\s*(.+)")
    # Matches amounts like 1,200.50 or 500
    raw_amount = search(r"(?:Total|Amount)\s*[:\-]?\s*\$?([\d,]+\.?\d*)")
    date = search(r"(?:Date)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})")
    po_num = search(r"PO\s*(?:Number|#|No)?\s*[:\-]?\s*(\S+)")

    amount = float(raw_amount.replace(",", "")) if raw_amount else 0.0

    return {
        "invoice_number": inv_num,
        "vendor_name": vendor,
        "invoice_amount": amount,
        "invoice_date": date,
        "po_number": po_num
    }

