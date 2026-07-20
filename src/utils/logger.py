"""
This file provides logging functionality to track document processing status.
"""
import csv
import os
from datetime import datetime
from src.utils.time_utils import get_ist_now
from pathlib import Path
import pandas as pd

LOG_FILE = Path(__file__).resolve().parent.parent.parent / "processing_logs.csv"

def log_document_status(file_name: str, url: str, status: str, note: str, start_time: datetime = None, end_time: datetime = None, word_count:int=0, confidence:float=None, source:str="Unknown"):
    """Logs the processing status of a document to a CSV file."""
    file_exists = os.path.isfile(LOG_FILE)
    
    # Dynamically upgrade existing log files to include new columns if missing
    if file_exists:
        try:
            df = pd.read_csv(LOG_FILE)
            changed = False
            if 'OCR Confidence' not in df.columns:
                df['OCR Confidence'] = ""
                changed = True
            if 'Source' not in df.columns:
                df['Source'] = "Unknown"
                changed = True
            if changed:
                df.to_csv(LOG_FILE, index=False)
        except Exception:
            pass

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'File Name', 'URL', 'Status', 'Note', 'Word Count', 'Start Time', 'End Time', 'Processing Time (s)', 'OCR Confidence', 'Source'])
            
        timestamp = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
        
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else ""
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else ""
        
        processing_time = ""
        if start_time and end_time:
            processing_time = str(round((end_time - start_time).total_seconds(), 2))
            
        conf_str = str(confidence) if confidence is not None else ""
        writer.writerow([timestamp, file_name, url, status, note, word_count, start_str, end_str, processing_time, conf_str, source])



def get_logs():

    if not os.path.exists(
        LOG_FILE
    ):
        return pd.DataFrame()

    return pd.read_csv(
        LOG_FILE
    )

def get_metrics():

    logs = get_logs()

    if logs.empty:
        return {
            "processed": 0,
            "indexed": 0,
            "avg_time": 0,
            "avg_confidence": 0
        }

    processed = len(logs)

    indexed = len(
        logs[
            logs["Status"] == "Completed"
        ]
    )

    avg_time = round(
        pd.to_numeric(
            logs["Processing Time (s)"],
            errors="coerce"
        ).mean(),
        2
    )

    # Compute average OCR confidence persistently
    avg_confidence = 0.0
    if "OCR Confidence" in logs.columns:
        valid_conf = pd.to_numeric(logs["OCR Confidence"], errors="coerce").dropna()
        if not valid_conf.empty:
            avg_confidence = round(valid_conf.mean(), 2)

    return {
        "processed": processed,
        "indexed": indexed,
        "avg_time": avg_time,
        "avg_confidence": avg_confidence
    }
