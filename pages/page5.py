from navigation import make_sidebar, make_filter
import streamlit as st
from data_processing import finalize_data
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title='Categorization', page_icon=':🤝:')
make_sidebar()
df_survey25, df_survey24, df_survey23, df_creds = finalize_data()

# Columns for potential filtering and categorization
columns_list = [
    'unit', 'subunit', 'directorate', 'division', 'department', 'section',
    'layer', 'status', 'generation', 'gender', 'marital', 'education',
    'tenure_category', 'children', 'region', 'participation_23', 'core'
]

# Define function to categorize satisfaction, likelihood to stay, and NPS
def categorize(value):
    if value >= 4:
        return 'High'
    elif value <= 2:
        return 'Low'
    else:
        return 'Medium'

def categorize_NPS(value):
    if value >= 9:
        return 'Promoter'
    elif value <= 6:
        return 'Detractor'
    else:
        return 'Passive'

# Extract the logged-in user's unit after authentication
if st.session_state.get('authentication_status'):
    # Retrieve the username from session state
    username = st.session_state['username']

    # Get the user's units from the credentials and split by commas
    user_units = df_creds.loc[df_creds['username'] == username, 'unit'].values[0].split(', ')
    
    # Filter the survey data by the user's units (checking if unit is in user's units)
    df_survey25 = df_survey25[df_survey25['subunit'].isin(user_units)]
    df_survey24 = df_survey24[df_survey24['subunit'].isin(user_units)]
    df_survey23 = df_survey23[df_survey23['subunit'].isin(user_units)]

    # Apply categorization to the relevant columns
    df_survey25['category_sat'] = df_survey25['SAT'].apply(categorize)
    df_survey25['category_ke1'] = df_survey25['KE1'].apply(categorize)
    df_survey25['category_nps'] = df_survey25['NPS'].apply(categorize_NPS)
    df_survey24['category_sat'] = df_survey24['SAT'].apply(categorize)
    df_survey24['category_ke1'] = df_survey24['KE1'].apply(categorize)
    df_survey24['category_nps'] = df_survey24['NPS'].apply(categorize_NPS)
    df_survey23['category_sat'] = df_survey23['SAT'].apply(categorize)
    df_survey23['category_ke1'] = df_survey23['KE1'].apply(categorize)
    df_survey23['category_nps'] = df_survey23['NPS'].apply(categorize_NPS)

    st.header('Employee Categorization', divider='rainbow')

    # Create combined categories based on user selection
    combine_with_nps = st.checkbox("Uncheck for Satisfaction X Likelihood to Stay; Check for Satisfaction X NPS")

    # --- Year selection ---
    year_options = ["2025", "2024", "2023"]
    selected_year = st.selectbox("Select Year", year_options)

    if selected_year == "2025":
        df_survey = df_survey25.copy()
    elif selected_year == "2024":
        df_survey = df_survey24.copy()
    else:
        df_survey = df_survey23.copy()

    # ✅ Only include employees who answered KE1 or NPS
    df_survey = df_survey[(~df_survey['KE1'].isna()) | (~df_survey['NPS'].isna())]

    if combine_with_nps:
        df_survey['combined_category'] = df_survey.apply(
            lambda row: f"{row['category_sat']} Satisfaction - {row['category_nps']}",
            axis=1
        )
        st.subheader('Satisfaction and NPS Analysis', divider='gray')
    else:
        df_survey['combined_category'] = df_survey.apply(
            lambda row: f"{row['category_sat']} Satisfaction - {row['category_ke1']} Likelihood to Stay",
            axis=1
        )
        st.subheader('Satisfaction and Likelihood to Stay Analysis', divider='gray')

    # SECTION - HEATMAP

   # ==============================
    # FILTER SECTION
    # ==============================

    # Call the filter function
    selected_filters = make_filter(columns_list, df_survey, key_prefix="filter")  # returns dict

    # Apply the selected filters to df_survey
    filtered_data = df_survey.copy()
    for col, selected_values in selected_filters.items():
        if selected_values:  # only filter if user selected something
            filtered_data = filtered_data[filtered_data[col].isin(selected_values)]

    # Confidentiality check (N ≤ 1)
    if filtered_data.shape[0] <= 1 and len(selected_filters) > 0:
        st.warning("⚠️ Data is unavailable to protect confidentiality (N ≤ 1).")
        filtered_data = df_survey.iloc[0:0].copy()  # ✅ empty but with same columns

    
    # Heatmap of Satisfaction vs Likelihood/NPS
    category_order = ["High", "Medium", "Low"]
    category_order2 = ["Promoter", "Passive", "Detractor"]
    if combine_with_nps:
        filtered_data['category_nps'] = pd.Categorical(filtered_data['category_nps'], categories=category_order2, ordered=True)
        pivot_table = filtered_data.pivot_table(index='category_sat', columns='category_nps', aggfunc='size', fill_value=0).reindex(index=category_order, columns=category_order2)
    else:
        filtered_data['category_ke1'] = pd.Categorical(filtered_data['category_ke1'], categories=category_order, ordered=True)
        pivot_table = filtered_data.pivot_table(index='category_sat', columns='category_ke1', aggfunc='size', fill_value=0).reindex(index=category_order, columns=category_order)
    
    # Replace NaN with 0
    pivot_table.fillna(0, inplace=True)
    
    # Calculate percentages and annotations
    total = pivot_table.values.sum()
    percentages = pivot_table / total * 100
    annotations = pivot_table.astype(str) + "\n(" + percentages.round(1).astype(str) + "%)"

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        pivot_table, annot=annotations, fmt="", cmap="Blues", ax=ax, cbar=False
    )
    ax.set_title('Heatmap of Satisfaction vs NPS' if combine_with_nps else 'Heatmap of Satisfaction vs Likelihood to Stay')
    ax.set_xlabel('NPS' if combine_with_nps else 'Likelihood to Stay')
    ax.set_ylabel('Satisfaction')
    st.pyplot(fig)

    # SECTION - COMPARISON

    st.subheader('Demography Comparison', divider='gray')

    # Sort combined_category values alphabetically
    ordered_categories = sorted(filtered_data['combined_category'].unique())

    # Display the selectbox with sorted options
    selected_category = st.selectbox(
        "Select Combined Category",
        ordered_categories
    )

    comparison_column = st.selectbox(
        'Select the column for comparison:',
        options=columns_list,
        format_func=lambda x: x.capitalize()
    )

    # Filter data for selected combined category and count occurrences by the comparison column
    select_combine = filtered_data[filtered_data['combined_category'] == selected_category]
    category_counts = select_combine[comparison_column].value_counts().reset_index()
    category_counts.columns = [comparison_column, 'count']

    # Calculate a dynamic height with a minimum threshold
    min_height = 300
    dynamic_height = max(len(category_counts) * 40, min_height)

    total_emp = category_counts['count'].sum()

   # Confidentiality check: Store original size before filtering
    original_size = category_counts.shape[0]

    # Confidentiality check: Remove rows where N=1
    category_counts = category_counts[category_counts['count'] > 1]

    # Calculate the number of rows removed
    rows_removed = original_size - category_counts.shape[0]

    # If any rows were removed, show the disclaimer
    if rows_removed > 0:
        st.write(f"Disclaimer: {rows_removed} entry/entries in the '{comparison_column.capitalize()}' column were removed to protect confidentiality (N=1).")

    # Adjust the sorting behavior based on the comparison_column for the list
    if comparison_column in ['layer', 'tenure_category']:
        # Sort by the comparison column itself and get the list
        sorted_demography = category_counts.sort_values(by=comparison_column, ascending=True)[comparison_column].tolist()
    else:
        # Sort by avg_satisfaction and get the list
        sorted_demography = category_counts.sort_values(by='count', ascending=False)[comparison_column].tolist()

    # Calculate percentages
    category_counts['percentage'] = (category_counts['count'] / category_counts['count'].sum()) * 100

    # Create the Plotly bar chart
    bar_chart = px.bar(
        category_counts,
        y=comparison_column,
        x='count',
        hover_data={},
        category_orders={comparison_column: sorted_demography}  # Order dimensions by sorted average score
    )

    # Customize chart appearance
    bar_chart.update_traces(
        texttemplate='%{x:.0f} (%{customdata:.1f}%)',  # Display count values and percentages
        textposition='auto',
        marker_color='#1f77b4',
        customdata=category_counts['percentage']  # Pass percentages as custom data
    )
    bar_chart.update_layout(
        title_text=f'Breakdown of {selected_category} by {comparison_column.capitalize()} (N={total_emp})',
        yaxis_title=" ",
        xaxis_title=" ",
        height=dynamic_height
    )

    st.plotly_chart(bar_chart, use_container_width=True)
