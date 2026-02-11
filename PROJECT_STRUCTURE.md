## Project structure and pipeline

This document explains the layout of the repo and how the PAO Bhangra email pipeline fits together.

### Top-level files

- **`email-company.py`**  
  Core script that sends the PAO Bhangra invitation email.
  - Reads configuration from `.env` (email credentials, sender name, rate limits).
  - Accepts CLI flags for:
    - `--contacts-csv` / `-c`: path to the contacts CSV.
    - `--sent-log` / `-l`: path to the sent-log CSV.
  - Uses a fixed HTML template with:
    - Personalized greeting (`Hello {first_name},`).
    - PAO Bhangra event description.
    - Clickable ticket link and video link.
  - Connects to Gmail over SMTP (`smtp.gmail.com:465`).
  - Tracks already-contacted emails and skips them on future runs.

- **`.env`**  
  Environment variables for runtime configuration:
  - `EMAIL_ADDRESS` – Gmail address used to send emails.
  - `EMAIL_PASSWORD` – Gmail App Password (not your normal password).
  - `SENDER_NAME` – Name used in the From header and signature.
  - `EMAIL_DELAY` – Seconds between consecutive sends.
  - `DAILY_SEND_LIMIT` – Maximum emails to send per run/day.

- **`requirements.txt`**  
  Python dependencies needed by `email-company.py`. Install these into a virtual environment.

- **`.gitignore`**  
  Ignores:
  - `.env`
  - Most data files under `data/` (except the main PAO contacts CSV).
  - Send logs (to avoid leaking recipient data).

- **`README.md`**  
  User-facing, high-level documentation:
  - What the project does.
  - How to install dependencies.
  - How to configure `.env`.
  - How to run test and production campaigns.
  - How to schedule daily runs.

- **`PROJECT_STRUCTURE.md`** (this file)  
  Internal documentation for maintainers and new contributors:
  - Explains repository layout.
  - Describes the pipeline steps end-to-end.

### Data directory

- **`data/`**  
  Default location for contact lists and (optionally) test logs.

  Typical contents:

  - `data/paolist.csv` – Main production contact list.
  - `data/test_paolist.csv` – Small test contact list.
  - `data/pao_sent_log_test.csv` – Example test log (if you choose to store test logs inside `data/`).

  The production sent-log is usually kept at the project root as `pao_sent_log.csv`.

#### Contacts CSV format

- Required:
  - `email` (or `Email`)
- Recommended:
  - `first_name` / `First Name`
  - `last_name` / `Last Name`

The script is flexible with casing and spaces vs. underscores. If `first_name` / `last_name` are missing, you can adapt the CSV or extend the parser logic in `email-company.py`.

### Archive directory

- **`archive/`**  
  Contains older or auxiliary scripts that are not part of the core PAO pipeline but are kept for reference:

  - `archive/clean_csv.py` – Legacy CSV cleaning helper.
  - `archive/producthunt_scraper.py` – Product Hunt scraper for previous cold-email workflows.
  - `archive/make_pao_contacts.py` – Utility to construct a `first_name,last_name,email` CSV from raw data.
  - `archive/fix_tools_json.py`, `archive/tools.json`, `archive/tools_fixed.json` – Legacy tooling/config artifacts.
  - `archive/prompt-template/` – Old prompt template for LLM-generated emails (not used in the PAO pipeline).

These files are safe to ignore for the PAO use case. They are retained only so older experiments and utilities are not lost.

### Pipeline overview

1. **Prepare data**
   - Place your production contact list at something like `data/paolist.csv`.
   - Optionally, create a small `data/test_paolist.csv` for safe testing.

2. **Configure environment**
   - Create `.env` with:
     - Gmail address and App Password.
     - `SENDER_NAME`, `EMAIL_DELAY`, `DAILY_SEND_LIMIT`.

3. **Install dependencies**
   - Create a virtual environment and install from `requirements.txt`.

4. **Run a test campaign**
   - Execute:
     - `python email-company.py --contacts-csv data/test_paolist.csv --sent-log data/pao_sent_log_test.csv`
   - Verify:
     - Emails are received by test recipients.
     - Names and links are correct.
     - `data/pao_sent_log_test.csv` contains the test emails.

5. **Run a production campaign**
   - Execute:
     - `python email-company.py --contacts-csv data/paolist.csv --sent-log pao_sent_log.csv`
   - The script:
     - Skips any addresses already present in `pao_sent_log.csv`.
     - Sends up to `DAILY_SEND_LIMIT` new emails.
     - Appends successfully contacted addresses to `pao_sent_log.csv`.

6. **Automate (optional)**
   - Use a scheduler (like `cron`) to run the production command daily.

### Key invariants and guarantees

- **Idempotency per sent-log**  
  An email address appears at most once in the sent-log file. If the script is re-run with the same `--sent-log`, previously contacted addresses are immediately skipped.

- **Separation of concerns**  
  - `.env` carries only secrets and behavior knobs.
  - CLI flags control which data files are used.
  - Archived scripts do not affect the core pipeline.

- **Safe testing vs. production**  
  You can use:
  - `data/test_paolist.csv` + `data/pao_sent_log_test.csv` for repeated tests.
  - `data/paolist.csv` + `pao_sent_log.csv` for the real campaign.

