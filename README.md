# ColdEmailAIAgent

## Requirements
- Python 3.8+
- openai
- pandas
- tqdm
- python-dotenv

## Setup
1. Install dependencies:
   ```bash
   pip install openai pandas tqdm python-dotenv
   ```
2. Create a `.env` file in the project root with the following variables:
   ```env
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   OPENAI_API_KEY=sk-...
   COMPANY_LIST_PATH=ai_companies.csv
   CV_PDF_PATH=cv/cv.pdf
   CV_TEXT_PATH=cv/cv_extracted.txt
   PROMPT_TEMPLATE_PATH=prompt-template/email-company.txt
   SENDER_NAME=Your Name
   EMAIL_DELAY=5
   OPENAI_MODEL=gpt-3.5-turbo  # Optional, default is gpt-3.5-turbo
   ```
3. Prepare your company CSV and prompt template as described above.

## Usage
Run the script:
```bash
python email-company.py
```