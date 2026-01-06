import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import time
import base64
import requests
from io import BytesIO
from PIL import Image
import plotly.express as px
from streamlit_lottie import st_lottie

# --- ΡΥΘΜΙΣΗ ΚΩΔΙΚΟΥ ---
MASTER_PASSWORD = "γουρουνακια3" 

st.set_page_config(page_title="Chanchito Pro & Missu", layout="wide")

# --- CUSTOM CSS ΓΙΑ PREMIUM LOOK ---
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
    .stButton>button { border-radius: 12px; transition: 0.3s; font-weight: bold; width: 100%; height: 3em; }
    .stDataFrame { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

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

# Load Animations (Updated URLs)
lottie_piggy = load_lottieurl("https://lottie.host/808f9037-3705-4752-9721-3f8d394e246a/v9o3p3E59k.json") 
lottie_success = load_lottieurl("https://lottie.host/c5c16265-d0c3-4f90-8451-8e01933f728c/7VnS5vO9fB.json")

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

# --- DATABASE ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, amount REAL, source_desc TEXT, date TEXT, receipt TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)")
c.execute("CREATE TABLE IF NOT EXISTS shopping_list (id INTEGER PRIMARY KEY, item TEXT, store TEXT, added_by TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS common_products (id INTEGER PRIMARY KEY, name TEXT, store TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, title TEXT, due_date TEXT, status TEXT)")
conn.commit()

# --- TRANSLATIONS ---
lang_choice = st.sidebar.radio("Language / Idioma", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇬Β English"])
t = {
    "🇬🇷 Ελληνικά": {
        "menu": ["Κεντρική", "Έσοδα", "Έξοδα", "🛒 Σούπερ Μάρκετ", "Ιστορικό", "🎯 Στόχοι", "🔔 Υπενθυμίσεις"],
        "income": "Έσοδα", "expense": "Έξοδα", "balance": "Υπόλοιπο", "report": "📅 Μηνιαία Αναφορά Εξόδων",
        "month": "Μήνας", "total": "Σύνολο", "save": "Αποθήκευση", "person": "Ποιος;", "cat": "Κατηγορία", "amount": "Ποσό (€)",
        "inc_cats": ["Μισθός", "Ενοίκιο", "Άλλο"],
        "exp_cats": ["🐾 Missu", "Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Άλλο"]
    },
    "🇪🇸 Español": {
        "menu": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "Historial", "🎯 Objetivos", "🔔 Recordatorios"],
        "income": "Ingresos", "expense": "Gastos", "balance": "Saldo", "report": "📅 Informe Mensual",
        "month": "Mes", "total": "Total", "save": "Guardar", "person": "¿Quién?", "cat": "Categoría", "amount": "Cantidad (€)",
        "inc_cats": ["Salario", "Alquiler", "Otro"],
        "exp_cats": ["🐾 Missu", "Supermercado", "Comida", "Facturas", "Hogar", "Salud", "Otro"]
    },
    "🇬Β English": {
        "menu": ["Dashboard", "Income", "Expenses", "🛒 Shopping", "History", "🎯 Goals", "🔔 Reminders"],
        "income": "Income", "expense": "Expenses", "balance": "Balance", "report": "📅 Monthly Report",
        "month": "Month", "total": "Total", "save": "Save", "person": "Who?", "cat": "Category", "amount": "Amount (€)",
        "inc_cats": ["Salary", "Rent", "Other"],
        "exp_cats": ["🐾 Missu", "Market", "Food", "Bills", "Home", "Health", "Other"]
    }
}
curr_t = t[lang_choice]

# Sidebar
st.sidebar.divider()
d_from = st.sidebar.date_input("From / Από", value=date(2026, 1, 1))
d_to = st.sidebar.date_input("To / Έως", value=date.today())
choice = st.sidebar.selectbox("Menu", curr_t["menu"])

# Data
df_raw = pd.read_sql_query("SELECT * FROM entries", conn)
if not df_raw.empty:
    df_raw['date_dt'] = pd.to_datetime(df_raw['date']).dt.date
    df = df_raw[(df_raw['date_dt'] >= d_from) & (df_raw['date_dt'] <= d_to)].copy()
else:
    df = df_raw.copy()

# --- 1. DASHBOARD ---
if choice in ["Κεντρική", "Panel", "Dashboard"]:
    col1, col2 = st.columns([1, 4])
    with col1:
        if lottie_piggy: st_lottie(lottie_piggy, height=120, key="piggy")
    with col2:
        st.title(choice)
    
    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'])
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-label" style="color:#4CAF50">➕ {curr_t["income"]}</div><div class="metric-value">{t_inc:,.2f} €</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-label" style="color:#FF5252">➖ {curr_t["expense"]}</div><div class="metric-value">{t_exp:,.2f} €</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-label" style="color:#2196F3">💎 {curr_t["balance"]}</div><div class="metric-value">{(t_inc - t_exp):,.2f} €</div></div>', unsafe_allow_html=True)
        
        st.divider()
        exp_df = df[df['type'] == 'Expense'].copy()
        if not exp_df.empty:
            # Monthly Report Table
            st.subheader(curr_t["report"])
            exp_df['month_key'] = pd.to_datetime(exp_df['date']).dt.strftime('%Y-%m')
            summary = exp_df.groupby('month_key')['amount'].sum().reset_index()
            summary.columns = [curr_t['month'], curr_t['total']]
            st.dataframe(summary, use_container_width=True, hide_index=True)
            
            st.divider()
            # Distribution Chart
            fig = px.pie(exp_df, values='amount', names='category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
            
        st.download_button("📥 Excel", data=to_excel(df), file_name="finances.xlsx")
    else:
        st.info("No data available.")

# --- 2. INCOME ---
elif choice == curr_t["menu"][1]:
    st.header(curr_t["menu"][1])
    with st.form("inc_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["inc_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input("Περιγραφή / Desc")
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)", ("Income", p, cat, amt, desc, str(date.today())))
            conn.commit()
            if lottie_success: st_lottie(lottie_success, height=200, key="success_inc")
            st.balloons()
            time.sleep(1.5); st.rerun()

# --- 3. EXPENSES ---
elif choice == curr_t["menu"][2]:
    st.header(curr_t["menu"][2])
    with st.form("exp_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["exp_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input("Περιγραφή / Desc")
        up = st.file_uploader("Receipt", type=['jpg', 'png'])
        if st.form_submit_button(curr_t["save"]):
            img_s = ""
            if up:
                img = Image.open(up).convert('RGB'); img.thumbnail((400, 400))
                img_s = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt) VALUES (?,?,?,?,?,?,?)", ("Expense", p, cat, amt, desc, str(date.today()), img_s))
            conn.commit(); st.success("Saved!"); time.sleep(0.5); st.rerun()

# --- 4. SHOPPING ---
elif choice == curr_t["menu"][3]:
    st.header(curr_t["menu"][3])
    c_l, c_s = st.columns(2)
    with c_l:
        st.write("🏬 **Lidl**")
        for i_id, i_n in c.execute("SELECT id, name FROM common_products WHERE store='Lidl'").fetchall():
            if st.button(f"➕ {i_n}", key=f"l_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (i_n, "Lidl")); conn.commit(); st.rerun()
    with c_s:
        st.write("🏬 **Σκλαβενίτης**")
        for i_id, i_n in c.execute("SELECT id, name FROM common_products WHERE store='Σκλαβενίτης'").fetchall():
            if st.button(f"➕ {i_n}", key=f"s_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (i_n, "Σκλαβενίτης")); conn.commit(); st.rerun()
    st.divider()
    for sid, itm, sto in c.execute("SELECT id, item, store FROM shopping_list").fetchall():
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"🛒 **{itm}** ({sto})")
        if col2.button("✅", key=f"d_{sid}"):
            c.execute("DELETE FROM shopping_list WHERE id=?", (sid,)); conn.commit(); st.rerun()
    with st.expander("Add Quick Items"):
        with st.form("q_add"):
            n, s = st.text_input("Name"), st.selectbox("Store", ["Lidl", "Σκλαβενίτης"])
            if st.form_submit_button("Add"):
                c.execute("INSERT INTO common_products (name, store) VALUES (?,?)", (n, s)); conn.commit(); st.rerun()

# --- 5. HISTORY ---
elif choice == curr_t["menu"][4]:
    st.header(curr_t["menu"][4])
    for idx, r in df.sort_values('id', ascending=False).iterrows():
        with st.expander(f"{r['date']} | {r['amount']}€ | {r['category']}"):
            if r['receipt']: st.image(base64.b64decode(r['receipt']))
            if st.button("🗑️", key=f"del_{r['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

# --- 6. GOALS ---
elif choice == curr_t["menu"][5]:
    st.header(curr_t["menu"][5])
    with st.form("g_f"):
        gn, ga = st.text_input("Goal Name"), st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Add Goal"):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (gn, ga)); conn.commit(); st.rerun()
    sav = df_raw[df_raw['type'] == 'Income']['amount'].sum() - df_raw[df_raw['type'] == 'Expense']['amount'].sum()
    for gid, gn, gt in c.execute("SELECT * FROM goals").fetchall():
        st.write(f"**{gn}** ({sav:,.2f}/{gt:,.2f}€)")
        st.progress(min(sav/gt, 1
