import imaplib
import email
from email.header import decode_header
import os
from typing import List, Dict, Any

class GmailAgent:
    """Agent responsible for polling a Gmail inbox and extracting emails and attachments."""
    
    def __init__(self):
        self.username = os.getenv("GMAIL_EMAIL")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        self.imap_server = "imap.gmail.com"
        self.mail = None

    def connect(self) -> bool:
        """Connects to the Gmail IMAP server using the App Password."""
        if not self.username or not self.password:
            print("Error: GMAIL_EMAIL or GMAIL_APP_PASSWORD is not set in .env")
            return False
            
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"Failed to connect to Gmail: {e}")
            return False

    def fetch_unseen_emails(self) -> List[Dict[str, Any]]:
        """Scans the inbox for unread emails, extracting the body and any file attachments."""
        if not self.mail:
            print("Not connected to Gmail.")
            return []

        self.mail.select("inbox")
        # Search for all unread emails
        status, messages = self.mail.search(None, "UNSEEN")
        
        email_data_list = []

        if status == "OK" and messages[0]:
            email_ids = messages[0].split()
            for e_id in email_ids:
                res, msg_data = self.mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode the email subject
                        subject = "No Subject"
                        if msg["Subject"]:
                            subject_bytes, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject_bytes, bytes):
                                subject = subject_bytes.decode(encoding if encoding else "utf-8", errors="ignore")
                            else:
                                subject = subject_bytes
                        
                        body = ""
                        attachments = []
                        
                        # Walk through the email parts (handling attachments and text)
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                if "attachment" in content_disposition or part.get_filename():
                                    filename = part.get_filename()
                                    if filename and filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.docx')):
                                        file_data = part.get_payload(decode=True)
                                        attachments.append({"filename": filename, "data": file_data})
                                elif content_type == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body += payload.decode(errors="ignore")
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors="ignore")
                            
                        email_data_list.append({
                            "id": e_id,
                            "subject": subject,
                            "body": body.strip(),
                            "attachments": attachments
                        })
        return email_data_list

    def mark_as_read(self, email_id: bytes):
        """Marks a specific email as read so it isn't processed again."""
        if self.mail:
            self.mail.store(email_id, '+FLAGS', '\\Seen')

    def disconnect(self):
        """Closes the connection to the IMAP server."""
        if self.mail:
            try:
                self.mail.close()
            except:
                pass
            self.mail.logout()
