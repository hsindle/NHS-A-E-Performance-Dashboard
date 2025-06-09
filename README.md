#NHS A&E Performance Dashboard#

This project is an interactive data analytics dashboard exploring NHS Accident & Emergency (A&E) performance data across the UK. It is designed to identify trends, highlight performance bottlenecks, and provide actionable insights for health policy, operational efficiency, and public health research.

🔍 Project Overview
Using publicly available NHS datasets, this dashboard tracks:

Monthly A&E attendances by trust

Percentage of patients seen within the 4-hour target

Regional variation in wait time performance

Temporal trends including COVID-19 impacts

(Planned) Demographic breakdowns using Emergency Care Data Set (ECDS)

📁 Project Structure
NHS-A-E-Performance-Dashboard/
│
├── data/                   # CSV data files from NHS England and ECDS
├── scripts/                # Python scripts for cleaning, analysis, plotting
├── dashboard/              # Streamlit app code (to be deployed)
├── README.md               # Project overview (this file)
└── .gitignore              # Excludes data, .env, cache

📊 Tools Used
Python (pandas, matplotlib, seaborn, plotly)

Streamlit for interactive dashboard

NHS England data (A&E wait times, admissions)

(Planned) ECDS for patient demographics and visit types