import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from geopy.distance import geodesic
from fuzzywuzzy import process



# Page setup
st.set_page_config(page_title="NHS A&E Dashboard", layout="wide")

# Load cleaned data
@st.cache_data
def load_data():
    import pandas as pd

    # Load raw CSV
    df = pd.read_csv("data/ae_data_with_coords.csv")

    # Clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^\w_]", "", regex=True)
    )

    # Rename and clean 'month' column
    df = df.rename(columns={"period": "month"})

    # Convert 'MSitAE-APRIL-2023' -> 'April-2023' -> datetime
    df["month"] = (
        df["month"]
        .str.replace("MSitAE-", "", regex=False)
        .str.title()
    )
    df["month"] = pd.to_datetime(df["month"], format="%B-%Y", errors="coerce")


    # Drop empty/unnamed columns
    df = df.loc[:, ~df.columns.str.contains("unnamed")]

    # Create summary metrics
    df["total_attendances"] = (
        df["ae_attendances_type_1"].fillna(0) +
        df["ae_attendances_type_2"].fillna(0) +
        df["ae_attendances_other_ae_department"].fillna(0)
    )

    df["attendances_over_4hrs"] = (
        df["attendances_over_4hrs_type_1"].fillna(0) +
        df["attendances_over_4hrs_type_2"].fillna(0) +
        df["attendances_over_4hrs_other_department"].fillna(0) +
        df["attendances_over_4hrs_booked_appointments_type_1"].fillna(0) +
        df["attendances_over_4hrs_booked_appointments_type_2"].fillna(0) +
        df["attendances_over_4hrs_booked_appointments_other_department"].fillna(0)
    )


    df["pct_seen_within_4hrs"] = 100 * (
        1 - df["attendances_over_4hrs"] / df["total_attendances"]
    )

    return df



df = load_data()

# Header
st.title("📊 NHS A&E Performance Dashboard")
st.markdown("Tracking attendances and wait times across NHS Trusts in England - April 2023 to April 2025")



# KPI summary
col1, col2 = st.columns(2)

with col1:
    total = int(df["total_attendances"].sum())
    st.metric("Total Attendances", f"{total:,}")

with col2:
    avg_pct = df["pct_seen_within_4hrs"].mean()
    st.metric("% Seen Within 4 Hours (Avg)", f"{avg_pct:.1f} %")

# Monthly trend chart
monthly = df.groupby("month")[["total_attendances", "attendances_over_4hrs"]].sum().reset_index()
monthly["pct_seen_within_4hrs"] = 100 * (1 - monthly["attendances_over_4hrs"] / monthly["total_attendances"])

st.subheader("📅 Monthly A&E Attendance Trend")

fig1 = px.line(monthly, x="month", y="total_attendances", title="Total Attendances Over Time")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.line(monthly, x="month", y="pct_seen_within_4hrs", title="% Seen Within 4 Hours")
fig2.add_hline(y=95, line_dash="dash", annotation_text="Target (95%)", annotation_position="bottom right")
st.plotly_chart(fig2, use_container_width=True)



st.subheader("🏥 Trust-Level Performance Comparison")

# Step 1: Month selector
available_months = df['month'].dropna().sort_values().dt.strftime("%B %Y").unique()
selected_month_str = st.selectbox("Select a month to compare trusts", available_months)
selected_month = pd.to_datetime(selected_month_str, format="%B %Y")


# Step 2: Filter + numeric check
month_df = df[df['month'] == selected_month].copy()
for col in ['total_attendances', 'attendances_over_4hrs']:
    month_df[col] = pd.to_numeric(month_df[col], errors='coerce')
month_df = month_df[month_df['total_attendances'] > 0]

# Step 3: Calculate % seen within 4 hours
month_df['pct_seen_within_4hrs'] = (
    100 * (1 - month_df['attendances_over_4hrs'] / month_df['total_attendances'])
).round(2)


# Step 4: Separate perfect performers (100%)
perfect_df = month_df[month_df['pct_seen_within_4hrs'] == 100].copy()
perfect_trusts = perfect_df['org_name'].unique().tolist()


# Step 5: Top 10 (excluding 100%) — but ensure bottom stays in
top_pool = month_df[month_df['pct_seen_within_4hrs'] < 95]
top_10_df = top_pool.sort_values('pct_seen_within_4hrs', ascending=False).head(10)


# Step 6: Display NHS 4-hour target achievers
target_df = month_df[month_df['pct_seen_within_4hrs'] >= 95].copy()

st.markdown("✅ **Trusts Meeting or Exceeding the 95% NHS 4-Hour A&E Target**")
st.markdown(
    "_The NHS's four-hour A&E target is a standard that aims for **at least 95%** of patients attending Accident and Emergency (A&E) to be admitted, transferred, or discharged within four hours of arrival._"
)

if not target_df.empty:
    st.dataframe(
        target_df[['org_name', 'total_attendances', 'pct_seen_within_4hrs']]
        .sort_values('pct_seen_within_4hrs', ascending=False)
        .rename(columns={
            'org_name': 'Trust',
            'total_attendances': 'Attendances',
            'pct_seen_within_4hrs': '% Seen <4hrs'
        })
        .reset_index(drop=True), #Removes ID from table.
        use_container_width=True
    )
else:
    st.info("No trusts met or exceeded the 95% target for this month.")

#Plot Top 10 (excluding 95% achievers)

fig_top = px.bar(
    top_10_df,
    x='pct_seen_within_4hrs',
    y='org_name',
    orientation='h',
    title='Top 10 Trusts Below 100% Seen Within 4 Hours',
    labels={'pct_seen_within_4hrs': '% Seen <4hrs', 'org_name': 'Trust'}
)
fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
fig_top.update_traces(texttemplate='%{x:.1f}%', textposition='outside')
st.plotly_chart(fig_top, use_container_width=True)

