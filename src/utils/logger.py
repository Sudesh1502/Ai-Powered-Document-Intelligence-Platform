"""
This file provides logging functionality to track document processing status.
"""
import csv
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent.parent / "processing_logs.csv"

def log_document_status(file_name: str, url: str, status: str, note: str, start_time: datetime = None, end_time: datetime = None, word_count:int=0):
    """Logs the processing status of a document to a CSV file."""
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'File Name', 'URL', 'Status', 'Note','Word Count', 'Start Time', 'End Time', 'Processing Time (s)'])
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else ""
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else ""
        
        processing_time = ""
        if start_time and end_time:
            processing_time = str(round((end_time - start_time).total_seconds(), 2))
            
        writer.writerow([timestamp, file_name, url, status, note,word_count, start_str, end_str, processing_time])
