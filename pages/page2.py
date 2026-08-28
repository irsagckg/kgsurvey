from navigation import make_sidebar, make_filter
import streamlit as st
from data_processing import finalize_data
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


st.set_page_config(
    page_title='Mood Meter',
    page_icon=':😊:', 
)

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

    st.header('Mood Meter Overview', divider='rainbow')

    # ==============================
    # FILTER SECTION
    # ==============================
    selected_filters = make_filter(columns_list, combined_df)

    # Apply selected filters to the combined data
    filtered_data = combined_df.copy()
    for col, values in selected_filters.items():
        if col in filtered_data.columns and values:
            filtered_data = filtered_data[filtered_data[col].isin(values)]

    #st.write("Selected filters:", selected_filters)
    #st.write("Combined filtered rows:", len(filtered_data))
    # =========================================
    # 🟡 Remove rows where N per year equals 1
    # =========================================
    rows_removed_total = 0

    # Loop per tahun (2023, 2024, 2025)
    for year in [2023, 2024, 2025]:
        n_col = f"{year} N"
        if n_col in filtered_data.columns:
            before = len(filtered_data)
            filtered_data = filtered_data[filtered_data[n_col] != 1]
            rows_removed_total += before - len(filtered_data)

    # 📝 Confidentiality disclaimer
    if rows_removed_total > 0:
        st.write(
            f"Disclaimer: {rows_removed_total} entry/entries were removed to protect confidentiality (N=1) across years 2023–2025."
        )


    # ==============================
    # MOOD METER 100% STACKED BAR
    # ==============================
    # Gabungkan semua data hasil filter

    # Pastikan semua dataframe sudah ada
    df_survey23_filtered = df_survey23.copy()
    df_survey24_filtered = df_survey24.copy()
    df_survey25_filtered = df_survey25.copy()

    # Tambahkan kolom tahun
    df_survey23_filtered = df_survey23_filtered.assign(year=2023)
    df_survey24_filtered = df_survey24_filtered.assign(year=2024)
    df_survey25_filtered = df_survey25_filtered.assign(year=2025)
    # Gabungkan semua dataframe hasil filter
    df_all = pd.concat(
        [
            df_survey23_filtered.assign(year=2023),
            df_survey24_filtered.assign(year=2024),
            df_survey25_filtered.assign(year=2025)
        ],
        ignore_index=True
    )


    # Gabungkan semua data
    df_combined = pd.concat(
        [df_survey23_filtered, df_survey24_filtered, df_survey25_filtered],
        ignore_index=True
    )

    # Hitung unique nik per EMO per tahun
    mood_summary = (
        filtered_data.groupby(['year', 'EMO'])['nik']
        .nunique()
        .reset_index(name='count')
    )

    # =====================================================
    # 🟡 Confidentiality check: remove years with N=1 total
    # =====================================================
    # Hitung jumlah unik nik per tahun di data hasil filter
    n_per_year = filtered_data.groupby('year')['nik'].nunique().to_dict()

    # Hapus data tahun yang hanya punya 1 responden
    years_to_remove = [y for y, n in n_per_year.items() if n == 1]
    rows_removed_total = filtered_data[filtered_data['year'].isin(years_to_remove)].shape[0]
    filtered_data = filtered_data[~filtered_data['year'].isin(years_to_remove)]

    # 📝 Disclaimer tampil hanya kalau ada yang dihapus
    if years_to_remove:
        st.write(
            f"Disclaimer: Data for year(s) {', '.join(map(str, years_to_remove))} "
            f"were removed to protect confidentiality (N=1)."
        )


    # Hitung total per tahun untuk normalisasi 100%
    total_per_year = mood_summary.groupby('year')['count'].transform('sum')
    mood_summary['percentage'] = (mood_summary['count'] / total_per_year) * 100
    mood_summary['year'] = mood_summary['year'].astype(str)
    # Definisikan warna, emotikon, dan deskripsi
    mood_map = {
        1: {'emo': '😭', 'desc': 'Sedih', 'color': '#8B0000'},
        2: {'emo': '😞', 'desc': 'Kesepian', 'color': '#CD5C5C'},
        3: {'emo': '😐', 'desc': 'Tertekan', 'color': '#FFA07A'},
        4: {'emo': '😠', 'desc': 'Marah', 'color': '#FFE4B5'},
        5: {'emo': '😄', 'desc': 'Senang', 'color': '#FFD700'},
        6: {'emo': '😁', 'desc': 'Bermakna', 'color': '#ADFF2F'},
        7: {'emo': '🤩', 'desc': 'Tenteram', 'color': '#00BFFF'},
        8: {'emo': '😍', 'desc': 'Tenang', 'color': '#00008B'}
    }

    mood_summary['desc'] = mood_summary['EMO'].map(lambda x: mood_map[x]['desc'])
    mood_summary['emo'] = mood_summary['EMO'].map(lambda x: mood_map[x]['emo'])
    mood_summary['color'] = mood_summary['EMO'].map(lambda x: mood_map[x]['color'])

    # Label text format: "xx%(n)"
    mood_summary['label'] = mood_summary.apply(
        lambda row: f"{row['percentage']:.1f}% ({row['count']})", axis=1
    )


    # 🚫 Hapus tahun yang hanya punya N=1
    year_counts = mood_summary.groupby('year')['count'].sum()
    years_to_remove = year_counts[year_counts <= 1].index.tolist()

    if years_to_remove:
        st.warning(
            f"⚠️ Data untuk tahun {', '.join(map(str, years_to_remove))} dihapus karena hanya memiliki satu responden (N=1)."
        )
        mood_summary = mood_summary[~mood_summary['year'].isin(years_to_remove)]

    # Kalau semua tahun kehapus (artinya semua N=1), hentikan eksekusi
    if mood_summary.empty:
        st.stop()

    # Buat stacked bar chart 100%
    fig = px.bar(
        mood_summary,
        x='year',
        y='percentage',
        color='desc',
        text='label',
        color_discrete_map={v['desc']: v['color'] for v in mood_map.values()},
        category_orders={'year': ['2023', '2024', '2025'], 'desc': [v['desc'] for v in mood_map.values()]},
        custom_data=['emo', 'desc', 'count']
    )

    # Update layout
    fig.update_traces(
        textposition='inside',
        textfont=dict(size=12, color='black'),
        hovertemplate=(
            "<b>%{customdata[1]}</b> %{customdata[0]}<br>"
            "Tahun: %{x}<br>"
            "Jumlah: %{customdata[2]}<br>"
            "Persentase: %{y:.1f}%<extra></extra>"
        )
    )

    fig.for_each_trace(lambda t: t.update(textfont_color='white') if t.marker.color in ['#00008B','#8B0000','#CD5C5C'] else None)

    fig.update_layout(
        barmode='stack',
        yaxis=dict(title='Persentase', range=[0, 100], ticksuffix='%'),
        xaxis_title='Tahun',
        title='Mood Meter',
        legend_title='Emosi',
        template='presentation',
        height=500
    )
    fig.update_xaxes(type='category')

    st.plotly_chart(fig, use_container_width=True)


    
    # ==============================
    # ADDITIONAL CHART: MOOD METER BY FILTER
    # ==============================

    keterangan = [
        "1 😭 Sedih",
        "2 😞 Kesepian",
        "3 😐 Tertekan",
        "4 😠 Marah",
        "5 😄 Senang",
        "6 😁 Bermakna",
        "7 🤩 Tenteram",
        "8 😍 Tenang"
    ]
    unit_column = st.selectbox(
        'Select the column to compare mood meter by:',
        options=columns_list,
        format_func=lambda x: x.capitalize()
    )

    # Year selector — default to 2025
    year_options = ["2023", "2024", "2025"]
    selected_year = st.selectbox("Select Year to Display:", year_options, index=year_options.index("2025"))

    # Drop baris yang tidak punya nilai EMO atau unit_column
    filtered_df = filtered_data.dropna(subset=['EMO', unit_column], how='any')

    # Filter by selected year
    filtered_df = filtered_df[filtered_df['year'] == int(selected_year)]

    if filtered_df.empty:
        st.info("Tidak ada data yang cocok dengan filter saat ini.")
    else:
        # Hitung jumlah mood per kategori
        mood_counts = filtered_df.groupby([unit_column, 'EMO']).size().unstack(fill_value=0)

        # Confidentiality: hapus baris yang cuma punya 1 responden
        original_size = mood_counts.shape[0]
        mood_counts = mood_counts[mood_counts.sum(axis=1) > 1]
        rows_removed = original_size - mood_counts.shape[0]

        if rows_removed > 0:
            st.write(f"Disclaimer: {rows_removed} entry/entries in the '{unit_column.capitalize()}' column were removed to protect confidentiality (N=1).")

        # Pastikan semua level EMO (1–8) ada
        for i in range(1, 9):
            if i not in mood_counts.columns:
                mood_counts[i] = 0

        mood_counts = mood_counts.reset_index()
        mood_counts = mood_counts[[unit_column] + list(range(1, 9))]

        # Ubah ke format panjang
        mood_counts = mood_counts.melt(
            id_vars=unit_column,
            value_vars=list(range(1, 9)),
            var_name='EMO',
            value_name='count'
        )
        mood_counts['EMO'] = mood_counts['EMO'].astype(int)

        # Hitung persentase per kategori
        mood_total = mood_counts.groupby(unit_column)['count'].transform('sum')
        mood_counts['percentage'] = (mood_counts['count'] / mood_total) * 100
        mood_counts['percentage'] = mood_counts['percentage'].fillna(0)

        mood_colors = ['#8B0000', '#CD5C5C', '#FFA07A', '#FFE4B5', '#FFD700', '#ADFF2F', '#00BFFF', '#00008B']

        # Plot dengan Plotly
        fig = go.Figure()

        for mood_level in range(1, 9):
            mood_data = mood_counts[mood_counts['EMO'] == mood_level]
            if mood_data.empty:
                continue

            # Nama safety: kalau index di luar range (seharusnya tidak) fallback ke angka
            name = keterangan[mood_level - 1] if 0 <= (mood_level - 1) < len(keterangan) else str(mood_level)

            fig.add_trace(
                go.Bar(
                    x=mood_data['percentage'],
                    y=mood_data[unit_column],
                    name=name,
                    orientation='h',
                    text=mood_data.apply(lambda row: f"{row['percentage']:.1f}%\n({int(row['count'])})", axis=1),
                    textposition='inside',
                    marker=dict(color=mood_colors[mood_level - 1]),
                    hovertemplate='%{y}<br>' + name + '<br>Persentase: %{x:.1f}%<br>Jumlah: %{text}<extra></extra>'
                )
            )

        fig.update_layout(
            title_text=f'Mood Level Distribution by {unit_column.capitalize()} ({selected_year})',
            xaxis_title='Percentage (%)',
            yaxis_title=unit_column.capitalize(),
            barmode='stack',
            template='presentation',
            width=1000,
            height=1000
        )

        st.plotly_chart(fig, use_container_width=True)
