from navigation import make_sidebar, make_filter
import streamlit as st
from data_processing import finalize_data
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title='NPS',
    page_icon='🗣️',
)

make_sidebar()
df_survey25, df_survey24, df_survey23, df_creds = finalize_data()

# ==============================
# FILTER CONFIG
# ==============================
columns_list = [
    'unit', 'subunit', 'directorate', 'division', 'site', 'department', 'section',
    'layer', 'work_contract', 'generation', 'gender',
    'tenure_category', 'region', 'year', 'core'
]

# ==============================
# MAIN SECTION
# ==============================
if st.session_state.get('authentication_status'):
    username = st.session_state['username']
    user_units = df_creds.loc[df_creds['username'] == username, 'unit'].values[0].split(', ')

    # Filter each dataset based on user access
    df_survey25 = df_survey25[df_survey25['subunit'].isin(user_units)]
    df_survey24 = df_survey24[df_survey24['subunit'].isin(user_units)]
    df_survey23 = df_survey23[df_survey23['subunit'].isin(user_units)]

    # Add year column
    df_survey25['year'] = 2025
    df_survey24['year'] = 2024
    df_survey23['year'] = 2023
    combined_df = pd.concat([df_survey23, df_survey24, df_survey25], ignore_index=True)
    st.header('Net Promoter Score Overview', divider='rainbow')
    selected_filters = make_filter(columns_list, combined_df)

    filtered_data = combined_df.copy()
    for col, vals in selected_filters.items():
        filtered_data = filtered_data[filtered_data[col].isin(vals)]

    if filtered_data.empty:
        st.warning("No data available after applying filters.")
        st.stop()


    # ==============================
    # HITUNG NPS PER TAHUN
    # ==============================
    def calculate_nps(df):
        df['NPS'] = pd.to_numeric(df['NPS'], errors='coerce')
        total = df['NPS'].count()
        promoters = df[df['NPS'] >= 9].shape[0]
        passives = df[(df['NPS'] >= 7) & (df['NPS'] <= 8)].shape[0]
        detractors = df[df['NPS'] <= 6].shape[0]

        percent_promoters = (promoters / total) * 100 if total > 0 else 0
        percent_passives = (passives / total) * 100 if total > 0 else 0
        percent_detractors = (detractors / total) * 100 if total > 0 else 0
        nps = percent_promoters - percent_detractors
        return {
            'promoters': promoters,
            'passives': passives,
            'detractors': detractors,
            'percent_promoters': percent_promoters,
            'percent_passives': percent_passives,
            'percent_detractors': percent_detractors,
            'nps': nps,
            'total': total
        }

    results = {}
    for year in [2023, 2024, 2025]:
        df_year = filtered_data[filtered_data['year'] == year]
        results[year] = calculate_nps(df_year)

    # ==============================
    # BUAT DATAFRAME UNTUK VISUAL
    # ==============================
    nps_df = pd.DataFrame({
        'Year': [2023, 2024, 2025],
        'Detractors': [results[y]['percent_detractors'] for y in [2023, 2024, 2025]],
        'Passives': [results[y]['percent_passives'] for y in [2023, 2024, 2025]],
        'Promoters': [results[y]['percent_promoters'] for y in [2023, 2024, 2025]],
        'NPS': [results[y]['nps'] for y in [2023, 2024, 2025]]
    })

    # ==============================
    # 🚫 Confidentiality check (hapus tahun dengan total responden N=1)
    # ==============================
    year_counts = {year: results[year]['total'] for year in [2023, 2024, 2025]}
    years_to_remove = [year for year, count in year_counts.items() if count <= 1]

    if years_to_remove:
        st.warning(
            f"⚠️ Data untuk tahun {', '.join(map(str, years_to_remove))} "
            f"dihapus untuk melindungi kerahasiaan (N=1)."
        )
        nps_df = nps_df[~nps_df['Year'].isin(years_to_remove)]

    # Kalau semua tahun dihapus → stop biar chart nggak muncul
    if nps_df.empty:
        st.stop()








    # ==============================
    # STACKED BAR 100%
    # ==============================
    # Pastikan kolom Year tetap numerik agar bar tetap terbaca
    nps_df['Year'] = nps_df['Year'].astype(int)

    fig = go.Figure()

    # Detractors
    fig.add_trace(go.Bar(
        x=nps_df['Year'],
        y=nps_df['Detractors'],
        name='Detractors',
        marker_color='tomato',
        text=[f"{v:.1f}% ({results[int(y)]['detractors']})" for y, v in zip(nps_df['Year'], nps_df['Detractors'])],
        textposition='inside'
    ))

    # Passives
    fig.add_trace(go.Bar(
        x=nps_df['Year'],
        y=nps_df['Passives'],
        name='Passives',
        marker_color='beige',
        text=[f"{v:.1f}% ({results[int(y)]['passives']})" for y, v in zip(nps_df['Year'], nps_df['Passives'])],
        textposition='inside'
    ))

    # Promoters
    fig.add_trace(go.Bar(
        x=nps_df['Year'],
        y=nps_df['Promoters'],
        name='Promoters',
        marker_color='cadetblue',
        text=[f"{v:.1f}% ({results[int(y)]['promoters']})" for y, v in zip(nps_df['Year'], nps_df['Promoters'])],
        textposition='inside'
    ))

    # Tambahkan teks NPS% di atas setiap bar
    for year, nps_value in zip(nps_df['Year'], nps_df['NPS']):
        fig.add_annotation(
            x=year,
            y=105,
            text=f"<b>NPS: {nps_value:.1f}%</b>",
            showarrow=False,
            font=dict(size=14, color='black')
        )

    # Layout
    fig.update_layout(
        barmode='stack',
        title='NPS Breakdown by Year',
        xaxis=dict(
            title='Year',
            tickmode='array',
            tickvals=nps_df['Year'],
            ticktext=[str(int(y)) for y in nps_df['Year']]  # tampil tanpa .5
        ),
        yaxis=dict(title='Percentage', range=[0, 110]),
        legend_title_text='Category',
        height=500,
        template='simple_white',
    )

    st.plotly_chart(fig, use_container_width=True)


    st.markdown("###### NPS Score Categories")
    legend_columns = st.columns(4)

    categories = [
        {"label": "Needs Improvement (-100 to 0)", "color": "#c7522a"},
        {"label": "Good (0 to 30)", "color": "#e9c46a"},
        {"label": "Great (30 to 70)", "color": "#74a892"},
        {"label": "Excellent (70 to 100)", "color": "#6B9CB0"},
    ]

    # Display each category with color
    for col, category in zip(legend_columns, categories):
        col.markdown(f"<div style='background-color: {category['color']}; padding: 5px; border-radius: 4px; text-align: center;'>{category['label']}</div>", unsafe_allow_html=True)

    st.divider()

    # ==============================
    # 🎯 FILTER
    # ==============================

    selected_filter = st.selectbox(
        " Select Demographic Variable :",
        options=columns_list,
        format_func=lambda x: x.capitalize()
    )


    # ==============================
    # 📊 TABEL PERBANDINGAN NPS (2023–2025)
    # ==============================

    st.markdown("##### 📋 NPS Comparison Table (2023–2025)")

    nps_compare = filtered_data.copy()
    # ==============================
    # 🔒 CONFIDENTIALITY CHECK (N=1)
    # ==============================

    # Hitung jumlah unik per tahun dan per kategori filter
    yearly_counts = (
        nps_compare.groupby([selected_filter, 'year'])['nik']
        .nunique()
        .unstack(fill_value=0)
    )

    # Buat kolom total untuk tracking
    for y in [2023, 2024, 2025]:
        if y not in yearly_counts.columns:
            yearly_counts[y] = 0

    # Hapus kategori yang punya N=1 di salah satu tahun
    mask_remove = (yearly_counts[[2023, 2024, 2025]] == 1).any(axis=1)
    to_remove = yearly_counts[mask_remove].index.tolist()

    if len(to_remove) > 0:
        removed_rows = nps_compare[nps_compare[selected_filter].isin(to_remove)]
        nps_compare = nps_compare[~nps_compare[selected_filter].isin(to_remove)]
        st.info(
            f"Disclaimer: {len(to_remove)} entry/entries in "
            f"'{selected_filter.capitalize()}' were removed to protect confidentiality (N=1)."
        )


    # --- Hitung summary NPS ---
    def calc_nps_summary(df):
        # Pastikan kolom NPS numerik
        df['NPS'] = pd.to_numeric(df['NPS'], errors='coerce')
        total = df['NPS'].count()

        promoters = (df['NPS'] >= 9).sum()
        detractors = (df['NPS'] <= 6).sum()
        passives = ((df['NPS'] >= 7) & (df['NPS'] <= 8)).sum()

        promoters_pct = (promoters / total) * 100 if total > 0 else 0
        detractors_pct = (detractors / total) * 100 if total > 0 else 0
        nps_score = promoters_pct - detractors_pct

        return pd.Series({
            'Detractors': detractors_pct,
            'Promoters': promoters_pct,
            'NPS': nps_score,
            'Promoters_Count': promoters,
            'Passives_Count': passives,
            'Detractors_Count': detractors,
            'Total': total
        })

    summary = nps_compare.groupby([selected_filter, 'year'], dropna=False).apply(calc_nps_summary).reset_index()

    # Pisahkan per tahun
    summary_2023 = summary[summary['year'] == 2023].drop(columns=['year'])
    summary_2024 = summary[summary['year'] == 2024].drop(columns=['year'])
    summary_2025 = summary[summary['year'] == 2025].drop(columns=['year'])

    # Gabungkan
    comparison_df = pd.merge(summary_2023, summary_2024, on=selected_filter, suffixes=('_2023', '_2024'), how='outer')
    comparison_df = pd.merge(comparison_df, summary_2025, on=selected_filter, how='outer')

    comparison_df.rename(columns={
        'Detractors': 'Detractors_2025',
        'Promoters': 'Promoters_2025',
        'NPS': 'NPS_2025'
    }, inplace=True)

    # Hitung perubahan
    comparison_df['Δ 2023–2024 (%)'] = (comparison_df['NPS_2024'] - comparison_df['NPS_2023']).round(1)
    comparison_df['Δ 2024–2025 (%)'] = (comparison_df['NPS_2025'] - comparison_df['NPS_2024']).round(1)

    # Urutkan kolom
    ordered_cols = [
        selected_filter,
        'Detractors_2023', 'Promoters_2023', 'NPS_2023',
        'Detractors_2024', 'Promoters_2024', 'NPS_2024',
        'Δ 2023–2024 (%)',
        'Detractors_2025', 'Promoters_2025', 'NPS_2025',
        'Δ 2024–2025 (%)'
    ]
    comparison_df = comparison_df[[c for c in ordered_cols if c in comparison_df.columns]]

    # Bulatkan angka
    numeric_cols = [
        'Detractors_2023', 'Promoters_2023', 'NPS_2023',
        'Detractors_2024', 'Promoters_2024', 'NPS_2024',
        'Detractors_2025', 'Promoters_2025', 'NPS_2025'
    ]
    for col in numeric_cols:
        if col in comparison_df.columns:
            comparison_df[col] = comparison_df[col].round(1)

    # Format kolom perubahan
    def format_change(v):
        if pd.isna(v):
            return "-"
        elif v > 0:
            return f"{v:+.1f}% ↑"
        elif v < 0:
            return f"{v:+.1f}% ↓"
        else:
            return f"{v:+.1f}% →"

    for col in ['Δ 2023–2024 (%)', 'Δ 2024–2025 (%)']:
        comparison_df[col + "_val"] = comparison_df[col]
        comparison_df[col] = comparison_df[col].apply(format_change)

    # Warna perubahan
    def color_change(val):
        if isinstance(val, str):
            if '↑' in val:
                return 'color: #228B22; font-weight: 600;'  # hijau
            elif '↓' in val:
                return 'color: #B22222; font-weight: 600;'  # merah
            elif '→' in val:
                return 'color: grey; font-weight: 600;'
        return ''

    # 🔹 Highlight abu-abu untuk kolom NPS
    def highlight_nps(col):
        if any(keyword in col for keyword in ['NPS_2023', 'NPS_2024', 'NPS_2025']):
            return ['background-color: #f3f3f3' for _ in range(len(comparison_df))]
        else:
            return ['' for _ in range(len(comparison_df))]

    # Simpan hanya kolom yang benar-benar ada
    available_cols = [c for c in comparison_df.columns if not c.endswith('_val')]

    # Terapkan style aman
    styled_df = (
        comparison_df
        .drop(columns=[c for c in comparison_df.columns if c.endswith('_val')], errors='ignore')
        .style
        .applymap(color_change, subset=[c for c in ['Δ 2023–2024 (%)', 'Δ 2024–2025 (%)'] if c in comparison_df.columns])
        .apply(highlight_nps, subset=available_cols, axis=0)
        .format({col: "{:.1f}" for col in numeric_cols if col in comparison_df.columns})
    )

    st.dataframe(styled_df, use_container_width=True)

    # ==============================
    # 🎯STACKED BAR 
    # ==============================

    year_options = ["2023", "2024", "2025"]
    selected_year = st.selectbox("Select Year to Display:", year_options, index=year_options.index("2025"))

    # Filter data berdasarkan tahun terpilih
    filtered_data = filtered_data[filtered_data['year'] == int(selected_year)]

    if selected_filter in filtered_data.columns:
        # Hanya ambil data yang punya NPS
        filtered_data = filtered_data.dropna(subset=['NPS'])
        filtered_data['NPS'] = pd.to_numeric(filtered_data['NPS'], errors='coerce')

        if filtered_data.empty:
            st.warning(f"No NPS data available for {selected_year}.")
        else:
            # --- Hitung jumlah & persentase tiap kategori NPS ---
            grouped = filtered_data.groupby(selected_filter).apply(lambda x: pd.Series({
                'Promoters': (x['NPS'] >= 9).mean() * 100,
                'Passives': ((x['NPS'] >= 7) & (x['NPS'] <= 8)).mean() * 100,
                'Detractors': (x['NPS'] <= 6).mean() * 100,
                'Promoters_Count': (x['NPS'] >= 9).sum(),
                'Passives_Count': ((x['NPS'] >= 7) & (x['NPS'] <= 8)).sum(),
                'Detractors_Count': (x['NPS'] <= 6).sum(),
            })).reset_index()

            # --- Confidentiality check (hapus kategori dengan total N=1) ---
            grouped['Total'] = grouped[['Promoters_Count', 'Passives_Count', 'Detractors_Count']].sum(axis=1)
            removed_rows = grouped[grouped['Total'] == 1][selected_filter].tolist()
            grouped = grouped[grouped['Total'] > 1]

            if len(removed_rows) > 0:
                st.info(f"Disclaimer: {len(removed_rows)} entry/entries in '{selected_filter.capitalize()}' were removed to protect confidentiality (N=1).")

            # --- Bentuk data long format ---
            stacked_data = grouped.melt(
                id_vars=[selected_filter],
                value_vars=['Promoters', 'Passives', 'Detractors'],
                var_name='NPS Category',
                value_name='Percentage'
            )

            stacked_counts = grouped.melt(
                id_vars=[selected_filter],
                value_vars=['Promoters_Count', 'Passives_Count', 'Detractors_Count'],
                var_name='NPS Category Count',
                value_name='Counts'
            )

            # Gabungkan count
            stacked_data['Counts'] = stacked_counts['Counts'].values

            # --- Warna kategori ---
            colors = {
                'Promoters': 'cadetblue',  
                'Passives': 'beige',   
                'Detractors': 'tomato' 
            }

            # --- Plot stacked bar ---
            fig_stacked = go.Figure()

            for category in ['Promoters', 'Passives', 'Detractors']:
                cat_data = stacked_data[stacked_data['NPS Category'] == category]
                fig_stacked.add_trace(go.Bar(
                    y=cat_data[selected_filter],
                    x=cat_data['Percentage'],
                    name=category,
                    orientation='h',
                    marker_color=colors[category],
                    text=cat_data.apply(lambda r: f"{r['Percentage']:.1f}%<br>({int(r['Counts'])})", axis=1),
                    textposition='inside'
                ))

            # --- Hitung skor NPS per kategori (Promoters - Detractors) ---
            grouped['NPS_Score'] = (grouped['Promoters'] - grouped['Detractors']).round(1)

            # --- Tambahkan annotation NPS di kanan bar ---
            for _, row in grouped.iterrows():
                fig_stacked.add_annotation(
                    x=108,
                    y=row[selected_filter],
                    text=f"{row['NPS_Score']}%",
                    showarrow=False,
                    font=dict(size=16, color="black"),
                    align="left"
                )

            # --- Layout ---
            fig_stacked.update_layout(
                title=f"NPS Breakdown by {selected_filter.title()} ({selected_year})",
                xaxis_title="Percentage (%)",
                yaxis_title=selected_filter.title(),
                barmode='stack',
                height=600,
                legend_title_text="NPS Category",
                margin=dict(l=50, r=50, t=80, b=50),  # kiri diperkecil biar gak makan tempat
                xaxis=dict(
                    range=[0, 110],
                    title_font=dict(size=14, color='black'),
                    tickfont=dict(size=14, color='black')
                ),
                yaxis=dict(
                    title_font=dict(size=14, color='black'),
                    tickfont=dict(size=14, color='black', family='Arial', weight='bold')
                ),
                title_font=dict(size=14, color='black'),
                template='simple_white'
            )


            # Tambah ini biar label Y jadi bold
            fig_stacked.update_yaxes(title_font=dict(size=14), tickfont=dict(size=14, weight='bold'))


            st.plotly_chart(fig_stacked, use_container_width=True)
