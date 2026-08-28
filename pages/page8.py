import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from data_processing import finalize_data
from navigation import make_sidebar, make_filter

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title='IPA', page_icon='📕')
make_sidebar()

# ==============================
# LOAD DATA
# ==============================
df_survey25, df_survey24, df_survey23, df_creds = finalize_data()
df_all = {"2025": df_survey25, "2024": df_survey24, "2023": df_survey23}

st.header('Importance–Performance Analysis (IPA)', divider='rainbow')

# ==============================
# SELECT YEAR
# ==============================
selected_year = st.selectbox("Pilih tahun survei:", options=list(df_all.keys()), index=0)
df = df_all[selected_year].copy()
df = df[df['submit_date'].notna() & (df['submit_date'] != "")]

# ==============================
# USER ACCESS FILTER
# ==============================
if st.session_state.get('authentication_status'):
    username = st.session_state['username']
    user_units = df_creds.loc[df_creds['username'] == username, 'unit'].values[0].split(', ')
    df = df[df['subunit'].isin(user_units)]

# ==============================
# FILTER TAMBAHAN
# ==============================
columns_list = [
    'unit', 'subunit', 'directorate', 'division', 'department', 'section',
    'layer', 'status', 'generation', 'gender', 'marital', 'education',
    'tenure_category', 'children', 'region', 'participation_23', 'core'
]

selected_filters = make_filter(columns_list, df, key_prefix="ipa_filter")

for col, values in selected_filters.items():
    if values:
        df = df[df[col].isin(values)]

st.write(f"Jumlah data setelah filter: {df.shape[0]} responden")

# ==============================
# SELECT TARGET VARIABLE (SAT or NPS)
# ==============================
target_option = st.radio(
    "Pilih variabel target untuk menghitung *Importance*:",
    options=["SAT", "NPS"],
    format_func=lambda x: "Satisfaction (SAT)" if x == "SAT" else "Net Promoter Score (NPS)",
    horizontal=True
)

# ==============================
# DEFINISI VARIABEL
# ==============================
independent_vars = [
    'KD0', 'KD1', 'KD2', 'KD3', 'KE0', 'KE1', 'KE2', 'KE3',
    'KI0', 'KI1', 'KI2', 'KI3', 'KI4', 'KI5',
    'KR0', 'KR1', 'KR2', 'KR3', 'KR4', 'KR5',
    'PR0', 'PR1', 'PR2',
    'TU0', 'TU1', 'TU2', 'TU3'
]
if selected_year in ["2024", "2023"]:
    independent_vars.remove("TU3")

# ==============================
# FILTER DATA
# ==============================
if target_option not in df.columns:
    st.error(f"Kolom '{target_option}' tidak ditemukan di dataset.")
    st.stop()

df = df.dropna(subset=[target_option] + independent_vars)
if df.empty:
    st.warning("Tidak ada data yang memenuhi filter saat ini.")
    st.stop()

# ==============================
# IMPORTANCE–PERFORMANCE ANALYSIS
# ==============================
performance_mean = df[independent_vars].mean()  # Performance tetap mean item
importance_mean = performance_mean  # Just to keep naming consistent

# Standardisasi dan regresi
scaler = StandardScaler()
X = scaler.fit_transform(df[independent_vars])
y = scaler.fit_transform(df[[target_option]]).flatten()

model = LinearRegression()
model.fit(X, y)

# Importance = standardized beta coefficient
importance_values = model.coef_

# Construct result dataframe
correlation_df = pd.DataFrame({
    'Factor': independent_vars,
    'Importance': [round(beta, 3) for beta in importance_values],
    'Performance': [round(beta, 3) for beta in performance_mean.values]
})

# Midpoints
importance_min, importance_max = correlation_df['Importance'].min(), correlation_df['Importance'].max()
performance_min, performance_max = correlation_df['Performance'].min(), correlation_df['Performance'].max()
importance_midpoint = (importance_max + importance_min) / 2
performance_midpoint = (performance_max + performance_min) / 2

# ==============================
# KATEGORI QUADRANT
# ==============================
def classify_factor_dynamic(importance, performance, imp_mid, perf_mid):
    if importance > imp_mid and performance > perf_mid:
        return 'Leverage'
    elif importance > imp_mid and performance <= perf_mid:
        return 'Improve'
    elif importance <= imp_mid and performance > perf_mid:
        return 'Nice to have'
    else:
        return 'Low priority'

