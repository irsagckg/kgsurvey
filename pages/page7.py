import streamlit as st
import math
import pandas as pd
import numpy as np
import plotly.express as px
from navigation import make_sidebar, make_filter
from data_processing import finalize_data

# ==============================
# Page & Sidebar
# ==============================
st.set_page_config(page_title='Gallup Engagement', page_icon=':bar_chart:')
make_sidebar()

# ==============================
# Load & Authenticate
# ==============================
df_survey25, df_survey24, df_survey23, df_creds = finalize_data()

if not st.session_state.get('authentication_status'):
    st.warning("You are not authenticated — please log in to view this page.")
    st.stop()

username = st.session_state['username']
user_units = df_creds.loc[df_creds['username'] == username, 'unit'].values[0].split(', ')

df_survey23 = df_survey23[df_survey23['subunit'].isin(user_units)]
df_survey24 = df_survey24[df_survey24['subunit'].isin(user_units)]
df_survey25 = df_survey25[df_survey25['subunit'].isin(user_units)]

# ==============================
# Header
# ==============================
st.header("🟣 Gallup Engagement Index", divider="rainbow")

# Define Gallup items
gallup_items = [
    "KD1", "KD2", "KI1", "KI2", "KI4", "KI5",
    "KR2", "KR3", "KR4", "KR5", "PR1", "PR2"
]

filter_columns = [
    'unit', 'subunit', 'directorate', 'site', 'division', 'department',
    'section', 'layer', 'work_contract', 'generation', 'gender',
    'tenure_category', 'region', 'core'
]

# ==============================
# Filter Section
# ==============================
combined = pd.concat([df_survey23, df_survey24, df_survey25], ignore_index=True)
selected_filters = make_filter(filter_columns, combined, key_prefix="gallup_filter")

def apply_selected_filters(df, selected_filters):
    if not selected_filters:
        return df
    for col, values in selected_filters.items():
        if values and col in df.columns:
            df = df[df[col].isin(values)]
    return df

df23 = apply_selected_filters(df_survey23, selected_filters)
df24 = apply_selected_filters(df_survey24, selected_filters)
df25 = apply_selected_filters(df_survey25, selected_filters)

# ==============================
# Year Selector
# ==============================
selected_year = st.radio(
    "Select Year:",
    options=[2023, 2024, 2025],
    horizontal=True,
    index=2
)
df_selected = {2023: df23, 2024: df24, 2025: df25}[selected_year].copy()

# ==============================
# Compute Gallup Engagement Category
# ==============================
existing_cols = [c for c in gallup_items if c in df_selected.columns]
if not existing_cols:
    st.error("No Gallup items found in the dataset.")
    st.stop()

df_selected['Gallup_Avg'] = df_selected[existing_cols].mean(axis=1, skipna=True)

def categorize_gallup(score):
    if pd.isna(score):
        return np.nan
    if score <= 2.75:
        return "Actively Disengaged"
    elif score <= 4.24:
        return "Not Engaged"
    else:
        return "Actively Engaged"

df_selected['Engagement Category'] = df_selected['Gallup_Avg'].apply(categorize_gallup)

if df_selected.shape[0] <= 1:
    st.warning("⚠️ Data unavailable to protect confidentiality (N ≤ 1).")
    st.stop()

# ==============================
# Year-Specific Gallup Benchmarks
# ==============================
gallup_benchmark_data = {
    2023: {
        "Global":  {"Actively Disengaged": 18, "Not Engaged": 59, "Actively Engaged": 23},
        "SEA":     {"Actively Disengaged": 6, "Not Engaged": 68, "Actively Engaged": 26}
    },
    2024: {
        "Global":  {"Actively Disengaged": 15, "Not Engaged": 62, "Actively Engaged": 23},
        "SEA":     {"Actively Disengaged": 8, "Not Engaged": 67, "Actively Engaged": 26}
    },
    2025: {
        "Global":  {"Actively Disengaged": 17, "Not Engaged": 62, "Actively Engaged": 21},
        "SEA":     {"Actively Disengaged": 8, "Not Engaged": 67, "Actively Engaged": 26}
    },
}

# ==============================
# Construct Benchmark Table
# ==============================
benchmarks = pd.DataFrame([
    {"Group": f"Global Gallup {selected_year}", **gallup_benchmark_data[selected_year]["Global"]},
    {"Group": f"Southeast Asia {selected_year}", **gallup_benchmark_data[selected_year]["SEA"]},
    {"Group": "KG", "Actively Disengaged": np.nan, "Not Engaged": np.nan, "Actively Engaged": np.nan}
])

