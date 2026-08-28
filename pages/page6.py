import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
from data_processing import finalize_data
from navigation import make_sidebar, make_filter

# Streamlit page setup
st.set_page_config(page_title='Statistical Analysis', page_icon='📊')
make_sidebar()

# Load data
df_survey25, df_survey24, df_survey23, df_creds = finalize_data()

if st.session_state.get('authentication_status'):
    username = st.session_state['username']
    user_units = df_creds.loc[df_creds['username'] == username, 'unit'].values[0].split(', ')
    # Filter by user units and keep only respondents who submitted the survey
    df_survey25 = df_survey25[
        (df_survey25['subunit'].isin(user_units)) &
        (df_survey25['submit_date'].notna()) &
        (df_survey25['submit_date'] != "")
    ]
    df_survey24 = df_survey24[
        (df_survey24['subunit'].isin(user_units)) &
        (df_survey24['submit_date'].notna()) &
        (df_survey24['submit_date'] != "")
    ]
    df_survey23 = df_survey23[
        (df_survey23['subunit'].isin(user_units)) &
        (df_survey23['submit_date'].notna()) &
        (df_survey23['submit_date'] != "")
    ]


    df_all = {
        "2025": df_survey25,
        "2024": df_survey24,
        "2023": df_survey23
    }

    st.header('Statistical Analysis', divider='rainbow')

    # --- Apply Filter (like Categorization page) ---
    # --- Year selection ---
    selected_year = st.selectbox("Select survey year:", options=list(df_all.keys()), index=0)
    df = df_all[selected_year].copy()
    df = df[df['submit_date'].notna() & (df['submit_date'] != "")]

    columns_list = [
        'unit', 'subunit', 'directorate', 'division', 'department', 'section',
        'layer', 'status', 'generation', 'gender', 'marital', 'education',
        'tenure_category', 'children', 'region', 'participation_23', 'core'
    ]

    selected_filters = make_filter(columns_list, df, key_prefix="corr_filter")

    # ✅ Apply filter selections to df
    for col, values in selected_filters.items():
        if values:  # only filter when user selected something
            df = df[df[col].isin(values)]

    st.write(f"Data shape after filter: {df.shape[0]} rows × {df.shape[1]} columns")

    # --- Apply SAME filters to all years in df_all ---
    df_all_filtered = {}
    for y, d in df_all.items():
        d_filtered = d.copy()
        for col, values in selected_filters.items():
            if values and col in d_filtered.columns:
                d_filtered = d_filtered[d_filtered[col].isin(values)]
        df_all_filtered[y] = d_filtered

    df_all = df_all_filtered

    # ======================================================
    # SECTION 1 — CORRELATION TEST (MULTIPLE VARIABLES) with normality check
    # ======================================================
    st.subheader("🔗 Correlation Test (Multiple Variables)", divider='gray')

    # Get numeric columns, but exclude ID-like or irrelevant ones
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    exclude_cols = ['nik', 'tenure']  # add any others as needed
    numeric_cols = [c for c in numeric_cols if c.lower() not in [e.lower() for e in exclude_cols]]

    # Define satisfaction variables
    satisfaction_columns = [
        'SAT', 'NPS', 'EMO', 'average_kd', 'average_ki', 'average_kr',
        'average_pr', 'average_tu', 'average_ke'
    ]
    satisfaction_columns_item = [
        'SAT', 'NPS', 'EMO',
        'KD0', 'KD1', 'KD2', 'KD3', 'KE0', 'KE1', 'KE2', 'KE3',
        'KI0', 'KI1', 'KI2', 'KI3', 'KI4', 'KI5',
        'KR0', 'KR1', 'KR2', 'KR3', 'KR4', 'KR5',
        'PR0', 'PR1', 'PR2',
        'TU0', 'TU1', 'TU2', 'TU3'
    ]

    # Filter only existing columns
    satisfaction_columns = [c for c in satisfaction_columns if c in df.columns]
    satisfaction_columns_item = [c for c in satisfaction_columns_item if c in df.columns]

    if len(numeric_cols) < 2:
        st.warning("Not enough numeric columns for correlation test.")
    else:
        # Buttons to quickly fill multiselect
        col1, col2, col3 = st.columns(3)
        with col1:
            use_all_items = st.button("Select All Satisfaction Items")
        with col2:
            use_all_dimensions = st.button("Select All Dimensions")
        with col3:
            clear_selection = st.button("Clear Selection")

        # Initialize session state for persistent selection
        if "selected_vars" not in st.session_state:
            st.session_state.selected_vars = []

        # Handle button actions
        if use_all_items:
            st.session_state.selected_vars = satisfaction_columns_item
        elif use_all_dimensions:
            st.session_state.selected_vars = satisfaction_columns
        elif clear_selection:
            st.session_state.selected_vars = []

        # Multiselect always visible
        selected_vars = st.multiselect(
            "Select numeric variables to test correlation:",
            options=numeric_cols,
            default=st.session_state.selected_vars,
            key="corr_multiselect"
        )

        # --- Helper function for normality ---
        def check_normality(samples):
            if len(samples) < 5:
                return False
            _, p = stats.shapiro(samples)
            return p > 0.05

        # Run correlation
        if len(selected_vars) < 2:
            st.info("Please select at least two variables to calculate correlations.")
        else:
            # Pairwise correlation with automatic test selection
            st.markdown("### 🧪 Pairwise Correlation with Normality Check")
            results = []
            for i in range(len(selected_vars)):
                for j in range(i + 1, len(selected_vars)):
                    x = df[selected_vars[i]].dropna()
                    y = df[selected_vars[j]].dropna()
                    common_idx = x.index.intersection(y.index)
                    x, y = x.loc[common_idx], y.loc[common_idx]

                    if len(x) > 2:
                        normal_x, normal_y = check_normality(x), check_normality(y)
                        if normal_x and normal_y:
                            r, p = stats.pearsonr(x, y)
                            test_used = "Pearson"
                        else:
                            r, p = stats.spearmanr(x, y)
                            test_used = "Spearman"

                        results.append({
                            "Var1": selected_vars[i],
                            "Var2": selected_vars[j],
                            "Normal Var1": normal_x,
                            "Normal Var2": normal_y,
                            "Test Used": test_used,
                            "r": round(r, 3),
                            "p-value": round(p, 4),
                            "Significant (p<0.05)": "✅" if p < 0.05 else "–"
                        })

            st.dataframe(pd.DataFrame(results))

            # Correlation heatmap: show Pearson only if all selected vars are normal
            if all(check_normality(df[v].dropna()) for v in selected_vars):
                corr_matrix = df[selected_vars].corr(method='pearson').round(3)
                st.write("### 📊 Pearson Correlation Matrix")
            else:
                corr_matrix = df[selected_vars].corr(method='spearman').round(3)
                st.write("### 📊 Spearman Correlation Matrix (due to non-normality)")

            st.dataframe(corr_matrix)

            # Heatmap visualization
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                color_continuous_scale='RdBu_r',
                zmin=-1, zmax=1,
                title=f"Correlation Heatmap ({selected_year})"
            )
            st.plotly_chart(fig, use_container_width=True)

    # ======================================================
    # SECTION 2 — MEAN DIFFERENCE TEST (with normality check, group summary & effect size interpretation)
    # ======================================================
    st.subheader("📈 Mean Difference Test", divider='gray')

    # Exclude ID-like or irrelevant numeric columns
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    exclude_cols = ['nik', 'tenure', 'serial', 'id', 'employee_id']
    numeric_cols = [c for c in numeric_cols if c.lower() not in [e.lower() for e in exclude_cols]]

    # Get categorical columns for grouping
    group_cols = df.select_dtypes(exclude=np.number).columns.tolist() + ["tenure_category", "layer", "year"]
    group_cols = sorted(list(set(group_cols)))
    exclude_group_cols = ["admin_hr", "email", "name", "nik_short", "personnel_area", "position", "submit_date", ]  # ⬅️ Add any others you don’t want
    group_cols = [c for c in group_cols if c not in exclude_group_cols]

    if len(numeric_cols) == 0 or len(group_cols) == 0:
        st.warning("Not enough variables for mean difference test.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            numeric_var = st.selectbox("Select numeric variable:", numeric_cols)
        with col2:
            group_var = st.selectbox("Select grouping variable:", group_cols)

        if group_var == "year":
            years_selected = st.multiselect(
                "Select years to compare:",
                options=list(df_all.keys()),
                default=["2024", "2025"]
            )
            paired_test = st.checkbox("Paired test (same respondents across years)", value=False)
            df_clean = None
        else:
            available_groups = sorted(df[group_var].dropna().unique().tolist())
            selected_groups = st.multiselect(
                f"Select which {group_var} groups to include:",
                options=available_groups,
                default=[]
            )
            df_clean = df[df[group_var].isin(selected_groups)][[numeric_var, group_var]].dropna()

        # --- Helper functions ---
        def check_normality(samples):
            if len(samples) < 5:
                return False
            _, p = stats.shapiro(samples)
            return p > 0.05

        def cohen_d(x, y):
            return (np.mean(x) - np.mean(y)) / np.sqrt((np.std(x, ddof=1)**2 + np.std(y, ddof=1)**2)/2)

        def rank_biserial_r(stat, n1, n2=None, test_type="mannwhitney"):
            if test_type == "mannwhitney":
                U = stat
                mean_U = n1 * n2 / 2
                std_U = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
                z = (U - mean_U) / std_U
                r = z / np.sqrt(n1 + n2)
            else:
                W = stat
                n = n1
                mean_W = n*(n+1)/4
                std_W = np.sqrt(n*(n+1)*(2*n+1)/24)
                z = (W - mean_W) / std_W
                r = z / np.sqrt(n)
            return r

        def kruskal_eta_sq(H, k, n):
            return (H - k + 1) / (n - k)

        def interpret_effect_size(es, test_type="cohen"):
            if test_type == "cohen":
                if abs(es) < 0.2:
                    return "Negligible"
                elif abs(es) < 0.5:
                    return "Small"
                elif abs(es) < 0.8:
                    return "Medium"
                else:
                    return "Large"
            elif test_type == "r":
                if abs(es) < 0.1:
                    return "Negligible"
                elif abs(es) < 0.3:
                    return "Small"
                elif abs(es) < 0.5:
                    return "Medium"
                else:
                    return "Large"
            elif test_type == "eta":
                if es < 0.01:
                    return "Negligible"
                elif es < 0.06:
                    return "Small"
                elif es < 0.14:
                    return "Medium"
                else:
                    return "Large"
            return "Unknown"

        def summarize_groups(groups, labels):
            """Return a markdown table showing N, mean, std for each group."""
            table_md = "| Group | N | Mean | Std Dev |\n|---|---|---|---|\n"
            for g, label in zip(groups, labels):
                n = len(g)
                m = np.mean(g)
                s = np.std(g, ddof=1)
                table_md += f"| {label} | {n} | {m:.2f} | {s:.2f} |\n"
            return table_md

        # --- Run test ---
        if st.button("Run Mean Difference Test"):

            # --- Across years ---
            if group_var == "year" and len(years_selected) >= 2:
                df_combined = []
                for y in years_selected:
                    d = df_all[y][['year', 'nik', numeric_var]].copy()
                    d = d[d[numeric_var].notna()]
                    df_combined.append(d)
                df_combined = pd.concat(df_combined)

                st.write(f"**Comparing {numeric_var} between years: {', '.join(years_selected)}**")
                unique_years = sorted(df_combined['year'].unique())

                if len(unique_years) == 2:
                    y1, y2 = unique_years
                    data1 = df_combined[df_combined['year'] == y1][numeric_var]
                    data2 = df_combined[df_combined['year'] == y2][numeric_var]

                    normal1, normal2 = check_normality(data1), check_normality(data2)

                    # --- Paired or independent test ---
                    if paired_test:
                        merged = (
                            df_all[y1][['nik', numeric_var]].rename(columns={numeric_var: f"{numeric_var}_{y1}"})
                            .merge(df_all[y2][['nik', numeric_var]].rename(columns={numeric_var: f"{numeric_var}_{y2}"}), on="nik", how="inner")
                        )
                        data1, data2 = merged[f"{numeric_var}_{y1}"], merged[f"{numeric_var}_{y2}"]

                        if len(merged) < 5:
                            st.warning(f"Not enough overlapping respondents for paired test ({len(merged)} matched).")
                        else:
                            # Summary for paired respondents only
                            st.markdown(summarize_groups([data1, data2], [y1, y2]))

                            diff = data1 - data2
                            st.markdown(summarize_groups([diff], [f"{y1}-{y2} Difference"]))

                            if check_normality(diff):
                                t_stat, pval = stats.ttest_rel(data1, data2)
                                test_name = "Paired T-test"
                                effect_size = cohen_d(data1, data2)
                                es_type = "cohen"
                            else:
                                t_stat, pval = stats.wilcoxon(data1, data2)
                                test_name = "Wilcoxon Signed-Rank"
                                effect_size = rank_biserial_r(t_stat, len(data1), test_type="wilcoxon")
                                es_type = "r"

                            es_label = interpret_effect_size(effect_size, test_type=es_type)
                            st.markdown(f"**{test_name}:** stat = {t_stat:.3f}, p = {pval:.4f}, effect size = {effect_size:.3f} ({es_label})")
                            st.info("✅ Significant" if pval < 0.05 else "⚪ Not significant")
                    else:
                        # Independent test summary
                        st.markdown(summarize_groups([data1, data2], [y1, y2]))
                        if normal1 and normal2:
                            t_stat, pval = stats.ttest_ind(data1, data2, equal_var=False)
                            test_name = "Independent T-test"
                            effect_size = cohen_d(data1, data2)
                            es_type = "cohen"
                        else:
                            t_stat, pval = stats.mannwhitneyu(data1, data2)
                            test_name = "Mann–Whitney U test"
                            effect_size = rank_biserial_r(t_stat, len(data1), len(data2), test_type="mannwhitney")
                            es_type = "r"

                        es_label = interpret_effect_size(effect_size, test_type=es_type)
                        st.markdown(f"**{test_name}:** stat = {t_stat:.3f}, p = {pval:.4f}, effect size = {effect_size:.3f} ({es_label})")
                        st.info("✅ Significant" if pval < 0.05 else "⚪ Not significant")

            # --- Within one year (group_var != year) ---
            elif df_clean is not None and len(selected_groups) >= 2:
                data_groups = [df_clean[df_clean[group_var] == g][numeric_var] for g in selected_groups]
                st.markdown(summarize_groups(data_groups, selected_groups))
                normals = [check_normality(d) for d in data_groups]

                if len(selected_groups) == 2:
                    g1, g2 = selected_groups
                    if all(normals):
                        stat, pval = stats.ttest_ind(*data_groups, equal_var=False)
                        test_name = "Independent T-test"
                        effect_size = cohen_d(data_groups[0], data_groups[1])
                        es_type = "cohen"
                    else:
                        stat, pval = stats.mannwhitneyu(*data_groups)
                        test_name = "Mann–Whitney U test"
                        effect_size = rank_biserial_r(stat, len(data_groups[0]), len(data_groups[1]), test_type="mannwhitney")
                        es_type = "r"
                    es_label = interpret_effect_size(effect_size, test_type=es_type)
                    st.markdown(f"**{test_name} between {g1} and {g2}:** stat = {stat:.3f}, p = {pval:.4f}, effect size = {effect_size:.3f} ({es_label})")
                    st.info("✅ Significant" if pval < 0.05 else "⚪ Not significant")
                else:
                    normal_all = all(normals)
                    n_total = sum(len(g) for g in data_groups)
                    k = len(data_groups)
                    if normal_all:
                        f_stat, pval = stats.f_oneway(*data_groups)
                        test_name = "One-way ANOVA"
                        ss_between = sum(len(g)*(np.mean(g)-np.mean(df_clean[numeric_var]))**2 for g in data_groups)
                        ss_total = sum((val - np.mean(df_clean[numeric_var]))**2 for val in df_clean[numeric_var])
                        effect_size = ss_between / ss_total
                    else:
                        f_stat, pval = stats.kruskal(*data_groups)
                        test_name = "Kruskal–Wallis"
                        effect_size = kruskal_eta_sq(f_stat, k, n_total)
                    es_label = interpret_effect_size(effect_size, test_type="eta")
                    st.markdown(f"**{test_name} across {k} groups:** stat = {f_stat:.3f}, p = {pval:.4f}, effect size = {effect_size:.3f} ({es_label})")
                    st.info("✅ Significant difference" if pval < 0.05 else "⚪ No significant difference")

else:
    st.warning("You are not authenticated — please log in to view this page.")
