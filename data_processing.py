import streamlit as st
import pandas as pd
import numpy as np
from fetch_data import fetch_data_survey25, fetch_data_survey24, fetch_data_survey23, fetch_data_creds

#@st.cache_data()
def finalize_data():
    df_survey25 = fetch_data_survey25()
    df_survey24 = fetch_data_survey24()
    df_survey23 = fetch_data_survey23()
    df_creds = fetch_data_creds()

    df_survey25['tenure'] = pd.to_numeric(df_survey25['tenure'], errors='coerce')
    df_survey24['tenure'] = pd.to_numeric(df_survey24['tenure'], errors='coerce')
    df_survey23['tenure'] = pd.to_numeric(df_survey23['tenure'], errors='coerce')

    # Categorizing tenure
    def categorize_tenure(df, col='tenure', new_col='tenure_category'):
        bins = [0, 1, 3, 6, 10, 15, 20, 25, float('inf')]
        labels = [
            '0 years',
            '1–2 years',
            '3–5 years',
            '6–9 years',
            '10–14 years',
            '15–19 years',
            '20–24 years',
            '25+ years'
        ]
        df[new_col] = pd.cut(df[col], bins=bins, labels=labels, right=False)
        return df

    # Apply to all surveys
    df_survey25 = categorize_tenure(df_survey25)
    df_survey24 = categorize_tenure(df_survey24)
    df_survey23 = categorize_tenure(df_survey23)

    # Convert all columns that can be numeric
    df_survey23 = df_survey23.apply(pd.to_numeric, errors="ignore")
    df_survey24 = df_survey24.apply(pd.to_numeric, errors="ignore")
    df_survey25 = df_survey25.apply(pd.to_numeric, errors="ignore")

    # make copies and add 'year' column so filtering by year works
    df_survey23 = df_survey23.copy()
    df_survey24 = df_survey24.copy()
    df_survey25 = df_survey25.copy()
    df_survey23['year'] = '2023'
    df_survey24['year'] = '2024'
    df_survey25['year'] = '2025'

    # Calculate the average for each dimension and round to 1 decimal place
    # For df_survey25
    df_survey25['average_kd'] = df_survey25[['KD1', 'KD2', 'KD3', 'KD0']].mean(axis=1).round(2)
    df_survey25['average_ki'] = df_survey25[['KI1', 'KI2', 'KI3', 'KI4', 'KI5', 'KI0']].mean(axis=1).round(2)
    df_survey25['average_kr'] = df_survey25[['KR1', 'KR2', 'KR3', 'KR4', 'KR5', 'KR0']].mean(axis=1).round(2)
    df_survey25['average_pr'] = df_survey25[['PR1', 'PR2', 'PR0']].mean(axis=1).round(2)
    df_survey25['average_tu'] = df_survey25[['TU1', 'TU2', 'TU3', 'TU0']].mean(axis=1).round(2)
    df_survey25['average_ke'] = df_survey25[['KE1', 'KE2', 'KE3', 'KE0']].mean(axis=1).round(2)

    # For df_survey24
    df_survey24['average_kd'] = df_survey24[['KD1', 'KD2', 'KD3', 'KD0']].mean(axis=1).round(2)
    df_survey24['average_ki'] = df_survey24[['KI1', 'KI2', 'KI3', 'KI4', 'KI5', 'KI0']].mean(axis=1).round(2)
    df_survey24['average_kr'] = df_survey24[['KR1', 'KR2', 'KR3', 'KR4', 'KR5', 'KR0']].mean(axis=1).round(2)
    df_survey24['average_pr'] = df_survey24[['PR1', 'PR2', 'PR0']].mean(axis=1).round(2)
    df_survey24['average_tu'] = df_survey24[['TU1', 'TU2', 'TU0']].mean(axis=1).round(2)  # difference here
    df_survey24['average_ke'] = df_survey24[['KE1', 'KE2', 'KE3', 'KE0']].mean(axis=1).round(2)
   
    # For df_survey23
    df_survey23['average_kd'] = df_survey23[['KD1', 'KD2', 'KD3', 'KD0']].mean(axis=1).round(2)
    df_survey23['average_ki'] = df_survey23[['KI1', 'KI2', 'KI3', 'KI4', 'KI5', 'KI0']].mean(axis=1).round(2)
    df_survey23['average_kr'] = df_survey23[['KR1', 'KR2', 'KR3', 'KR4', 'KR5', 'KR0']].mean(axis=1).round(2)
    df_survey23['average_pr'] = df_survey23[['PR1', 'PR2', 'PR0']].mean(axis=1).round(2)
    df_survey23['average_tu'] = df_survey23[['TU1', 'TU2', 'TU0']].mean(axis=1).round(2)  # difference here
    df_survey23['average_ke'] = df_survey23[['KE1', 'KE2', 'KE3', 'KE0']].mean(axis=1).round(2)

    # Mapping untuk layer
    layer_mapping = {
        'Group 5 Str Layer 1': 'Director',
        'Group 5': 'Professional setara Director (Consultant)',
        'Group 4 Str Layer 2': 'General Manager',
        'Group 4': 'Professional setara GM (Advisor)',
        'Group 3 Str Layer 3B': 'Senior Manager',
        'Group 3 Str Layer 3A': 'Manager',
        'Group 3': 'Professional setara Manager (Specialist)',
        'Group 2 Str Layer 4': 'Superintendent',
        'Group 2': 'Officer',
        'Group 1 Str Layer 5': 'Team Leader',
        'Group 1': 'Pelaksana',
        '-' :'-'
    }

    # Fungsi fleksibel: hanya ubah jika ada di mapping, jika tidak biarkan seperti aslinya
    def flexible_map(series, mapping):
        return series.apply(lambda x: mapping.get(x, x))
    
    # Terapkan ke masing-masing dataframe
    df_survey25['layer'] = flexible_map(df_survey25['layer'], layer_mapping)
    df_survey23['layer'] = flexible_map(df_survey23['layer'], layer_mapping)

    return df_survey25, df_survey24, df_survey23, df_creds

