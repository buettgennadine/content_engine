"""
Gmail IMAP reader for newsletter ingestion.
Fetches unread emails from descartes.research@gmail.com
"""
import imaplib
import email
import logging
import os
from email.header import decode_header
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)


def decode_str(s) -> str:
    if isinstance(s, bytes):
        return s.decode("utf-8", errors="replace")
    return str(s)


def get_email_text(msg) -> str:
    """Extract plain text from email message."""
    text_parts = []
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                text_parts.append(payload.decode("utf-8", errors="replace"))
        elif content_type == "text/html" and not text_parts:
            payload = part.get_payload(decode=True)
            if payload:
                soup = BeautifulSoup(payload.decode("utf-8", errors="replace"), "lxml")
                text_parts.append(soup.get_text(separator=" "))
    return " ".join(text_parts)[:1000]


def fetch_newsletter_emails(limit: int = 20) -> list[dict]:
    """
    Connect to Gmail IMAP and fetch unread emails.
    Returns list of {subject, sender, date, snippet} dicts.
    """
    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not user or not password:
        logger.warning("Gmail credentials not configured — skipping IMAP fetch")
        return []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        _, data = mail.search(None, "UNSEEN")
        email_ids = data[0].split()[-limit:]  # last N unseen

        results = []
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject_raw = decode_header(msg["Subject"])[0]
            subject = decode_str(subject_raw[0])
            sender = msg.get("From", "")
            date = msg.get("Date", "")
            snippet = get_email_text(msg)[:500]

            results.append({
                "title": subject,
                "url": f"imap:{eid.decode()}",  # synthetic URL for dedup
                "source_type": "imap",
                "snippet": snippet,
                "published_date": date,
                "sender": sender,
            })

            # Mark as read
            mail.store(eid, "+FLAGS", "\\Seen")

        mail.logout()
        logger.info(f"Fetched {len(results)} newsletter emails")
        return results

    except Exception as e:
        logger.error(f"IMAP fetch failed: {e}")
        return []
