import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml

# Fetch data

@st.cache_resource()
def fetch_data_survey25():
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('ES25 - Combined Data')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df_survey25 = pd.DataFrame(data)
    return df_survey25

@st.cache_resource()
def fetch_data_survey24():
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('ES24 - Combined Data')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df_survey24 = pd.DataFrame(data)
    return df_survey24

@st.cache_resource()
def fetch_data_survey23():
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('ES23 - Combined Data')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df_survey23 = pd.DataFrame(data)
    return df_survey23

@st.cache_resource()
def fetch_data_creds():
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Dashboard Credentials')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df_creds = pd.DataFrame(data)
    return df_creds
