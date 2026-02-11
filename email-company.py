import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from tqdm import tqdm
import time
from datetime import datetime
import pandas as pd

# Load environment variables
load_dotenv()

# Configuration from environment variables
EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")
# Default paths (overridable via CLI flags)
DEFAULT_COMPANY_LIST_PATH = "data/paolist.csv"

# Email settings
DELAY_BETWEEN_EMAILS = int(os.getenv("EMAIL_DELAY", 10))
SENDER_NAME = os.getenv("SENDER_NAME", "Mihir")
BCC_EMAIL = "cornellairbhangra@gmail.com"  # Cornell Bhangra org – BCC on every outreach

# Sending / logging behavior
DEFAULT_SENT_LOG_PATH = "pao_sent_log.csv"
DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", 100))

# Validate required configuration (PAO flow does not require OpenAI)
required_vars = {
    'EMAIL_ADDRESS': EMAIL,
    'EMAIL_PASSWORD': APP_PASSWORD,
    'SENDER_NAME': SENDER_NAME
}

missing_vars = [var for var, val in required_vars.items() if not val]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}. Please check your .env file.")

# PAO Bhangra invitation email template
PAO_EMAIL_SUBJECT = "Invitation to PAO Bhangra XXIII: March 7, 2026!"

PAO_TICKETS_URL = "https://vivenu.com/event/pao-bhangra-xxiii-fiq6q5"

PAO_EMAIL_TEMPLATE = '''<p>Hello {first_name},</p>

<p>I hope this email finds you well! My name is Mihir, and I am a member of Cornell Bhangra, a competitive, gender-inclusive bhangra dance team that competes in national competitions and performs for Cornell and Ithaca community events. Bhangra is a joyful, energetic folk dance that originated in the region of Punjab in India and Pakistan. Our mission is to dance bhangra, engage with and share Punjabi culture, be a supportive network of friends and peers, and give back to our personal, local, and global communities.</p>

<p>PAO Bhangra is Cornell Bhangra's annual bhangra exhibition which aims to share South Asian culture with the larger community and promote the aspect of bhangra we love the most – the joy of performing! We have teams from across the country and campus performing and I would love to have you there! It's number 57 on 161 things to do at Cornell and it's one of the largest events at Cornell. <b>This year, PAO XXIII is going to be in Barton Hall on March 7th. Tickets are 3 dollars and can be found</b> <a href="{tickets_url}">here</a>. We would deeply appreciate it if you could share this link with students, colleagues and friends who would enjoy the show.</p>

<p>Linked <a href="https://youtu.be/4qmpnwyFTcw">here</a> is our award-winning performance at the 2024 national Bhangra competition in Washington, D.C. — take a look at our amazing team!</p>

<p>Thank you so much! I look forward to seeing you at PAO Bhangra XXIII!</p>

<p>Sincerely,<br>
{sender_name}</p>
'''


class PAOEmailGenerator:
    """Email generator for PAO Bhangra invitation outreach."""

    def __init__(self, first_name, last_name, email):
        self.first_name = first_name.strip() if first_name else ""
        self.last_name = last_name.strip() if last_name else ""
        self.recipient_email = email.strip()
        self.email_message = None
        self.create_email_message()

    def create_email_message(self):
        """Create the PAO invitation email from the fixed template."""
        try:
            body = PAO_EMAIL_TEMPLATE.format(
                first_name=self.first_name or "there",
                sender_name=SENDER_NAME,
                tickets_url=PAO_TICKETS_URL
            )
            msg = MIMEMultipart()
            msg['From'] = f"{SENDER_NAME} <{EMAIL}>"
            msg['To'] = self.recipient_email
            msg['Subject'] = PAO_EMAIL_SUBJECT
            msg.attach(MIMEText(body, 'html'))
            self.email_message = msg.as_string()
        except Exception as e:
            print(f"Error creating email message for {self.recipient_email}: {e}")
            self.email_message = None

    def send_email(self, smtp_server):
        """Send the email using the provided SMTP server."""
        if not self.email_message:
            return False
        try:
            smtp_server.sendmail(EMAIL, [self.recipient_email, BCC_EMAIL], self.email_message)
            display_name = f"{self.first_name} {self.last_name}".strip() or self.recipient_email
            print(f"Email sent successfully to {display_name}")
            return True
        except Exception as e:
            display_name = f"{self.first_name} {self.last_name}".strip() or self.recipient_email
            print(f"Failed to send email to {display_name}: {e}")
            return False

