import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from tqdm import tqdm
import time
import pandas as pd

# Load environment variables
load_dotenv()

# Configuration from environment variables
EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")
COMPANY_LIST_PATH = os.getenv("COMPANY_LIST_PATH", "paolist.csv")

# Email settings
DELAY_BETWEEN_EMAILS = int(os.getenv("EMAIL_DELAY", 10))
SENDER_NAME = os.getenv("SENDER_NAME", "Mihir")
BCC_EMAIL = "cornellairbhangra@gmail.com"  # Cornell Bhangra org – BCC on every outreach

# Validate required configuration (PAO flow does not require OpenAI)
required_vars = {
    'EMAIL_ADDRESS': EMAIL,
    'EMAIL_PASSWORD': APP_PASSWORD,
    'COMPANY_LIST_PATH': COMPANY_LIST_PATH,
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


def main():
    """Main execution function."""
    smtp_server = None
    emails_sent = 0
    emails_skipped = 0
    try:
        df = pd.read_csv(COMPANY_LIST_PATH)
        print(f"Successfully loaded {len(df)} contacts from CSV")
        print("Connecting to Gmail SMTP server...")
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.login(EMAIL, APP_PASSWORD)
        print("Successfully connected to email server!")
        rows = df.to_dict('records')
        for row in tqdm(rows, desc="Processing contacts", unit="email"):
            email_addr = _get_csv_column(row, 'email')
            first_name = _get_csv_column(row, 'first_name', 'first name')
            last_name = _get_csv_column(row, 'last_name', 'last name')
            if not email_addr:
                print("Skipping row due to missing email")
                emails_skipped += 1
                continue
            generator = PAOEmailGenerator(
                first_name=first_name or "",
                last_name=last_name or "",
                email=email_addr
            )
            if generator.email_message:
                if generator.send_email(smtp_server):
                    emails_sent += 1
                    time.sleep(DELAY_BETWEEN_EMAILS)
                else:
                    emails_skipped += 1
            else:
                emails_skipped += 1
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if smtp_server:
            smtp_server.quit()
            print("Disconnected from email server")
        print(f"\n--- Email Campaign Summary ---")
        print(f"Emails sent successfully: {emails_sent}")
        print(f"Emails skipped or failed: {emails_skipped}")
        print(f"Total contacts processed: {emails_sent + emails_skipped}")

if __name__ == "__main__":
    main()
