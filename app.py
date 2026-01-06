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
    }
    .stButton>button {
        border-radius: 12px;
        transition: 0.3s;
        font-weight: bold;
    }
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
    }
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

# Load Animations
lottie_piggy = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_57pgbi7a.json")
lottie_success = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_pqnfmone.json")

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

# --- DATABASE SETUP ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, amount REAL, source_desc TEXT, date TEXT, receipt TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)")
c.execute("CREATE TABLE IF NOT EXISTS shopping_list (id INTEGER PRIMARY KEY, item TEXT, store TEXT, added_by TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS common_products (id INTEGER PRIMARY KEY, name TEXT, store TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, title TEXT, due_date TEXT, status TEXT)")
conn.commit()

# --- TRANSLATIONS ---
lang_choice = st.sidebar.radio("Language / Idioma", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇬🇧 English"])

t = {
    "🇬🇷 Ελληνικά": {
        "menu": ["Κεντρική", "Έσοδα", "Έξοδα", "🛒 Σούπερ Μάρκετ", "Ιστορικό", "🎯 Στόχοι", "🔔 Υπενθυμίσεις"],
        "income_title": "💰 Προσθήκη Εσόδου", "expense_title": "💸 Καταγραφή Εξόδου",
        "shopping_title": "🛒 Λίστα για Ψώνια", "history_title": "📜 Ιστορικό",
        "goals_title": "🎯 Στόχοι", "reminders_title": "🔔 Λογαριασμοί & Εκκρεμότητες",
        "amount": "Ποσό (€)", "desc": "Περιγραφή", "save": "Αποθήκευση",
        "person": "Ποιος;", "cat": "Κατηγορία", "store": "Κατάστημα",
        "goal_name": "Όνομα Στόχου", "goal_amt": "Ποσό Στόχου (€)",
        "export": "📥 Λήψη σε Excel", "monthly_report": "📅 Μηνιαία Αναφορά Εξόδων",
        "stats_title": "📊 Κατανομή Εξόδων", "date_range": "Χρονική Περίοδος",
        "from": "Από", "to": "Έως", "balance": "Υπόλοιπο", "month": "Μήνας", "total": "Σύνολο", "due": "Λήγει στις",
        "inc_cats": ["Μισθός", "Ενοίκιο", "Άλλο"],
        "exp_cats": ["🐾 Missu", "Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Άλλο"]
    },
    "🇪🇸 Español": {
        "menu": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "Historial", "🎯 Objetivos", "🔔 Recordatorios"],
        "income_title": "💰 Añadir Ingreso", "expense_title": "💸 Registrar Gasto",
        "shopping_title": "🛒 Lista de Compras", "history_title": "📜 Historial",
        "goals_title": "🎯 Objetivos", "reminders_title": "🔔 Recordatorios",
        "amount": "Cantidad (€)", "desc": "Descripción", "save": "Guardar",
        "person": "¿Quién?", "cat": "Categoría", "store": "Tienda",
        "goal_name": "Nombre", "goal_amt": "Meta (€)",
        "export": "📥 Descargar Excel", "monthly_report": "📅 Informe Mensual",
        "stats_title": "📊 Distribución", "date_range": "Rango",
        "from": "Desde", "to": "Hasta", "balance": "Saldo", "month": "Mes", "total": "Total", "due": "Vence",
        "inc_cats": ["Salario", "Alquiler", "Otro"],
        "exp_cats": ["🐾 Missu", "Supermercado", "Comida", "Facturas", "Alquiler", "Otro"]
    },
    "🇬🇧 English": {
        "menu": ["Dashboard", "Income", "Expenses", "🛒 Shopping", "History", "🎯 Goals", "🔔 Reminders"],
        "income_title": "💰 Add Income", "expense_title": "💸 Add Expense",
        "shopping_title": "🛒 Shopping List", "history_title": "📜 History",
        "goals_title": "🎯 Goals", "reminders_title": "🔔 Reminders",
        "amount": "Amount (€)", "desc": "Description", "save": "Save",
        "person": "Who?", "cat": "Category", "store": "Store",
        "goal_name": "Goal Name", "goal_amt": "Target (€)",
        "export": "📥 Excel", "monthly_report": "📅 Monthly Report",
        "stats_title": "📊 Stats", "date_range": "Range",
        "from": "From", "to": "To", "balance": "Balance", "month": "Month", "total": "Total", "due": "Due",
        "inc_cats": ["Salary", "Rent", "Other"],
        "exp_cats": ["🐾 Missu", "Market", "Food", "Bills", "Rent", "Other"]
    }
}

curr_t = t[lang_choice]

