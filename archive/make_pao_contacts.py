"""
Create pao_contacts.csv with only first_name, last_name, email.
Reads an existing company/contact CSV and outputs the three-column format
expected by email-company.py for PAO Bhangra invitations.
"""
import pandas as pd
import os

# Default: read from env or use a project CSV under data/
INPUT_CSV = os.getenv("INPUT_CSV", "data/newYork_companies_emails.csv")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "data/pao_contacts.csv")

# Column names if the input has no header (company_name, contact_name, email, ...)
NO_HEADER_NAMES = ["company_name", "contact_name", "email", "short_description", "full_description"]


def main():
    path = INPUT_CSV
    if not os.path.isfile(path):
        # Create an empty CSV with correct headers if no input exists
        out = pd.DataFrame(columns=["first_name", "last_name", "email"])
        out.to_csv(OUTPUT_CSV, index=False)
        print(f"No input file found. Created empty {OUTPUT_CSV} with headers: first_name, last_name, email")
        return

    # Try with header row first
    df_header = pd.read_csv(path, nrows=1)
    has_header = "email" in df_header.columns and ("contact_name" in df_header.columns or "first_name" in df_header.columns or "first name" in df_header.columns)

    if has_header:
        df = pd.read_csv(path)
        cols_lower = {str(c).lower().replace(" ", "_"): c for c in df.columns}
        rename = {}
        if "contact_name" in cols_lower:
            rename[cols_lower["contact_name"]] = "contact_name"
        if "email" in cols_lower:
            rename[cols_lower["email"]] = "email"
        if "first_name" in cols_lower:
            rename[cols_lower["first_name"]] = "first_name"
        if "last_name" in cols_lower:
            rename[cols_lower["last_name"]] = "last_name"
        if rename:
            df = df.rename(columns=rename)
    else:
        # No header: assume company_name, contact_name, email, short_description, full_description
        df = pd.read_csv(path, header=None, names=NO_HEADER_NAMES)

    # Prefer explicit first_name / last_name if present
    first_col = "first_name" if "first_name" in df.columns else ("first name" if "first name" in df.columns else None)
    last_col = "last_name" if "last_name" in df.columns else ("last name" if "last name" in df.columns else None)
    email_col = "email" if "email" in df.columns else None
    contact_col = "contact_name" if "contact_name" in df.columns else ("contact name" if "contact name" in df.columns else None)

    if first_col and last_col and email_col:
        out = df[[first_col, last_col, email_col]].copy()
        out.columns = ["first_name", "last_name", "email"]
    else:
        # Build first_name, last_name from contact_name
        contact = df[contact_col or "contact_name"].astype(str)
        email = df[email_col or "email"].astype(str)
        first_names = []
        last_names = []
        for c in contact:
            parts = (c or "").strip().split(None, 1)
            first_names.append(parts[0] if parts else "")
            last_names.append(parts[1] if len(parts) > 1 else "")
        out = pd.DataFrame({
            "first_name": first_names,
            "last_name": last_names,
            "email": email
        })

    out = out.dropna(subset=["email"])
    out["email"] = out["email"].astype(str).str.strip()
    out = out[out["email"].str.contains("@", na=False)]
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {len(out)} rows to {OUTPUT_CSV} (first_name, last_name, email)")


if __name__ == "__main__":
    main()
