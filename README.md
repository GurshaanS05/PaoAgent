## PAO Bhangra Email Agent

This repo contains a simple, production-focused email agent that sends a fixed PAO Bhangra invitation email to a list of contacts, once per email address.  
It is designed to:

- **Use a clean, known HTML template** (no LLM generation).
- **Avoid duplicates** by tracking already-contacted emails in a log CSV.
- **Throttle sending** via a daily cap and delay between emails.
- **Be configurable via flags**, so you can easily switch between test and production contact lists.

If you want a deeper explanation of the files and pipeline, see `PROJECT_STRUCTURE.md`.

### Requirements

- **Python**: 3.8+
- **Packages** (installed into a virtual environment):
  - `pandas`
  - `tqdm`
  - `python-dotenv`

### 1. Installation

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment configuration (`.env`)

Create a `.env` file in the project root with:

```env
# Required
EMAIL_ADDRESS=your_gmail_address@gmail.com
EMAIL_PASSWORD=your_gmail_app_password   # NOT your normal password

# Optional
SENDER_NAME=Your Name            # Used in the From header and email signature
EMAIL_DELAY=10                   # Seconds to wait between emails (default: 10)
DAILY_SEND_LIMIT=20              # Max emails to send in one run (default: 100)
```

Notes:

- `EMAIL_PASSWORD` must be a **Gmail App Password** (with 2FA enabled), not your normal account password.
- If you change any of these values, just save `.env` and re-run the script.

### 3. Preparing your data

Place your CSV files under the `data/` directory.

- **Production contacts file** (example):
  - `data/paolist.csv`
- **Test contacts file** (example, included in this repo):
  - `data/test_paolist.csv`

Each CSV should have at least:

- `email` (or `Email`)
- `first_name` / `First Name`
- `last_name` / `Last Name`

Column names are matched case-insensitively and also tolerate spaces vs. underscores (e.g. `first_name` or `First Name`).

### 4. Running the agent

The main script is `email-company.py`. It:

- Loads contacts from a CSV.
- Loads a log of already-contacted emails.
- Sends the PAO Bhangra HTML invitation email via Gmail SMTP.
- Writes newly contacted emails back to a CSV log so they are never emailed twice.

#### 4.1. Test run (recommended first)

Use a small test CSV and a separate log file:

```bash
source .venv/bin/activate
python email-company.py \
  --contacts-csv data/test_paolist.csv \
  --sent-log data/pao_sent_log_test.csv
```

What this does:

- Reads contacts from `data/test_paolist.csv`.
- Reads already-contacted addresses from `data/pao_sent_log_test.csv` (if it exists).
- Sends the PAO email (HTML, with correct name substitution and links).
- Appends newly contacted emails to `data/pao_sent_log_test.csv`.

Run it again with the same flags and no new rows will be sent—the script skips any email already in the sent-log.

#### 4.2. Production run

Once you’re happy with the test:

```bash
source .venv/bin/activate
python email-company.py \
  --contacts-csv data/paolist.csv \
  --sent-log pao_sent_log.csv
```

You can tune behavior via `.env`:

- `DAILY_SEND_LIMIT` to cap how many new contacts get emailed per run.
- `EMAIL_DELAY` to control how quickly emails are sent.

### 5. One-command daily run (`run_pao.sh`)

For everyday usage, you can run a single command from the repo root:

```bash
./run_pao.sh
```

This script:

- Changes into the project directory.
- Activates the `.venv` virtual environment.
- Runs:

```bash
python email-company.py \
  --contacts-csv data/paolist.csv \
  --sent-log pao_sent_log.csv
```

If `.venv` does not exist, it will print simple instructions to create it.

You can still customize or automate further by calling `email-company.py` directly with flags, but `./run_pao.sh` is the preferred “one command per morning” entry point for production use.

### 6. Automating daily runs (optional)

You can schedule a daily run via `cron` (on macOS/Linux).

Edit your crontab:

```bash
crontab -e
```

Add a line like (runs every day at 10:00 AM):

```bash
0 10 * * * cd /path/to/PaoAgent && ./run_pao.sh >> pao_cron.log 2>&1
```

This will:

- Use the same one-command script you run manually.
- Append logs to `pao_cron.log`.

### 7. Safety and guarantees

- **No duplicate emails per log file**: An email address is only sent to once per `--sent-log` file. Re-running with the same log will skip already-contacted addresses.
- **Separate test vs. production**: Use different `--sent-log` values to keep test sends independent from your production campaign.
- **Graceful completion**: If all emails in the contacts CSV are already in the sent-log, the script sends nothing and exits cleanly.