# --- KG distribution ---
df_all_raw = {2023: df_survey23, 2024: df_survey24, 2025: df_survey25}[selected_year].copy()
df_all_raw['Gallup_Avg'] = df_all_raw[existing_cols].mean(axis=1, skipna=True)
df_all_raw['Engagement Category'] = df_all_raw['Gallup_Avg'].apply(categorize_gallup)
kg_dist = (
    df_all_raw['Engagement Category']
    .value_counts(normalize=True)
    .reindex(["Actively Disengaged", "Not Engaged", "Actively Engaged"], fill_value=0)
    * 100
)
benchmarks.loc[
    benchmarks['Group'] == "KG",
    ["Actively Disengaged", "Not Engaged", "Actively Engaged"]
] = kg_dist.values

# ==============================
# Helper function
# ==============================
def compute_percentage(df, group_col):
    if not group_col or group_col not in df.columns:
        return pd.DataFrame()
    group_counts = df.groupby([group_col, "Engagement Category"]).size().unstack(fill_value=0)
    group_perc = group_counts.div(group_counts.sum(axis=1), axis=0) * 100
    group_perc = group_perc.reindex(columns=["Actively Disengaged", "Not Engaged", "Actively Engaged"], fill_value=0)
    group_counts = group_counts.reindex(columns=["Actively Disengaged", "Not Engaged", "Actively Engaged"], fill_value=0)
    group_perc.reset_index(inplace=True)
    group_counts.reset_index(inplace=True)
    merged = group_perc.melt(id_vars=[group_col], var_name="Engagement Category", value_name="Percent").merge(
        group_counts.melt(id_vars=[group_col], var_name="Engagement Category", value_name="Count"),
        on=[group_col, "Engagement Category"]
    )
    merged.rename(columns={group_col: "Group"}, inplace=True)
    return merged

# ==============================
# SECTION 1 — Overall Comparison
# ==============================
st.subheader("🌍 Overall Comparison", divider="gray")

bench_list = []

# Compute real N for KG
kg_counts = (
    df_all_raw['Engagement Category']
    .value_counts()
    .reindex(["Actively Disengaged", "Not Engaged", "Actively Engaged"], fill_value=0)
)

bench_list = []
for _, row in benchmarks.iterrows():
    for cat in ["Actively Disengaged", "Not Engaged", "Actively Engaged"]:
        if row["Group"] == "KG":
            # use KG’s real N
            count_val = int(kg_counts.get(cat, 0))
        else:
            # benchmarks (Global / SEA) don’t have N
            count_val = np.nan
        bench_list.append({
            "Group": row["Group"],
            "Engagement Category": cat,
            "Percent": row[cat],
            "Count": count_val
        })

bench_df = pd.DataFrame(bench_list)

kg_melted = compute_percentage(df_all_raw, "unit") if "unit" in df_all_raw.columns else pd.DataFrame()
comparison_df1 = pd.concat([bench_df, kg_melted], ignore_index=True)

order1 = [f"Global Gallup {selected_year}", f"Southeast Asia {selected_year}", "KG"]
if "unit" in df_selected.columns:
    order1 += sorted(df_selected["unit"].dropna().unique().tolist())
comparison_df1["Group"] = pd.Categorical(comparison_df1["Group"], categories=order1, ordered=True)

def format_label(row):
    # Safely coerce Group to string (handle NaN/None)
    group = "" if pd.isna(row.get("Group")) else str(row.get("Group"))

    # Safely read percent and count (handle NaN)
    percent = row.get("Percent")
    count = row.get("Count")

    # If percent is missing, return empty label
    if percent is None or (isinstance(percent, float) and math.isnan(percent)):
        return ""

    pct_str = f"{int(round(percent))}%"

    # If it's a Gallup benchmark (global / SEA) show only percentage
    if any(substr in group for substr in ["Global Gallup", "Southeast Asia"]):
        return pct_str

    # For company/unit rows, show percentage (N) if Count available and numeric
    if count is not None and not (isinstance(count, float) and math.isnan(count)):
        try:
            cnt = int(round(float(count)))
            return f"{pct_str} ({cnt})"
        except Exception:
            # fallback if count cannot be coerced to int
            return pct_str

    # fallback: just percentage
    return pct_str

