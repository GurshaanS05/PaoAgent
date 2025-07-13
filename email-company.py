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
COMPANY_LIST_PATH = os.getenv("COMPANY_LIST_PATH", "test_companies.csv")
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
MARKETING_TEMPLATE = '''
TL;DR: We help people discover tools like {company_name} through our growing platform (25,000+ searches so far). You can list your product for free or boost visibility with paid promotions (10% off with code TOOL10). Add your tool here: https://toolforthat.io/submit. Check out our premium plans here: https://Toolforthat.io/pricing.

Hey {company_name}!

My name is Sachin and I am one of the founders of https://toolforthat.io.

We are a platform where users can search for things they are building, creating or just need help with and our search engine indexes the best tools available. We are dropping a completely new update to our website. We launched back in January, where we have had over 25,000 searches on our platform. This new revamp should take us to a whole new level. 

One of our most popular requests is "{short_desc}," so we know that {company_name} is perfect for our site. We're excited to help you grow your visibility on our platform and boost your user count even more. You can add more information about your product, for FREE, here: https://toolforthat.io/submit

If you're interested in being the #1 tool on our site, we'd love to connect. Check out our different plans at https://Toolforthat.io/pricing. We'd  to offer you a discount of 10% on your first promotion with discount code TOOL10!

If anything above interests you, please feel free to respond to this email (or book a time on calendly), and we can set up a time to chat.

Looking forward to hearing from you!

Best,

Sachin @ Toolforthat.io
https://calendly.com/sachin-toolforthat


--If you want to stop receiving these emails, please reply with "STOP" in the subject line.
'''


class CompanyEmailGenerator:
    """Email generator for Toolforthat marketing outreach."""

    def __init__(self, contact_name, company_name, email, short_desc, full_desc, attachment_path=None):
        self.contact_name = contact_name
        self.company_name = company_name
        self.recipient_email = email.strip()
        self.short_desc = short_desc
        self.full_desc = full_desc
        self.attachment_path = attachment_path
        self.email_message = None

        # Generate personalized email content
        personalized_content = self.generate_personalized_email()
        if not personalized_content:
            print(f"Failed to generate personalized email for {company_name}")
            return

        # Create email message
        self.create_email_message(personalized_content)

    def generate_personalized_email(self):
        """Generate a personalized email content using the company's full description."""
        try:
            prompt = (
                f"Create a personalized email for {self.company_name} that follows this exact structure and tone. "
                f"Use the following information about the company:\n"
                f"Company: {self.company_name}\n"
                f"Short Description: {self.short_desc}\n"
                f"Full Description: {self.full_desc}\n\n"
                f"Email Structure:\n"
                f"1. Start with 'Hey [Company Name]!'\n"
                f"2. Write a personal story: 'I recently used your [website/app/platform], and firstly I fell in love with the [specific feature]. It really helped me [what the tool solves in a casual, personal way]. I had tons of friends also face similar issues.'\n"
                f"3. Continue the story: 'I kept getting asked by friends about the tools I use, so I decided to create a curated list to share with others.'\n"
                f"4. Connect to your platform: 'Inspired by this, I spent the past few weeks building toolforthat.io. In short terms, its a directory with an enhanced search feature to help people find the best tools for their use cases.'\n"
                f"5. Explain the value: 'I genuinely think that exploring something like this would give [Company Name] so much visibility and introduce you guys to a whole new audience.'\n"
                f"6. Share milestone: 'Recently toolforthat has just surpassed over 25,000 searches, and that just being within a few weeks is mind blowing to us. It really showed us how many people are looking for the perfect tech tools.'\n"
                f"7. Make the ask: 'Absolutely no pressure at all, I know your busy working on your amazing [website/app/platform], but I'd love to sit down and have a quick chat with you to get some insight into your audience, and how we can collaborate together!'\n"
                f"8. Call to action: 'If you're open to it, feel free to reply or grab a time on my calendar to chat: https://calendly.com/sachin-toolforthat'\n"
                f"9. End with 'Big fan of what you're building!'\n"
                f"10. Close with 'Best, Sachin'\n"
                f"11. Keep the personal, authentic tone throughout - like you're genuinely sharing your story\n"
                f"12. Make it feel like you actually used their product and were inspired by it\n"
                f"13. When describing how the tool helped you, use casual, personal language but feel free to use business terms like 'game-changer' - just keep it conversational\n\n"
                f"Write the email body only (no subject line)."
            )
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are Sachin, co-founder of ToolForThat.io, writing personal, story-driven outreach emails. Write like you're genuinely sharing your personal experience with their product and how it inspired you to build your platform. Be authentic, personal, and conversational. When describing how a tool helped you, use casual, everyday language but feel free to include business terms like 'game-changer' to add impact."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.8
            )
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            print(f"Error generating personalized email for {self.company_name}: {e}")
            return None

    def create_email_message(self, personalized_content):
        """Create the complete marketing email message with personalized content and attachments."""
        try:
            # Only proceed if we have personalized content
            if not personalized_content:
                print(f"No personalized content generated for {self.company_name}, skipping email")
                self.email_message = None
                return
                
            subject = f"Hello {self.company_name}!"
            
            # Use the personalized content from ChatGPT
            body = personalized_content
            
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
