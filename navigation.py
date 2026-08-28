import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
import pandas as pd


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")

    return pages[ctx.page_script_hash]["page_name"]


def make_sidebar():
    with st.sidebar:
        st.title(":blue_heart: KG Survey Result")
        
        # Display authenticated user identity from session_state safely
        user_email = st.session_state.get("user_email", "Guest User")
        st.caption(f"Logged in as:\n**{user_email}**")
        st.write("")
        st.write("")

        if st.session_state.get("logged_in", False):
            st.page_link("pages/page1.py", label="Demography", icon="🌎")
            st.page_link("pages/page2.py", label="Mood Meter", icon="😊")
            st.page_link("pages/page3.py", label="Satisfaction", icon="👍")
            st.page_link("pages/page4.py", label="NPS", icon="🗣️")
            st.page_link("pages/page5.py", label="Categorization", icon="🤝")
            st.page_link("pages/page6.py", label="Stats Tools", icon="📊")
            st.page_link("pages/page7.py", label="Gallup Index", icon="🧑‍🔬")
            st.page_link("pages/page8.py", label="IPA", icon="📕")

            st.write("")
            st.write("")

            if st.button("Log out"):
                logout()

        elif get_current_page_name() != "streamlit_app":
            # Redirect unauthenticated page access to main script
            st.switch_page("streamlit_app.py")


def logout():
    st.session_state.logged_in = False
    st.info("Logged out successfully!")
    sleep(0.5)
    st.switch_page("streamlit_app.py")


def make_filter(columns_list, df_survey, combined_df):
    filter_columns = st.multiselect(
        'Filter the data (optional):',
        options=columns_list,
        format_func=lambda x: x.capitalize()
    )

    if 'layer' in filter_columns:
        st.write(""" 
        - **Group 1** = Pelaksana  
        - **Group 1 Str Layer 5** = Team Leader  
        - **Group 2** = Professional setara Officer  
        - **Group 2 Str Layer 4** = Superintendent  
        - **Group 3** = Professional setara Manager (Specialist / Senior Officer)  
        - **Group 3 Str Layer 3A** = Manager  
        - **Group 3 Str Layer 3B** = Senior Manager  
        - **Group 4** = Professional setara GM (Advisor)  
        - **Group 4 Str Layer 2** = GM / Senior GM / Vice GM / Deputy GM / Vice Rector  
        - **Group 5** = Professional setara Director (Consultant)  
        - **Group 5 Str Layer 1** = CEO / Director / Vice Director / Deputy Director / Vice President / Assistant Vice President / Rector
        """)

    selected_filters = {}
    filtered_data, filtered_combined = df_survey.copy(), combined_df.copy()

    for filter_col in filter_columns:
        selected_filter_value = st.multiselect(
            f'Select {filter_col.capitalize()} to filter the data:',
            options=filtered_data[filter_col].dropna().unique(),
            key=f'filter_{filter_col}'
        )
        
        if selected_filter_value:
            filtered_data = filtered_data[filtered_data[filter_col].isin(selected_filter_value)]
            filtered_combined = filtered_combined[filtered_combined[filter_col].isin(selected_filter_value)]
            selected_filters[filter_col] = selected_filter_value

    if filtered_data.shape[0] <= 1 or filtered_combined.shape[0] <= 1:
        st.write("Data is unavailable to protect confidentiality.")
        return pd.DataFrame(), pd.DataFrame(), {}

    return filtered_data, filtered_combined, selected_filters