comparison_df1["Label"] = comparison_df1.apply(format_label, axis=1)

fig1 = px.bar(
    comparison_df1,
    x="Percent",
    y="Group",
    color="Engagement Category",
    text="Label",
    orientation="h",
    color_discrete_map={
        "Actively Disengaged": "#e74c3c",
        "Not Engaged": "#f1c40f",
        "Actively Engaged": "#2ecc71"
    },
)
fig1.update_layout(
    barmode="stack",
    xaxis=dict(title="%", range=[0, 100]),
    yaxis_title=None,
    legend_title=None,
    height=600,
)
fig1.update_traces(textposition="inside", insidetextanchor="middle")
st.plotly_chart(fig1, use_container_width=True)

# ==============================
# SECTION 1 — Comparison Table (vs Indonesia Benchmark & Last Year)
# ==============================
st.caption("📈 Table: Unit-level comparison vs Indonesia benchmark and last year")

indonesia_benchmark_data = {2023: 24, 2024: 26, 2025: 27}
ind_benchmark = indonesia_benchmark_data.get(selected_year, np.nan)

def get_engaged_percentage(df):
    if df.empty:
        return np.nan
    df = df.copy()
    df["Gallup_Avg"] = df[existing_cols].mean(axis=1, skipna=True)
    df["Engagement Category"] = df["Gallup_Avg"].apply(categorize_gallup)
    return (df["Engagement Category"].value_counts(normalize=True).get("Actively Engaged", 0)) * 100

# --- Previous year reference ---
if selected_year > 2023:
    prev_year_df = {2024: df_survey23, 2025: df_survey24}.get(selected_year, pd.DataFrame())
else:
    prev_year_df = pd.DataFrame()

section1_table = []

# KG overall
kg_engaged = get_engaged_percentage(df_all_raw)
prev_kg = get_engaged_percentage(prev_year_df) if not prev_year_df.empty else np.nan

section1_table.append({
    "Group": "KG (Overall)",
    "Actively Engaged (%)": kg_engaged,
    "Indonesia Benchmark (%)": ind_benchmark,
    "Δ vs Last Year": round(kg_engaged - prev_kg, 1) if not np.isnan(prev_kg) else "—",
    "Status": "✅ Above ID" if kg_engaged >= ind_benchmark else "❌ Below ID"
})

# 🔹 Breakdown by unit (lowercase)
if "unit" in df_selected.columns:
    for unit in sorted(df_selected["unit"].dropna().unique()):
        curr_df = df_selected[df_selected["unit"] == unit]
        curr_engaged = get_engaged_percentage(curr_df)

        if not prev_year_df.empty:
            prev_df_unit = prev_year_df[prev_year_df["unit"] == unit]
            prev_engaged = get_engaged_percentage(prev_df_unit) if not prev_df_unit.empty else np.nan
        else:
            prev_engaged = np.nan

        delta = round(curr_engaged - prev_engaged, 1) if not np.isnan(prev_engaged) else "—"
        status = "✅ Above ID" if curr_engaged >= ind_benchmark else "❌ Below ID"

        section1_table.append({
            "Group": unit,
            "Actively Engaged (%)": curr_engaged,
            "Indonesia Benchmark (%)": ind_benchmark,
            "Δ vs Last Year": delta,
            "Status": status
        })

section1_table = pd.DataFrame(section1_table)

def safe_format(val, fmt):
    if isinstance(val, (int, float, np.floating)) and not np.isnan(val):
        return fmt.format(val)
    return val

formatted_df1 = section1_table.copy()
formatted_df1["Actively Engaged (%)"] = formatted_df1["Actively Engaged (%)"].apply(lambda v: safe_format(v, "{:.1f}%"))
formatted_df1["Indonesia Benchmark (%)"] = formatted_df1["Indonesia Benchmark (%)"].apply(lambda v: safe_format(v, "{:.1f}%"))
formatted_df1["Δ vs Last Year"] = formatted_df1["Δ vs Last Year"].apply(
    lambda v: safe_format(v, "{:+.1f}%") if isinstance(v, (int, float, np.floating)) else v
)

st.dataframe(
    formatted_df1.style.map(
        lambda v: "color: green;" if isinstance(v, str) and "✅" in v else
                  ("color: red;" if isinstance(v, str) and "❌" in v else None),
        subset=["Status"]
    ),
    use_container_width=True
)

