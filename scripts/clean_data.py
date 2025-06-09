import pandas as pd
import glob
import os

# Define the folder with your monthly CSVs
DATA_DIR = "./data"
OUTPUT_FILE = "./data/combined_ae_data.csv"

def load_and_combine_csvs():
    # Find all CSVs in the data folder
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    all_dataframes = []
    
    for file in csv_files:
        print(f"Loading {file}...")
        df = pd.read_csv(file)
        df['source_file'] = os.path.basename(file)  # Optional: keep track of origin
        all_dataframes.append(df)
    
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    return combined_df

def clean_columns(df):
    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^\w_]", "", regex=True)
    )
    
    # Convert 'month' to datetime if it exists
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'], errors='coerce')

    return df

def main():
    df_raw = load_and_combine_csvs()
    df_clean = clean_columns(df_raw)
    
    print(f"Saving cleaned data to {OUTPUT_FILE}...")
    df_clean.to_csv(OUTPUT_FILE, index=False)
    print("✔ Done.")

if __name__ == "__main__":
    main()
