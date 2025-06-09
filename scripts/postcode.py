import pandas as pd

# Load both datasets
ae_data = pd.read_csv("data/combined_ae_data.csv")
ods_data = pd.read_csv("data/trust_postcode.csv")

# Rename ODS column to match
ods_data = ods_data.rename(columns={"Organisation Code": "org_code"})

# Merge on org_code
merged_df = ae_data.merge(
    ods_data[["org_code", "Postcode"]],
    on="org_code",
    how="left"
)

# Save merged data
merged_df.to_csv("data/ae_data_with_postcodes.csv", index=False)
print("✅ Saved merged file with postcodes: ae_data_with_postcodes.csv")
