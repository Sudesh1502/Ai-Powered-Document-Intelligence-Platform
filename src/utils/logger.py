"""
This file provides logging functionality to track document processing status.
Primary storage: Azure Table Storage (cloud-safe, survives restarts).
Fallback: Local CSV file (for local development without Azure credentials).
"""
import csv
import os
import uuid
from datetime import datetime
from src.utils.time_utils import get_ist_now
from pathlib import Path
import pandas as pd

LOG_FILE = Path(__file__).resolve().parent.parent.parent / "processing_logs.csv"
LOG_TABLE_NAME = "ProcessingLogs"
LOG_PARTITION_KEY = "Logs"


def _get_log_table_client():
    """Returns an Azure Table client for ProcessingLogs, or None if not configured."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        return None
    try:
        from azure.data.tables import TableServiceClient
        from azure.core.exceptions import ResourceExistsError
        service_client = TableServiceClient.from_connection_string(connection_string)
        try:
            service_client.create_table(LOG_TABLE_NAME)
        except ResourceExistsError:
            pass
        return service_client.get_table_client(LOG_TABLE_NAME)
    except Exception as e:
        print(f"[Logger] Failed to connect to Azure Table Storage: {e}")
        return None


def log_document_status(file_name: str, url: str, status: str, note: str, start_time: datetime = None, end_time: datetime = None, word_count: int = 0, confidence: float = None, source: str = "Unknown"):
    """Logs the processing status of a document.
    
    Writes to Azure Table Storage in cloud environments.
    Falls back to local CSV for local development.
    """
    timestamp = get_ist_now()
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else ""
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else ""
    processing_time = ""
    if start_time and end_time:
        processing_time = str(round((end_time - start_time).total_seconds(), 2))
    conf_str = str(confidence) if confidence is not None else ""

    # --- Primary: Azure Table Storage ---
    table_client = _get_log_table_client()
    if table_client:
        try:
            entity = {
                "PartitionKey": LOG_PARTITION_KEY,
                "RowKey": str(uuid.uuid4()),
                "Timestamp_IST": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "FileName": file_name,
                "URL": url or "",
                "Status": status,
                "Note": note or "",
                "WordCount": str(word_count),
                "StartTime": start_str,
                "EndTime": end_str,
                "ProcessingTime": processing_time,
                "OCRConfidence": conf_str,
                "Source": source,
            }
            table_client.upsert_entity(entity=entity)
            return
        except Exception as e:
            print(f"[Logger] Azure Table write failed, falling back to CSV: {e}")

    # --- Fallback: Local CSV (dev environment) ---
    file_exists = os.path.isfile(LOG_FILE)
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
        writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), file_name, url, status, note, word_count, start_str, end_str, processing_time, conf_str, source])


def get_logs():
    """Returns all log entries as a DataFrame.
    
    Reads from Azure Table Storage in cloud. Falls back to local CSV.
    """
    table_client = _get_log_table_client()
    if table_client:
        try:
            entities = list(table_client.query_entities(query_filter=f"PartitionKey eq '{LOG_PARTITION_KEY}'"))
            if entities:
                rows = []
                for e in entities:
                    rows.append({
                        "Timestamp": e.get("Timestamp_IST", ""),
                        "File Name": e.get("FileName", ""),
                        "URL": e.get("URL", ""),
                        "Status": e.get("Status", ""),
                        "Note": e.get("Note", ""),
                        "Word Count": e.get("WordCount", 0),
                        "Start Time": e.get("StartTime", ""),
                        "End Time": e.get("EndTime", ""),
                        "Processing Time (s)": e.get("ProcessingTime", ""),
                        "OCR Confidence": e.get("OCRConfidence", ""),
                        "Source": e.get("Source", ""),
                    })
                return pd.DataFrame(rows)
        except Exception as e:
            print(f"[Logger] Failed to read from Azure Table Storage: {e}")

    # Fallback: local CSV
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()
    return pd.read_csv(LOG_FILE)


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
    indexed = len(logs[logs["Status"] == "Completed"])
    avg_time = round(pd.to_numeric(logs["Processing Time (s)"], errors="coerce").mean(), 2)

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
