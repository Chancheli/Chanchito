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

# --- CUSTOM CSS ΓΙΑ APP LOOK ---
st.markdown("""
    <style>
    /* Γενικό στυλ για κάρτες (Glassmorphism) */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    /* Στρογγυλεμένα κουμπιά */
    .stButton>button {
        border-radius: 10px;
        transition: 0.3s;
    }
    /* Τίτλοι */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

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
lottie_piggy = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_57pgbi7a.json") # Piggy bank
lottie_success = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_pqnfmone.json") # Success check

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
c.execute('''CREATE TABLE IF NOT EXISTS entries 
             (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, 
              amount REAL, source_desc TEXT, date TEXT, receipt TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals 
             (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS shopping_list 
             (id INTEGER PRIMARY KEY, item TEXT, store TEXT, added_by TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS common_products 
             (id INTEGER PRIMARY KEY, name TEXT, store TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reminders 
             (id INTEGER PRIMARY KEY, title TEXT, due_date TEXT, status TEXT)''')
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
        "add_goal": "Προσθήκη Νέου Στόχου", "goal_name": "Όνομα Στόχου", "goal_amt": "Ποσό Στόχου (€)",
        "quick_add": "⚡ Γρήγορη Προσθήκη", "export": "📥 Λήψη σε Excel",
        "monthly_report": "📅 Μηνιαία Αναφορά Εξόδων", "stats_title": "📊 Κατανομή Εξόδων",
        "date_range": "Χρονική Περίοδος", "from": "Από", "to": "Έως",
        "balance": "Υπόλοιπο", "month": "Μήνας", "total": "Σύνολο", "due": "Λήγει στις",
        "inc_cats": ["Μισθός", "Ενοίκιο", "Άλλο"],
        "exp_cats": ["🐾 Missu", "Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Άλλο"]
    },
    "🇪🇸 Español": {
        "menu": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "Historial", "🎯 Objetivos", "🔔 Recordatorios"],
        "income_title": "💰 Añadir Ingreso", "expense_title": "💸 Registrar Gasto",
        "shopping_title": "🛒 Lista de Compras", "history_title": "📜 Historial",
        "goals_title": "🎯 Objetivos", "reminders_title": "🔔 Recordatorios y Facturas",
        "amount": "Cantidad (€)", "desc": "Descripción", "save": "Guardar",
        "person": "¿Quién?", "cat": "Categoría", "store": "Tienda",
        "add_goal": "Añadir Nuevo Objetivo", "goal_name": "Nombre del Objetivo", "goal_amt": "Cantidad Meta (€)",
        "quick_add": "⚡ Añadir Rápido", "export": "📥 Descargar Excel",
        "monthly_report": "📅 Informe Mensual", "stats_title": "📊 Distribución de Gastos",
        "date_range": "Rango de Fechas", "from": "Desde", "to": "Hasta",
        "balance": "Saldo", "month": "Mes", "total": "Total", "due": "Vence el",
        "inc_cats": ["Salario", "Alquiler", "Otro"],
        "exp_cats": ["🐾 Missu", "Supermercado", "Comida", "Facturas", "Alquiler", "Entretenimiento", "Hogar", "Salud", "Otro"]
    },
    "🇬🇧 English": {
        "menu": ["Dashboard", "Income", "Expenses", "🛒 Shopping List", "History", "🎯 Goals", "🔔 Reminders"],
        "income_title": "💰 Add Income", "expense_title": "💸 Record Expense",
        "shopping_title": "🛒 Shopping List", "history_title": "📜 History",
        "goals_title": "🎯 Goals", "reminders_title": "🔔 Reminders & Bills",
        "amount": "Amount (€)", "desc": "Description", "save": "Save",
        "person": "Who?", "cat": "Category", "store": "Store",
        "add_goal": "Add New Goal", "goal_name": "Goal Name", "goal_amt": "Target Amount (€)",
        "quick_add": "⚡ Quick Add", "export": "📥 Download Excel",
        "monthly_report": "📅 Monthly Summary", "stats_title": "📊 Expense Distribution",
        "date_range": "Date Range", "from": "From", "to": "To",
        "balance": "Balance", "month": "Month", "total": "Total", "due": "Due on",
        "inc_cats": ["Salary", "Rent", "Other"],
        "exp_cats": ["🐾 Missu", "Supermarket", "Food", "Bills", "Rent", "Entertainment", "Home", "Health", "Other"]
    }
}

curr_t = t[lang_choice]

# --- SIDEBAR FILTERS ---
st.sidebar.divider()
st.sidebar.write(f"🔍 **{curr_t['date_range']}**")
d_from = st.sidebar.date_input(curr_t["from"], value=date(2026, 1, 1))
d_to = st.sidebar.date_input(curr_t["to"], value=date.today())

choice = st.sidebar.selectbox("Menu", curr_t["menu"])

# Data Loading
df_raw = pd.read_sql_query("SELECT * FROM entries", conn)
if not df_raw.empty:
    df_raw['date_dt'] = pd.to_datetime(df_raw['date']).dt.date
    df = df_raw[(df_raw['date_dt'] >= d_from) & (df_raw['date_dt'] <= d_to)].copy()
else:
    df = df_raw.copy()

# --- 1. DASHBOARD ---
if choice in ["Κεντρική", "Panel", "Dashboard"]:
    st_lottie(lottie_piggy, height=150, key="piggy")
    st.title(choice)
    
    # Reminders Alert
    pending = c.execute("SELECT title, due_date FROM reminders WHERE status='Pending'").fetchall()
    for tit, d_date in pending:
        if datetime.strptime(d_date, '%Y-%m-%d').date() <= date.today():
            st.error(f"⚠️ {tit} ({d_date})")

    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'])
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        
        # UI CARDS
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><p style="color:#4CAF50">{curr_t["menu"][1]}</p><h2>{t_inc:,.2f} €</h2></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><p style="color:#FF5252">{curr_t["menu"][2]}</p><h2>{t_exp:,.2f} €</h2></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><p style="color:#2196F3">{curr_t["balance"]}</p><h2>{(t_inc - t_exp):,.2f} €</h2></div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Chart
        exp_df = df[df['type'] == 'Expense']
        if not exp_df.empty:
            st.subheader(curr_t["stats_title"])
            fig = px.pie(exp_df, values='amount', names='category', hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Monthly Report Clean Table
        st.subheader(curr_t["monthly_report"])
        if not exp_df.empty:
            exp_df['month_key'] = pd.to_datetime(exp_df['date']).dt.strftime('%Y-%m')
            summary = exp_df.groupby('month_key')['amount'].sum().reset_index()
            summary.columns = [curr_t['month'], curr_t['total']]
            st.dataframe(summary, use_container_width=True, hide_index=True)

        st.download_button(label=curr_t["export"], data=to_excel(df), file_name=f"chanchito_{d_from}_{d_to}.xlsx")
    else:
        st.info("No data available.")

# --- 2. INCOME ---
elif choice == curr_t["menu"][1]:
    st.header(curr_t["income_title"])
    with st.form("inc_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["inc_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input(curr_t["desc"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            st_lottie(lottie_success, height=200) # SUCCESS ANIMATION!
            st.balloons() # BALLOONS!
            time.sleep(2)
            st.rerun()

# --- 3. EXPENSES ---
elif choice == curr_t["menu"][2]:
    st.header(curr_t["expense_title"])
    with st.form("exp_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["exp_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input(curr_t["desc"])
        uploaded_file = st.file_uploader("Receipt Photo", type=['jpg', 'jpeg', 'png'])
        if st.form_submit_button(curr_t["save"]):
            img_str = ""
            if uploaded_file:
                img = Image.open(uploaded_file).convert('RGB')
                img.thumbnail((400, 400))
                img_str = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt) VALUES (?,?,?,?,?,?,?)",
                      ("Expense", p, cat, amt, desc, str(datetime.now().date()), img_str))
            conn.commit(); st.success("OK!"); time.sleep(0.5); st.rerun()

# --- 4. SHOPPING LIST ---
elif choice == curr_t["menu"][3]:
    st.header(curr_t["shopping_title"])
    col_l, col_s = st.columns(2)
    with col_l:
        st.write("🏬 **Lidl**")
        for i_id, i_name in c.execute("SELECT id, name FROM common_products WHERE store='Lidl'").fetchall():
            if st.button(f"+ {i_name}", key=f"ql_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store, added_by) VALUES (?,?,?)", (i_name, "Lidl", "App"))
                conn.commit(); st.rerun()
    with col_s:
        st.write("🏬 **Σκλαβενίτης**")
        for i_id, i_name in c.execute("SELECT id, name FROM common_products WHERE store='Σκλαβενίτης'").fetchall():
            if st.button(f"+ {i_name}", key=f"qs_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store, added_by) VALUES (?,?,?)", (i_name, "Σκλαβενίτης", "App"))
                conn.commit(); st.rerun()
    st.divider()
    for item_id, name, st_name, _ in c.execute("SELECT * FROM shopping_list").fetchall():
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"🛒 **{name}** ({st_name})")
        if c2.button("✅", key=f"ds_{item_id}"):
            c.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
            conn.commit(); st.rerun()
    with st.expander("⚙️ Settings"):
        with st.form("add_c"):
            n, s = st.text_input("Item"), st.selectbox("Store", ["Lidl", "Σκλαβενίτης"])
            if st.form_submit_button("Add Quick"):
                c.execute("INSERT INTO common_products (name, store) VALUES (?,?)", (n, s))
                conn.commit(); st.rerun()

# --- 5. HISTORY ---
elif choice == curr_t["menu"][4]:
    st.header(curr_t["history_title"])
    # Χρησιμοποιούμε το φιλτραρισμένο df
    for idx, row in df.sort_values('id', ascending=False).iterrows():
        with st.expander(f"{row['date']} | {row['amount']:.2f}€ | {row['category']}"):
            if row['receipt']: st.image(base64.b64decode(row['receipt']))
            if st.button("🗑️", key=f"del_{row['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

# --- 6. GOALS ---
elif choice == curr_t["menu"][5]:
    st.header(curr_t["goals_title"])
    with st.form("goal_f"):
        n, a = st.text_input(curr_t["goal_name"]), st.number_input(curr_t["goal_amt"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (n, a))
            conn.commit(); st.rerun()
    st.divider()
    all_inc = df_raw[df_raw['type'] == 'Income']['amount'].sum()
    all_exp = df_raw[df_raw['type'] == 'Expense']['amount'].sum()
    savings = all_inc - all_exp
    for gid, name, target in c.execute("SELECT * FROM goals").fetchall():
        prog = min(savings / target, 1.0) if target > 0 else 0
        st.write(f"**{name}** ({savings:,.2f} / {target:,.2f} €)")
        st.progress(prog)
        if st.button(f"🗑️", key=f"dg_{gid}"):
            c.execute("DELETE FROM goals WHERE id=?", (gid,))
            conn.commit(); st.rerun()

# --- 7. REMINDERS ---
elif choice == curr_t["menu"][6]:
    st.header(curr_t["reminders_title"])
    with st.form("rem_f"):
        t_rem, d_rem = st.text_input(curr_t["desc"]), st.date_input(curr_t["due"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO reminders (title, due_date, status) VALUES (?,?,?)", (t_rem, str(d_rem), "Pending"))
            conn.commit(); st.rerun()
    for rid, r_tit, r_d, r_stat in c.execute("SELECT * FROM reminders ORDER BY due_date ASC").fetchall():
