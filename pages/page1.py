from navigation import make_sidebar, make_filter
import streamlit as st
from data_processing import finalize_data
import altair as alt
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title='Demography',
    page_icon='🌎',
)

# Guard against direct unauthenticated URL access
if not st.session_state.get('logged_in', False):
    st.warning("Please sign in via the main page.")
    st.switch_page("streamlit_app.py")

make_sidebar()
df_survey25, df_survey24, df_survey23, df_creds = finalize_data()

# ==============================
# FILTER CONFIG
# ==============================
columns_list = [
    'unit', 'subunit', 'directorate', 'division', 'site', 'department', 'section',
    'layer', 'status', 'generation', 'gender', 
    'tenure_category', 'region', 'core'
]

# ==============================
# CATEGORY FUNCTION
# ==============================
def categorize(value):
    if value >= 5:
        return 'High'
    elif value <= 2:
        return 'Low'
    else:
        return None

# ==============================
# MAIN SECTION & UNIT DATA ISOLATION
# ==============================
if st.session_state.get('logged_in', False):
    username = st.session_state['username']
    user_units = df_creds.loc[df_creds['username'] == username, 'unit'].values[0].split(', ')

    # Filter datasets strictly by the user's business unit access
    df_survey25 = df_survey25[df_survey25['subunit'].isin(user_units)]
    df_survey24 = df_survey24[df_survey24['subunit'].isin(user_units)]
    df_survey23 = df_survey23[df_survey23['subunit'].isin(user_units)]

    # Add year column
    df_survey25['year'] = 2025
    df_survey24['year'] = 2024
    df_survey23['year'] = 2023

    # Combine all years
    combined_df = pd.concat([df_survey23, df_survey24, df_survey25], ignore_index=True)

    # Add satisfaction categories
    for d in [df_survey23, df_survey24, df_survey25]:
        d['category_sat'] = d['SAT'].apply(categorize)

    st.header('Demography Overview', divider='rainbow')

    # ==============================
    # SATISFACTION FILTER (PRESERVED COMMENTED BLOCK)
    # ==============================
    #high_satisfaction = st.checkbox("Profil Karyawan Puas (Skor 5)")
    #low_satisfaction = st.checkbox("Profil Karyawan Tidak Puas (Skor 1 dan 2)")

    #if high_satisfaction:
    #    combined_df = combined_df[combined_df['category_sat'] == 'High']
    #    st.subheader('High Satisfaction Demography')
    #elif low_satisfaction:
    #    combined_df = combined_df[combined_df['category_sat'] == 'Low']
    #    st.subheader('Low Satisfaction Demography')
    #else:
    #    st.subheader('All Demography')

    # ==============================
    # FILTER SECTION
    # ==============================
    filtered_data, filtered_combined, selected_filters = make_filter(columns_list, combined_df, combined_df)

    def apply_selected_filters(df, selected_filters):
        if not selected_filters:
            return df.copy()
        filtered = df.copy()
        for col, values in selected_filters.items():
            if not values:
                continue
            if col in filtered.columns:
                filtered = filtered[filtered[col].isin(values)]
        return filtered

    # Apply filters to each year
    df_survey23_filtered = apply_selected_filters(df_survey23, selected_filters)
    df_survey24_filtered = apply_selected_filters(df_survey24, selected_filters)
    df_survey25_filtered = apply_selected_filters(df_survey25, selected_filters)

    #st.write("Selected filters:", selected_filters)
    #st.write("Combined filtered rows:", len(filtered_combined))

    # ==============================
    # 📊 METRICS SECTION
    # ==============================
    st.markdown("#### 📈 Metrics Overview by Year")

    def calc_participants(df, year_label):
        if df.empty:
            return {'year': year_label, 'participants': 0, 'total': 0, 'percentage': 0}
        df = df.copy()
        total = df['nik'].nunique()
        participants = df.loc[df['submit_date'].notna() & (df['submit_date'] != ""), 'nik'].nunique()
        percentage = (participants / total * 100) if total > 0 else 0
        return {
            'year': year_label,
            'participants': participants,
            'total': total,
            'percentage': round(percentage, 1)
        }

    yearly_data = []
    for year, df in [
        ("2023", df_survey23_filtered),
        ("2024", df_survey24_filtered),
        ("2025", df_survey25_filtered)
    ]:
        yearly_data.append(calc_participants(df, year))

    df_yearly = pd.DataFrame(yearly_data)

    st.markdown("###### 🧩 Participation Rate Comparison")

    # --- Color mappings ---
    colors = {
        "Participants": "#1A2B4C",
        "Non-participants": "#EAD8C0"
    }

    # --- Top summary metrics ---
    cols = st.columns(len(df_yearly), gap="large")
    for i, row in enumerate(df_yearly.itertuples()):
        with cols[i]:
            st.markdown(
                f"""
                <div style='text-align:center'>
                    <h5 style='margin-bottom:0'>{row.year}</h5>
                    <h3 style='margin-top:0;color:#1A2B4C'><b>{row.percentage:.1f}%</b></h3>
                    <p style='margin-top:-20px;color:grey'>({int(row.participants):,}/{int(row.total):,})</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- Calculations for non-participants ---
    df_yearly['non_percentage'] = 100 - df_yearly['percentage']
    df_yearly['non_participants'] = df_yearly['total'] - df_yearly['participants']

    # --- Plotly stacked figure (Preserved commented code) ---
    #fig = go.Figure()

    #for label, color in colors.items():
    #    if label == "Participants":
    #        y_values = df_yearly['percentage']
    #        n_values = df_yearly['participants']
    #    else:
    #        y_values = df_yearly['non_percentage']
    #        n_values = df_yearly['non_participants']

    #    fig.add_trace(go.Bar(
    #        x=df_yearly['year'],
    #        y=y_values,
    #        name=label,
    #        text=[f"{v:.1f}% ({int(n):,})" for v, n in zip(y_values, n_values)],
    #        textposition='inside',
    #        marker_color=color
    #    ))

    # --- Layout ---
    #fig.update_layout(
    #    barmode='stack',
    #    yaxis=dict(title="Percentage", range=[0, 100]),
    #    xaxis=dict(title="Year"),
    #    legend=dict(orientation="h", y=-0.2),
    #    height=450,
    #    template="plotly_white"
    #)

    #st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ==============================
    # 🎯 DYNAMIC METRIC BY FILTER (Year-selectable)
    # ==============================
    st.markdown("#### 🎛️ Participation by Selected Attribute")

    column_list = [
        'unit', 'subunit', 'directorate', 'division', 'site', 'department', 'section',
        'layer', 'status', 'generation', 'gender',
        'tenure_category', 'region', 'core'
    ]

    unit_column = st.selectbox("Select the demography by:", column_list)

    # Year selector — default to 2025
    year_options = ["2023", "2024", "2025"]
    selected_year = st.selectbox("Select Year to Display:", year_options, index=year_options.index("2025"))

    # Combine all years
    combined_years = pd.concat([
        df_survey23_filtered.assign(year="2023"),
        df_survey24_filtered.assign(year="2024"),
        df_survey25_filtered.assign(year="2025")
    ], ignore_index=True)

    # Filter by selected year
    df_year_selected = combined_years[combined_years['year'] == selected_year]

    if unit_column in df_year_selected.columns:
        df_filtered = df_year_selected.copy()

        # Compute participation status
        df_filtered['status_participation'] = df_filtered['submit_date'].apply(
            lambda x: 'Done' if pd.notna(x) and x != "" else 'Not Done'
        )

        # Count unique NIKs per unit column and status
        grouped = (
            df_filtered.groupby([unit_column, 'status_participation'])
            .agg(count=('nik', 'nunique'))
            .reset_index()
        )

        # Calculate unit total for percentage calculations
        totals = grouped.groupby(unit_column)['count'].transform('sum')
        grouped['percentage'] = grouped['count'] / totals * 100

        # Pivot table for horizontal stacked bar plot
        pivot_df = grouped.pivot(index=unit_column, columns='status_participation', values='percentage').fillna(0)
        pivot_counts = grouped.pivot(index=unit_column, columns='status_participation', values='count').fillna(0)

        # Ensure required columns exist
        for col in ['Done', 'Not Done']:
            if col not in pivot_df.columns:
                pivot_df[col] = 0
                pivot_counts[col] = 0

        pivot_df = pivot_df.reset_index()
        pivot_counts = pivot_counts.reset_index()

        # Render horizontal stacked bar chart
        fig2 = px.bar(
            pivot_df,
            y=unit_column,
            x=['Done', 'Not Done'],
            barmode='stack',
            orientation='h',
            title=f'Participation Status Distribution by {unit_column.capitalize()} ({selected_year})',
            color_discrete_map={
                'Done': '#1A2B4C',
                'Not Done': '#EAD8C0'
            }
        )

        # Apply labels
        for trace in fig2.data:
            status = trace.name
            trace.customdata = pivot_counts[status]
            trace.texttemplate = '%{x:.1f}%% (%{customdata})'
            trace.textposition = 'inside'

        fig2.update_layout(
            xaxis=dict(title="Percentage (%)", range=[0, 100]),
            yaxis=dict(title=unit_column.capitalize(), categoryorder='total ascending'),
            height=700,
            template="plotly_white",
            legend_title_text="Participation Status",
            bargap=0.2
        )

        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning(f"Column '{unit_column}' not found in data.")