# ==============================
# SECTION 2 — Detailed Breakdown
# ==============================
breakdown_var = st.selectbox(
    "🔍 Breakdown by (choose variable):",
    options=[None] + filter_columns,
    index=filter_columns.index("subunit") + 1 if "subunit" in filter_columns else 0
)
st.subheader("🏢 Detailed Breakdown", divider="gray")

if breakdown_var and breakdown_var in df_selected.columns:
    section2 = compute_percentage(df_selected, breakdown_var)
    if section2.empty:
        st.info("No data available for this breakdown.")
    else:
        section2["Label"] = section2.apply(lambda r: f"{int(round(r['Percent']))}% ({int(r['Count'])})", axis=1)
        order2 = sorted(df_selected[breakdown_var].dropna().unique().tolist())
        section2["Group"] = pd.Categorical(section2["Group"], categories=order2, ordered=True)

        fig2 = px.bar(
            section2,
            x="Percent",
            y="Group",
            color="Engagement Category",
            text="Label",
            orientation="h",
            color_discrete_map={
                "Actively Disengaged": "#e74c3c",
                "Not Engaged": "#f1c40f",
                "Actively Engaged": "#2ecc71"
            },
        )
        fig2.update_layout(
            barmode="stack",
            xaxis=dict(title="%", range=[0, 100]),
            yaxis_title=None,
            legend_title=None,
            height=600,
        )
        fig2.update_traces(textposition="inside", insidetextanchor="middle")
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Select a breakdown variable above to show the detailed section.")

# ==============================
# SECTION 2 — Breakdown Table (Same Format as Section 1)
# ==============================
st.caption("📈 Table: Breakdown vs Indonesia benchmark and last year")

if breakdown_var and breakdown_var in df_selected.columns:
    section2_table = []

    # --- Indonesia benchmark (current year)
    ind_benchmark = indonesia_benchmark_data.get(selected_year, np.nan)

    # --- Previous year data
    if selected_year > 2023:
        prev_df = {2024: df_survey23, 2025: df_survey24}[selected_year]
    else:
        prev_df = pd.DataFrame()

    # --- For each group in breakdown variable
    for grp in sorted(df_selected[breakdown_var].dropna().unique()):
        curr_grp_df = df_selected[df_selected[breakdown_var] == grp]
        curr_engaged = get_engaged_percentage(curr_grp_df)

        # Compare with last year’s same group
        if not prev_df.empty:
            prev_grp_df = prev_df[prev_df[breakdown_var] == grp]
            prev_engaged = get_engaged_percentage(prev_grp_df) if not prev_grp_df.empty else np.nan
        else:
            prev_engaged = np.nan

        delta = (
            round(curr_engaged - prev_engaged, 1)
            if not np.isnan(prev_engaged)
            else "—"
        )
        status = "✅ Above ID" if curr_engaged >= ind_benchmark else "❌ Below ID"

        section2_table.append({
            "Group": grp,
            "Actively Engaged (%)": curr_engaged,
            "Indonesia Benchmark (%)": ind_benchmark,
            "Δ vs Last Year": delta,
            "Status": status
        })

    section2_table = pd.DataFrame(section2_table)

    # --- Safe numeric formatting ---
    def safe_format(val, fmt):
        if isinstance(val, (int, float, np.floating)) and not np.isnan(val):
            return fmt.format(val)
        return val

    formatted_df = section2_table.copy()
    formatted_df["Actively Engaged (%)"] = formatted_df["Actively Engaged (%)"].apply(lambda v: safe_format(v, "{:.1f}%"))
    formatted_df["Indonesia Benchmark (%)"] = formatted_df["Indonesia Benchmark (%)"].apply(lambda v: safe_format(v, "{:.1f}%"))
    formatted_df["Δ vs Last Year"] = formatted_df["Δ vs Last Year"].apply(
        lambda v: safe_format(v, "{:+.1f}%") if isinstance(v, (int, float, np.floating)) else v
    )

    # --- Display styled table ---
    st.dataframe(
        formatted_df.style.map(
            lambda v: "color: green;" if isinstance(v, str) and "✅" in v else
                      ("color: red;" if isinstance(v, str) and "❌" in v else None),
            subset=["Status"]
        ),
        use_container_width=True
    )
else:
    st.info("Select a breakdown variable above to display its comparison table.")
