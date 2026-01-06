import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import time
import base64
import json
from io import BytesIO
from PIL import Image
import plotly.express as px
from streamlit_lottie import st_lottie

# --- ΡΥΘΜΙΣΗ ΚΩΔΙΚΟΥ ---
MASTER_PASSWORD = "γουρουνακια3" 

st.set_page_config(page_title="Chanchito Pro & Missu", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-label { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
    .metric-value { font-size: 28px; font-weight: bold; }
    .stButton>button { border-radius: 12px; font-weight: bold; width: 100%; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Entries')
    writer.close()
    return output.getvalue()

# --- DATABASE SETUP ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, amount REAL, source_desc TEXT, date TEXT, receipt TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)")
c.execute("CREATE TABLE IF NOT EXISTS shopping_list (id INTEGER PRIMARY KEY, item TEXT, store TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS common_products (id INTEGER PRIMARY KEY, name TEXT, store TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, title TEXT, due_date TEXT, status TEXT)")
conn.commit()

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Login")
    pwd_input = st.text_input("Password:", type="password")
    if st.button("Enter"):
        if pwd_input == MASTER_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Wrong password!")
    st.stop()

# --- TRANSLATIONS ---
lang_choice = st.sidebar.radio("Language", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇬Β English"])
t = {
    "🇬🇷 Ελληνικά": {
        "menu": ["Κεντρική", "Έσοδα", "Έξοδα", "🛒 Σούπερ Μάρκετ", "Ιστορικό", "🎯 Στόχοι", "🔔 Υπενθυμίσεις"],
        "income": "Έσοδα", "expense": "Έξοδα", "balance": "Υπόλοιπο", "report": "📅 Μηνιαία Αναφορά",
        "month": "Μήνας", "total": "Σύνολο", "save": "Αποθήκευση"
    },
    "🇪🇸 Español": {
        "menu": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "Historial", "🎯 Objetivos", "🔔 Recordatorios"],
        "income": "Ingresos", "expense": "Gastos", "balance": "Saldo", "report": "📅 Mensual",
        "month": "Mes", "total": "Total", "save": "Guardar"
    },
    "🇬Β English": {
        "menu": ["Dashboard", "Income", "Expenses", "🛒 Shopping