# Sidebar
st.sidebar.divider()
st.sidebar.write(f"🔍 **{curr_t['date_range']}**")
d_from = st.sidebar.date_input(curr_t["from"], value=date(2026, 1, 1))
d_to = st.sidebar.date_input(curr_t["to"], value=date.today())
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
    col_pig, col_tit = st.columns([1, 4])
    with col_pig: st_lottie(lottie_piggy, height=100)
    with col_tit: st.title(choice)
    
    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'])
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><p style="color:#4CAF50">➕ {curr_t["menu"][1]}</p><h2>{t_inc:,.2f} €</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><p style="color:#FF5252">➖ {curr_t["menu"][2]}</p><h2>{t_exp:,.2f} €</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><p style="color:#2196F3">💎 {curr_t["balance"]}</p><h2>{(t_inc - t_exp):,.2f} €</h2></div>', unsafe_allow_html=True)
        
        st.divider()
        exp_df = df[df['type'] == 'Expense']
        if not exp_df.empty:
            st.subheader(curr_t["stats_title"])
            fig = px.pie(exp_df, values='amount', names='category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader(curr_t["monthly_report"])
            exp_df['month_key'] = pd.to_datetime(exp_df['date']).dt.strftime('%Y-%m')
            summary = exp_df.groupby('month_key')['amount'].sum().reset_index()
            summary.columns = [curr_t['month'], curr_t['total']]
            st.dataframe(summary, use_container_width=True, hide_index=True)

        st.download_button(label=curr_t["export"], data=to_excel(df), file_name=f"chanchito.xlsx")
    else:
        st.info("No data yet.")

# --- 2. INCOME ---
elif choice == curr_t["menu"][1]:
    st.header(curr_t["income_title"])
    with st.form("inc_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["inc_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input(curr_t["desc"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)", ("Income", p, cat, amt, desc, str(date.today())))
            conn.commit()
            st_lottie(lottie_success, height=150)
            st.balloons()
            time.sleep(1.5); st.rerun()

# --- 3. EXPENSES ---
elif choice == curr_t["menu"][2]:
    st.header(curr_t["expense_title"])
    with st.form("exp_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["exp_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input(curr_t["desc"])
        up = st.file_uploader("Receipt", type=['jpg', 'jpeg', 'png'])
        if st.form_submit_button(curr_t["save"]):
            img_s = ""
            if up:
                img = Image.open(up).convert('RGB')
                img.thumbnail((400, 400))
                img_s = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt) VALUES (?,?,?,?,?,?,?)", ("Expense", p, cat, amt, desc, str(date.today()), img_s))
            conn.commit(); st.success("OK!"); time.sleep(0.5); st.rerun()

# --- 4. SHOPPING ---
elif choice == curr_t["menu"][3]:
    st.header(curr_t["shopping_title"])
    c_l, c_s = st.columns(2)
    with c_l:
        st.write("🏬 **Lidl**")
        for i_id, i_n in c.execute("SELECT id, name FROM common_products WHERE store='Lidl'").fetchall():
            if st.button(f"➕ {i_n}", key=f"l_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (i_n, "Lidl"))
                conn.commit(); st.rerun()
    with c_s:
        st.write("🏬 **Σκλαβενίτης**")
        for i_id, i_n in c.execute("SELECT id, name FROM common_products WHERE store='Σκλαβενίτης'").fetchall():
            if st.button(f"➕ {i_n}", key=f"s_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (i_n, "Σκλαβενίτης"))
                conn.commit(); st.rerun()
    st.divider()
    for sid, itm, sto in c.execute("SELECT id, item, store FROM shopping_list").fetchall():
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"🛒 **{itm}** ({sto})")
        if col2.button("✅", key=f"done_{sid}"):
            c.execute("DELETE FROM shopping_list WHERE id=?", (sid,))
            conn.commit(); st.rerun()
    with st.expander("Settings"):
        with st.form("set_sh"):
            n_itm, s_sto = st.text_input("Item"), st.selectbox("Store", ["Lidl", "Σκλαβενίτης"])
            if st.form_submit_button("Add Quick Item"):
                c.execute("INSERT INTO common_products (name, store) VALUES (?,?)", (n_itm, s_sto))
                conn.commit(); st.rerun()

# --- 5. HISTORY ---
elif choice == curr_t["menu"][4]:
    st.header(curr_t["history_title"])
    for idx, r in df.sort_values('id', ascending=False).iterrows():
        with st.expander(f"{r['date']} | {r['amount']:.2f}€ | {r['category']}"):
            if r['receipt']: st.image(base64.b64decode(r['receipt']))
            if st.button("🗑️", key=f"del_{r['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (r['id'],))
                conn.commit(); st.rerun()

# --- 6. GOALS ---
elif choice == curr_t["menu"][5]:
    st.header(curr_t["goals_title"])
    with st.form("goal_f"):
        gn, ga = st.text_input(curr_t["goal_name"]), st.number_input(curr_t["goal_amt"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (gn, ga))
            conn.commit(); st.rerun()
    st.divider()
    all_inc = df_raw[df_raw['type'] == 'Income']['amount'].sum()
    all_exp = df_raw[df_raw['type'] == 'Expense']['amount'].sum()
    sav = all_inc - all_exp
    for gid, gn, gt in c.execute("SELECT * FROM goals").fetchall():
        pr = min(sav / gt, 1.0) if gt > 0 else 0
        st.write(f"**{gn}** ({sav:,.2f} / {gt:,.2f} €)")
        st.progress(pr)
        if st.button(f"🗑️", key=f"dg_{gid}"):
            c.execute("DELETE FROM goals WHERE id=?", (gid,)); conn.commit(); st.rerun()

# --- 7. REMINDERS ---
elif choice == curr_t["menu"][6]:
    st.header(curr_t["reminders_title"])
    with st.form("rem_f"):
        rt, rd = st.text_input(curr_t["desc"]), st.date_input(curr_t["due"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO reminders (title, due_date, status) VALUES (?,?,?)", (rt, str(rd), "Pending"))
            conn.commit(); st.rerun()
    st.divider()
    for rid, rit, rid_d, ris in c.execute("SELECT * FROM reminders ORDER BY due_date ASC").fetchall():
        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        c1.write(f"🔔 **{rit}** - {rid_d}")
        c2.write("🔴" if ris == "Pending" else "🟢")
        if c3.button("✅", key=f"r_{rid}"):
            c.execute("UPDATE reminders SET status='Paid' WHERE id=?", (rid,))
            conn.commit(); st.rerun()
        if c3.button("🗑️", key=f"dr_{rid}"):
            c.execute("DELETE FROM reminders WHERE id=?", (rid,))
            conn.commit(); st.rerun()
