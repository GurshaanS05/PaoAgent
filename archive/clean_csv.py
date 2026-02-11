import pandas as pd
import csv

# Try to read the CSV with different options to handle parsing errors
try:
    # First try with standard pandas
    df = pd.read_csv('ai_companies.csv')
except pd.errors.ParserError:
    try:
        # Try with different quoting options
        df = pd.read_csv('ai_companies.csv', quoting=csv.QUOTE_NONE, escapechar='\\')
    except:
        # If that fails, try reading line by line and filtering
        print("Using manual CSV parsing due to parsing errors...")
        rows = []
        with open('ai_companies.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)  # Get header
            rows.append(header)
            
            for row in reader:
                # Check if any cell contains 'No direct'
                if not any('No direct' in str(cell) for cell in row):
                    rows.append(row)
        
        # Convert back to DataFrame
        df = pd.DataFrame(rows[1:], columns=rows[0])

# Remove rows where any column contains 'No direct' (if using pandas)
if 'df' in locals() and isinstance(df, pd.DataFrame):
    df_cleaned = df[~df.apply(lambda x: x.astype(str).str.contains('No direct', case=False, na=False).any(), axis=1)]
    
    # Save the cleaned data back to the file
    df_cleaned.to_csv('ai_companies.csv', index=False)
    
    print(f"Removed {len(df) - len(df_cleaned)} rows containing 'No direct'")
    print(f"Remaining rows: {len(df_cleaned)}")
else:
    print("CSV cleaning completed using manual parsing") 