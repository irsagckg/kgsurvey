import streamlit as st
from navigation import make_sidebar
from data_processing import finalize_data
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title='Survey Result',
    page_icon=':blue_heart:',
)

# Fetch data source credentials and survey data
df_survey25, df_survey24, df_survey23, df_creds = finalize_data()

# -----------------------------------------------------------------------------
# PRIVATE APP AUTHENTICATION VERIFICATION (CLOUD + LOCAL DEV FALLBACK)
# -----------------------------------------------------------------------------
def get_authenticated_user_email():
    # 1. Check Streamlit Cloud native st.user identity object
    if hasattr(st, "user") and hasattr(st.user, "email") and st.user.email:
        return st.user.email
    # 2. Check newer Streamlit st.context API if present
    elif hasattr(st, "context") and hasattr(st.context, "user") and getattr(st.context.user, "email", None):
        return st.context.user.email
    # 3. Local development fallback via secrets.toml
    elif st.secrets.get("LOCAL_DEV", False):
        return st.secrets.get("DEV_USER_EMAIL", df_creds['email'].iloc[0] if not df_creds.empty else None)
    return None

user_email = get_authenticated_user_email()

if not user_email:
    st.error("🔒 Access Denied. This is a private application. Please access it via your workspace account.")
    st.stop()

# Match authenticated workspace email to authorization dictionary (df_creds)
if user_email in df_creds['email'].values:
    user_row = df_creds[df_creds['email'] == user_email].iloc[0]
    
    # Store authenticated session variables
    st.session_state['logged_in'] = True
    st.session_state['user_email'] = user_email
    st.session_state['username'] = user_row['username']
    st.session_state['user_name'] = user_row['name']
    
    # Render navigation sidebar
    make_sidebar()

    st.subheader('KG Employee Survey Dashboard', divider='gray')
    st.success(f"Logged in successfully! Welcome, {user_row['name']}.")

    # -------------------------------------------------------------------------
    # ACCESS LOGGING (GOOGLE SHEETS INTEGRATION)
    # -------------------------------------------------------------------------
    def log_user_access(email):
        access_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["sheets"], scope)
            client = gspread.authorize(creds)
            spreadsheet_id = "1qUZaGkwv7Shx3gDnSQNdYFOjuqmVtRUEgKzdrBrsovM"
            sheet = client.open_by_key(spreadsheet_id).sheet1
            sheet.append_row([email, access_time])
        except gspread.SpreadsheetNotFound:
            st.write("Spreadsheet not found. Please check the ID and permissions.")
        except Exception as e:
            st.write(f"An error occurred: {e}")

    # Trigger user access log once per session
    if not st.session_state.get('logged_to_sheets', False):
        log_user_access(user_email)
        st.session_state['logged_to_sheets'] = True

else:
    st.error(f"❌ Account Unauthorized: The email address '{user_email}' is not listed in the credentials database.")
    st.stop()