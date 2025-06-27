import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import time
import pandas as pd

# Load environment variables
load_dotenv()

# Configuration from environment variables
EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COMPANY_LIST_PATH = os.getenv("COMPANY_LIST_PATH", "ai_companies.csv")
CV_PDF_PATH = os.getenv("CV_PDF_PATH", "cv/cv.pdf")
PROMPT_TEMPLATE_PATH = os.getenv("PROMPT_TEMPLATE_PATH", "prompt-template/email-company.txt")

# Email settings
DELAY_BETWEEN_EMAILS = int(os.getenv("EMAIL_DELAY", 5))
SENDER_NAME = os.getenv("SENDER_NAME", "Sachin Srikanth")

# Validate required configuration
required_vars = {
    'EMAIL_ADDRESS': EMAIL,
    'EMAIL_PASSWORD': APP_PASSWORD,
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'COMPANY_LIST_PATH': COMPANY_LIST_PATH,
    'PROMPT_TEMPLATE_PATH': PROMPT_TEMPLATE_PATH,
    'SENDER_NAME': SENDER_NAME
}

missing_vars = [var for var, val in required_vars.items() if not val]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}. Please check your .env file.")

# Configure OpenAI client (after loading env vars)
client = OpenAI(api_key=OPENAI_API_KEY)

# Configure OpenAI
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def read_text_file(file_path, description=""):
    """Read a text file with comprehensive error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                print(f"Warning: {description} file at {file_path} is empty.")
                return None
            return content
    except FileNotFoundError:
        print(f"Error: {description} file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading {description} file at {file_path}: {e}")
        return None

# Fixed marketing template (with placeholder for product description sentence)
MARKETING_TEMPLATE = '''I hope this email finds you well!

My name is {sender_name}, and I am one of the founders of Toolforthat.io, a platform dedicated to providing the perfect tech tools for users' needs. We index a wide range of products and tools to allow users to streamline their workflows.

After viewing your product, we believe it would be an excellent addition to our platform. "{product_sentence}" We'd love to feature this innovative product on Toolforthat for free and help you gain visibility among potential users. Over the past 10 days, we have had over 10,000 searches on our website.

You can add information about your product here: https://toolforthat.io/submit-your-tool

If you are interested in gaining more visibility by displying your product on our landing page, please feel free to respond to this email, and we can set up a time to chat!

Looking forward to hearing from you!

Best,

{sender_name} @ Toolforthat.io

--If you want to stop receiving these emails, please reply with "STOP" in the subject line.
'''

class CompanyEmailGenerator:
    """Email generator for Toolforthat marketing outreach."""

    def __init__(self, contact_name, company_name, email, short_desc, full_desc, attachment_path=None):
        self.contact_name = contact_name
        self.company_name = company_name
        self.recipient_email = email.strip()
        self.short_desc = short_desc
        self.attachment_path = attachment_path
        self.email_message = None

        # Generate product description sentence
        product_sentence = self.generate_product_sentence()
        if not product_sentence:
            print(f"Failed to generate product description for {company_name}")
            return

        # Create email message
        self.create_email_message(product_sentence)

    def generate_product_sentence(self):
        """Generate a single sentence describing the product using short description only."""
        try:
            prompt = (
                f"Write one concise, positive sentence describing the product based on the following information. "
                f"Short description: {self.short_desc}\n"
                f"The sentence should be suitable for a marketing email to the product's creators."
            )
            response = client.chat.completions.create(model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a marketing expert writing for a B2B SaaS platform."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=60,
            temperature=0.7)
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            print(f"Error generating product description for {self.company_name}: {e}")
            return None

    def create_email_message(self, product_sentence):
        """Create the complete marketing email message with proper formatting and attachments."""
        try:
            subject = "Feature your product on Toolforthat.io"
            body = MARKETING_TEMPLATE.format(
                sender_name=SENDER_NAME,
                product_sentence=product_sentence
            )
            msg = MIMEMultipart()
            msg['From'] = f"{SENDER_NAME} <{EMAIL}>"
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            if self.attachment_path and os.path.exists(self.attachment_path):
                self.attach_file(msg, self.attachment_path)
            self.email_message = msg.as_string()
        except Exception as e:
            print(f"Error creating email message for {self.company_name}: {e}")
            self.email_message = None

    def attach_file(self, msg, file_path):
        """Attach a file to the email message."""
        try:
            with open(file_path, 'rb') as file:
                filename = os.path.basename(file_path)
                part = MIMEApplication(file.read(), Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)
        except Exception as e:
            print(f"Error attaching file {file_path}: {e}")

    def send_email(self, smtp_server):
        """Send the email using the provided SMTP server."""
        if not self.email_message:
            return False
        try:
            smtp_server.sendmail(EMAIL, [self.recipient_email], self.email_message)
            print(f"Email sent successfully to {self.contact_name} at {self.company_name}")
            return True
        except Exception as e:
            print(f"Failed to send email to {self.contact_name}: {e}")
            return False

def main():
    """Main execution function."""
    smtp_server = None
    emails_sent = 0
    emails_skipped = 0
    try:
        # Load required files
        global MARKETING_TEMPLATE
        # MARKETING_TEMPLATE is now hardcoded above, but you could load from PROMPT_TEMPLATE_PATH if you want to allow editing
        # Load company list
        df = pd.read_csv(COMPANY_LIST_PATH)
        print(f"Successfully loaded {len(df)} companies from CSV")
        # Connect to SMTP server
        print("Connecting to SMTP server...")
        # Amazon WorkMail SMTP settings
        smtp_server = smtplib.SMTP_SSL('smtp.mail.us-east-1.awsapps.com', 465)
        smtp_server.login(EMAIL, APP_PASSWORD)
        print("Successfully connected to email server!")
        # Process each company
        company_list = df.to_dict('records')
        for company in tqdm(company_list, desc="Processing companies", unit="email"):
            if pd.isna(company.get('email')) or pd.isna(company.get('company_name')):
                print(f"Skipping company due to missing required information")
                emails_skipped += 1
                continue
            email_generator = CompanyEmailGenerator(
                contact_name=company.get('contact_name', f"Team at {company['company_name']}"),
                company_name=company['company_name'],
                email=company['email'],
                short_desc=company.get('short_description', ''),
                full_desc=company.get('full_description', ''),
                attachment_path=CV_PDF_PATH
            )
            if email_generator.email_message:
                if email_generator.send_email(smtp_server):
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
        print(f"Total companies processed: {emails_sent + emails_skipped}")

if __name__ == "__main__":
    main()