st.markdown("🚨 **Bottom 10 Performing Trusts**")

# Filter for trusts with valid data and non-zero attendances
valid_df = month_df[month_df['total_attendances'] > 0].copy()
bottom_10_df = valid_df.sort_values('pct_seen_within_4hrs').head(10)


fig_bottom = px.bar(
    bottom_10_df,
    x='pct_seen_within_4hrs',
    y='org_name',
    orientation='h',
    title='Bottom 10 Trusts by % Seen Within 4 Hours',
    labels={'pct_seen_within_4hrs': '% Seen <4hrs', 'org_name': 'Trust'}
)
fig_bottom.update_layout(yaxis={'categoryorder': 'total ascending'})
fig_bottom.update_traces(texttemplate='%{x:.1f}%', textposition='outside')

st.plotly_chart(fig_bottom, use_container_width=True)

st.subheader("📈 Trust Performance Over Time")

# Step 1: Dropdown to select trust
trust_list = df['org_name'].dropna().sort_values().unique()
selected_trust = None
postcode_input = st.text_input("📮 Enter aa postcode to find the nearest NHS trust")

def get_coordinates_from_postcode(postcode):
    try:
        response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
        if response.status_code == 200:
            data = response.json()
            return data["result"]["latitude"], data["result"]["longitude"]
    except:
        pass
    return None, None

# If postcode entered, use it to find nearest trust
if postcode_input:
    user_lat, user_lon = get_coordinates_from_postcode(postcode_input.strip())

    if user_lat and user_lon:
        trust_locs = df[df['latitude'].notna() & (df['total_attendances'] > 0)].copy()
        trust_locs['distance_km'] = trust_locs.apply(
            lambda row: geodesic((user_lat, user_lon), (row['latitude'], row['longitude'])).km,
            axis=1
        )

        nearest = trust_locs.sort_values('distance_km').iloc[0]
        selected_trust = nearest['org_name']
        st.success(f"🔍 Nearest Trust: {selected_trust} ({nearest['distance_km']:.1f} km away)")
    else:
        st.error("❌ Invalid postcode. Please check and try again.")

# Step 2: Dropdown — default to nearest if available
selected_trust = st.selectbox(
    "Alternatively, select a trust manually:",
    trust_list,
    index=trust_list.tolist().index(selected_trust) if selected_trust in trust_list else 0
)

# Optional: notify if override
if postcode_input and 'nearest' in locals():
    if selected_trust != nearest['org_name']:
        st.info("📭 Manual trust selected — postcode input is now ignored.")


# Step 3: Filter the data for the selected trust
trust_df = df[df['org_name'] == selected_trust].copy()

# Step 4: Ensure numeric + calculate %
for col in ['attendances_over_4hrs', 'total_attendances']:
    trust_df[col] = pd.to_numeric(trust_df[col], errors='coerce')

trust_df = trust_df[trust_df['total_attendances'] > 0]
trust_df['pct_seen_within_4hrs'] = (
    100 * (1 - trust_df['attendances_over_4hrs'] / trust_df['total_attendances'])
)
trust_df = trust_df.sort_values('month')

# Step 5: Plot with Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=trust_df['month'],
    y=trust_df['pct_seen_within_4hrs'],
    mode='lines+markers',
    name='% Seen <4hrs'
))

fig.add_hline(y=95, line_dash="dot", line_color="red", 
              annotation_text="NHS Target (95%)", 
              annotation_position="top right")

fig.update_layout(
    title=f"A&E Performance for {selected_trust}",
    xaxis_title="Month",
    yaxis_title="% Seen Within 4 Hours",
    yaxis=dict(range=[0, 100]),
    height=500
)

st.plotly_chart(fig, use_container_width=True)



st.subheader("🗺️ Trust Performance Map")

# 🎯 Step 1: Dropdown for selecting month
month_options = df['month'].dropna().sort_values(ascending=False).dt.strftime('%B %Y').unique()
selected_month_str = st.selectbox("Select month to view", options=month_options)

# Convert string back to datetime
selected_month = pd.to_datetime(selected_month_str)

# 🎯 Step 2: Filter data for selected month
map_df = df[df['month'] == selected_month].copy()

# 🎯 Step 3: Filter to England + Wales using coordinates
map_df = map_df[
    (map_df['latitude'].notna()) &
    (map_df['longitude'].notna()) &
    (map_df['latitude'] >= 49.9) &   # Southern England
    (map_df['latitude'] <= 55.8) &   # Northern England / mid-Wales
    (map_df['longitude'] >= -6.0) &  # West Wales
    (map_df['longitude'] <= 2.0)     # East England
]

# 🎯 Step 4: Calculate % seen within 4hrs
map_df['pct_seen_within_4hrs'] = (
    100 * (1 - map_df['attendances_over_4hrs'] / map_df['total_attendances'])
)

# 🎯 Step 5: Create the map
fig_map = px.scatter_mapbox(
    map_df,
    lat='latitude',
    lon='longitude',
    color='pct_seen_within_4hrs',
    size='total_attendances',
    hover_name='org_name',
    hover_data={
        'pct_seen_within_4hrs': ':.2f',
        'total_attendances': True,
        'month': False,
        'latitude': False,
        'longitude': False
    },
    color_continuous_scale='RdYlGn',
    zoom=5.5,
    height=600
)

# 🎯 Step 6: Style the map — centered on UK
fig_map.update_layout(
    mapbox_style='carto-darkmatter',
    mapbox_center={"lat": 53.0, "lon": -2.5},  # Approx center of England & Wales
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

# 🎯 Step 7: Render in Streamlit
st.plotly_chart(fig_map, use_container_width=True)