correlation_df['Category'] = [
    classify_factor_dynamic(row['Importance'], row['Performance'], importance_midpoint, performance_midpoint)
    for _, row in correlation_df.iterrows()
]

# ==============================
# SCATTER PLOT
# ==============================
st.subheader(f"GRAFIK IPA {selected_year} (Target: {target_option})")

fig, ax = plt.subplots(figsize=(10, 6))
color_map = {
    'Leverage': '#2ca02c',
    'Improve': '#d62728',
    'Nice to have': '#1f77b4',
    'Low priority': '#ff7f0e'
}

for category, data in correlation_df.groupby('Category'):
    ax.scatter(data['Performance'], data['Importance'],
               label=category, color=color_map.get(category, 'gray'),
               s=100, alpha=0.8)

# Label faktor
for i, row in correlation_df.iterrows():
    ax.text(row['Performance'] + 0.01, row['Importance'], row['Factor'], fontsize=9, ha='left', va='bottom')

# Garis tengah
ax.axhline(y=importance_midpoint, color='green', linestyle='--', label="Importance Midpoint")
ax.axvline(x=performance_midpoint, color='red', linestyle='--', label="Performance Midpoint")

# Label dan style
ax.set_xlabel('Performance (Mean of Items)', fontsize=12, labelpad=10)
ax.set_ylabel(f'Importance (Standardized Beta vs {target_option})', fontsize=12, labelpad=10)
ax.set_title(f'Importance–Performance Analysis (Target: {target_option})', fontsize=16, pad=20)
ax.grid(True, linestyle='--', alpha=0.5)
ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

plt.tight_layout()
st.pyplot(fig)

# ==============================
# TABEL HASIL IPA
# ==============================
label_mapping = {
    'KD1': 'Kejelasan ekspektasi kerja (KD1)',
    'KD2': 'Dukungan kebutuhan kerja (KD2)',
    'KD3': 'Komitmen kesejahteraan (KD3)',
    'KD0': 'Pemenuhan kebutuhan dasar (KD0)',
    'KE1': 'Keinginan bertahan (KE1)',
    'KE2': 'Motivasi menjaga perusahaan (KE2)',
    'KE3': 'Rasa bangga (KE3)',
    'KE0': 'Keterlekatan emosional (KE0)',
    'KI1': 'Kesempatan menunjukkan kemampuan (KI1)',
    'KI2': 'Pengakuan hasil kerja (KI2)',
    'KI3': 'Otonomi dalam bekerja (KI3)',
    'KI4': 'Rasa dihargai (KI4)',
    'KI5': 'Dukungan untuk berkembang (KI5)',
    'KI0': 'Fasilitasi kontribusi individu (KI0)',
    'PR1': 'Bimbingan untuk bertumbuh (PR1)',
    'PR2': 'Kesempatan pengembangan karir (PR2)',
    'PR0': 'Tempat bertumbuh ideal (PR0)',
    'KR1': 'Rasa keadilan (KR1)',
    'KR2': 'Penghargaan atas pendapat (KR2)',
    'KR3': 'Rasa berharga pekerjaannya (KR3)',
    'KR4': 'Komitmen rekan kerja (KR4)',
    'KR5': 'Hubungan pertemanan (KR5)',
    'KR0': 'Kolaborasi yang baik (KR0)',
    'TU1': 'Keselarasan tujuan (TU1)',
    'TU2': 'Keterikatan dengan tujuan perusahaan (TU2)',
    'TU3': 'Penerapan nilai perusahaan (TU3)',
    'TU0': 'Menemukan tujuan hidup (TU0)',
}

correlation_df['Factor'] = correlation_df['Factor'].replace(label_mapping)

midpoint_row = pd.DataFrame({
    'Factor': ['Midpoint'],
    'Importance': [round(importance_midpoint, 3)],
    'Performance': [round(performance_midpoint, 3)],
    'Category': ['-']
})
correlation_df = pd.concat([correlation_df, midpoint_row], ignore_index=True)

st.markdown(f"##### Tabel hasil IPA {selected_year} (Target: {target_option})")
st.dataframe(correlation_df, use_container_width=True)
