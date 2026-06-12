import csv
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent.parent / "processing_logs.csv"

def log_document_status(file_name: str, url: str, status: str, note: str):
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'File Name', 'URL', 'Status', 'Note'])
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, file_name, url, status, note])
