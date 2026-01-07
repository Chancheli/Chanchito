import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import time
import base64
from io import BytesIO
from PIL import Image

# --- ΡΥΘΜΙΣΗ ΚΩΔΙΚΟΥ ---
MASTER_PASSWORD = "γουρουνακια3" 

st.set_page_config(page_title="Chanchito Pro & Missu 🐷", layout="wide")

# --- CUSTOM CSS (Dark Mode Friendly) ---
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; border: 2px solid #ff4d6d; transition: all 0.3s; font-weight: bold; }
    .stButton>button:hover { background-color: #ff4d6d; color: white; transform: scale(1.05); }
    [data-testid="stSidebar"] { border-right: 2px solid #ff4d6d; }
    .stMetric { background-color: rgba(255, 77, 109, 0.1); padding: 15px; border-radius: 15px; border: 1px solid #ff4d6d; }
    h1, h2, h3 { color: #ff4d6d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Login")
    pwd_input = st.text_input("Κωδικός πρόσβασης:", type="password")
    if st.button("Είσοδος ✨"):
        if pwd_input == MASTER_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Λάθος κωδικός! 🐷")
    st.stop()

# --- DATABASE SETUP ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS entries 
             (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, 
              amount REAL, source_desc TEXT, date TEXT, receipt TEXT, is_shared INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals 
             (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS shopping_list 
             (id INTEGER PRIMARY KEY, item TEXT, store TEXT, added_by TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS common_products 
             (id INTEGER PRIMARY KEY, name TEXT, store TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reminders 
             (id INTEGER PRIMARY KEY, title TEXT, due_date TEXT, amount REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS missu_care 
             (id INTEGER PRIMARY KEY, action TEXT, date TEXT, notes TEXT)''')
conn.commit()

# --- HELPERS ---
def format_date_str(date_str):
    try: return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except: return date_str

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# Load Data
full_df = pd.read_sql_query("SELECT * FROM entries", conn)
if not full_df.empty:
    full_df['date_dt'] = pd.to_datetime(full_df['date'])

# --- MENU ---
menu_options = ["🏠 Αρχική", "💰 Έσοδα", "💸 Έξοδα", "🛒 Σούπερ Μάρκετ", "🐾 Missu Care", "🔔 Υπενθυμίσεις", "📜 Ιστορικό", "🎯 Στόχοι"]
choice = st.sidebar.selectbox("Μενού", menu_options)

# --- 1. ΑΡΧΙΚΗ ---
if choice == "🏠 Αρχική":
    st.title("¡Hola! 🐷✨")
    
    drange = st.selectbox("Διάστημα", ["Όλα", "Αυτός ο Μήνας", "Τελευταίες 30 μέρες"])
    df = full_df.copy()
    if not df.empty:
        if drange == "Αυτός ο Μήνας":
            df = df[df['date_dt'].dt.month == datetime.now().month]
        elif drange == "Τελευταίες 30 μέρες":
            df = df[df['date_dt'] >= (datetime.now() - timedelta(days=30))]

    # METRICS
    if not df.empty:
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Έσοδα", f"{t_inc:,.2f} €")
        c2.metric("Έξοδα", f"{t_exp:,.2f} €")
        c3.metric("Υπόλοιπο 🐷", f"{(t_inc - t_exp):,.2f} €")
    
    st.divider()
    
    # ALERTS
    col1, col2 = st.columns(2)
    today_s = str(datetime.now().date())
    next_w_s = str(datetime.now().date() + timedelta(days=7))
    with col1:
        st.subheader("🐾 Για τη Missu:")
        m_urg = c.execute("SELECT action, date FROM missu_care WHERE date >= ? AND date <= ?", (today_s, next_w_s)).fetchall()
        for a, d in m_urg: st.error(f"🦴 **{a}** ({format_date_str(d)})")
    with col2:
        st.subheader("⚠️ Λήγουν σύντομα:")
        b_urg = c.execute("SELECT title, due_date, amount FROM reminders WHERE due_date >= ? AND due_date <= ?", (today_s, next_w_s)).fetchall()
        for tb, db, ab in b_urg: st.warning(f"🧾 {tb}: {ab}€ ({format_date_str(db)})")

    st.divider()
    
    # DEBTS
    if not df.empty:
        shared = df[df['is_shared'] == 1]
        ais_paid = shared[shared['person'] == 'Άις']['amount'].sum() / 2
        kon_paid = shared[shared['person'] == 'Κωνσταντίνος']['amount'].sum() / 2
        st.subheader("📊 Εκκρεμότητες 🤝")
        if ais_paid > kon_paid: st.info(f"Ο Κωνσταντίνος χρωστάει στην Άις: **{(ais_paid - kon_paid):.2f} €**")
        elif kon_paid > ais_paid: st.info(f"Η Άις χρωστάει στον Κωνσταντίνο: **{(kon_paid - ais_paid):.2f} €**")
        else: st.success("✅ Είστε πάτσι! ❤️")

    st.divider()
    
    # REPORT
    st.subheader("📅 Αναφορά Εξόδων")
    exp_only = df[df['type'] == 'Expense'] if not df.empty else pd.DataFrame()
    if not exp_only.empty:
        exp_only['month_disp'] = exp_only['date_dt'].dt.strftime('%m/%Y')
        st.table(exp_only.groupby('month_disp')['amount'].sum().reset_index())
        st.bar_chart(data=exp_only.groupby('category')['amount'].sum())

# --- 2. ΕΣΟΔΑ ---
elif choice == "💰 Έσοδα":
    st.header("💰 Προσθήκη Εσόδου")
    with st.form("inc_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Κατηγορία", ["Μισθός", "Ενοίκιο", "Άλλο"])
        amt = st.number_input("Ποσό (€)", min_value=0.0)
        d_inc = st.date_input("Ημερομηνία", datetime.now())
        desc = st.text_input("Περιγραφή")
        if st.form_submit_button("Αποθήκευση ✨"):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(d_inc)))
            conn.commit(); st.balloons(); st.rerun()

# --- 3. ΕΞΟΔΑ ---
elif choice == "💸 Έξοδα":
    st.header("💸 Καταγραφή Εξόδου")
    with st.form("exp_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Κατηγορία", ["🐷 Αποταμίευση", "🐾 Missu", "🛒 Supermarket", "🍕 Φαγητό", "⚡ Λογαριασμοί", "🏠 Ενοίκιο", "🎬 Διασκέδαση", "🧸 Σπίτι", "💊 Υγεία", "🌈 Άλλο"])
        amt = st.number_input("Ποσό (€)", min_value=0.0)
        desc = st.text_input("Περιγραφή")
        sh = st.checkbox("