def _get_csv_column(row, *candidates):
    """Return the first existing column value from row (supports 'first_name', 'First Name', etc.)."""
    row_lower = {str(k).strip().lower(): k for k in row}
    for key in candidates:
        key_lower = key.lower().strip()
        if key_lower in row_lower:
            val = row.get(row_lower[key_lower])
            if pd.notna(val) and str(val).strip():
                return str(val).strip()
        # try with space instead of underscore
        alt = key_lower.replace('_', ' ')
        if alt in row_lower:
            val = row.get(row_lower[alt])
            if pd.notna(val) and str(val).strip():
                return str(val).strip()
    return None


def _load_sent_emails(log_path: str) -> set:
    """
    Load already-emailed addresses from the log CSV.
    Returns a lowercase set of email strings.
    """
    if not os.path.isfile(log_path):
        return set()
    try:
        df = pd.read_csv(log_path)
        if "email" not in df.columns:
            return set()
        return set(
            df["email"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.lower()
        )
    except Exception as e:
        print(f"Warning: could not read sent log '{log_path}': {e}")
        return set()


def _append_to_sent_log(log_path: str, rows: list[dict]) -> None:
    """Append newly sent emails to the log CSV."""
    if not rows:
        return
    df = pd.DataFrame(rows)
    file_exists = os.path.isfile(log_path)
    df.to_csv(log_path, mode="a" if file_exists else "w", header=not file_exists, index=False)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for input contacts and sent-log paths."""
    parser = argparse.ArgumentParser(description="Send PAO Bhangra email campaign.")
    parser.add_argument(
        "--contacts-csv",
        "-c",
        default=DEFAULT_COMPANY_LIST_PATH,
        help=f"Path to contacts CSV (default: {DEFAULT_COMPANY_LIST_PATH})",
    )
    parser.add_argument(
        "--sent-log",
        "-l",
        default=DEFAULT_SENT_LOG_PATH,
        help=f"Path to sent-log CSV (default: {DEFAULT_SENT_LOG_PATH})",
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    contacts_path = args.contacts_csv
    sent_log_path = args.sent_log

    smtp_server = None
    emails_sent = 0
    emails_skipped = 0
    log_rows: list[dict] = []

    try:
        df = pd.read_csv(contacts_path)
        print(f"Successfully loaded {len(df)} contacts from CSV: {contacts_path}")

        # Determine which emails have already been contacted
        sent_emails = _load_sent_emails(sent_log_path)
        print(f"Loaded {len(sent_emails)} previously contacted emails from {sent_log_path}")

        remaining_quota = DAILY_SEND_LIMIT
        print(f"Daily send limit: {DAILY_SEND_LIMIT}")

        print("Connecting to Gmail SMTP server...")
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.login(EMAIL, APP_PASSWORD)
        print("Successfully connected to email server!")

        rows = df.to_dict('records')
        for row in tqdm(rows, desc="Processing contacts", unit="email"):
            if remaining_quota <= 0:
                print("Daily send limit reached; stopping for today.")
                break

            email_addr = _get_csv_column(row, 'email')
            first_name = _get_csv_column(row, 'first_name', 'first name')
            last_name = _get_csv_column(row, 'last_name', 'last name')

            if not email_addr:
                print("Skipping row due to missing email")
                emails_skipped += 1
                continue

            normalized_email = email_addr.strip().lower()
            if normalized_email in sent_emails:
                # Already contacted in a previous run
                emails_skipped += 1
                continue

            generator = PAOEmailGenerator(
                first_name=first_name or "",
                last_name=last_name or "",
                email=email_addr
            )

            if not generator.email_message:
                emails_skipped += 1
                continue

            if generator.send_email(smtp_server):
                emails_sent += 1
                remaining_quota -= 1
                sent_emails.add(normalized_email)
                log_rows.append({
                    "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds"),
                    "first_name": first_name or "",
                    "last_name": last_name or "",
                    "email": email_addr.strip(),
                })
                time.sleep(DELAY_BETWEEN_EMAILS)
            else:
                emails_skipped += 1

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Persist log of newly sent emails
        try:
            _append_to_sent_log(sent_log_path, log_rows)
            if log_rows:
                print(f"Wrote {len(log_rows)} new rows to {sent_log_path}")
        except Exception as log_err:
            print(f"Warning: failed to write sent log: {log_err}")

        if smtp_server:
            smtp_server.quit()
            print("Disconnected from email server")

        print(f"\n--- Email Campaign Summary ---")
        print(f"Emails sent successfully: {emails_sent}")
        print(f"Emails skipped or failed (including already-contacted): {emails_skipped}")
        print(f"Total contacts processed this run: {emails_sent + emails_skipped}")

if __name__ == "__main__":
    main()
