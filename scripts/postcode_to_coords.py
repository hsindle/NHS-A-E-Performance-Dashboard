import pandas as pd
import requests
import time

# Load and clean
df = pd.read_csv("data/ae_data_with_postcodes.csv")
df['Postcode'] = df['Postcode'].astype(str).str.strip().str.upper()
unique_postcodes = df['Postcode'].dropna().unique().tolist()

# Split into batches of 100
batches = [unique_postcodes[i:i+100] for i in range(0, len(unique_postcodes), 100)]

postcode_coords = {}

for i, batch in enumerate(batches):
    print(f"🔄 Processing batch {i + 1}/{len(batches)}: {len(batch)} postcodes")
    response = requests.post("https://api.postcodes.io/postcodes", json={"postcodes": batch})

    if response.status_code == 200:
        results = response.json()["result"]
        for result in results:
            query = result["query"]
            if result["result"]:
                lat = result["result"]["latitude"]
                lon = result["result"]["longitude"]
                postcode_coords[query] = (lat, lon)
                print(f"✅ {query} → ({lat}, {lon})")
            else:
                postcode_coords[query] = (None, None)
                print(f"❌ {query} → No result found")
    else:
        print(f"❗ Error on batch {i + 1}: {response.status_code}")
    
    time.sleep(0.2)  # respectful delay

# Map back
df['latitude'] = df['Postcode'].map(lambda pc: postcode_coords.get(pc, (None, None))[0])
df['longitude'] = df['Postcode'].map(lambda pc: postcode_coords.get(pc, (None, None))[1])

# Save
df.to_csv("data/ae_data_with_coords.csv", index=False)
print("✅ Done! Saved to data/ae_data_with_coords.csv")
