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

# --- CUSTOM CSS (Παστέλ χρώματα & στυλ) ---
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; border: 1px solid #ffb3c1; transition: all 0.3s; }
    .stButton>button:hover { background-color: #ffb3c1; color: white; transform: scale(1.05); }
    [data-testid="stSidebar"] { background-color: #fff0f3; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #ff4d6d; font-family: 'Comic Sans MS', cursive, sans-serif; }
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

# --- TRANSLATIONS ---
lang_choice = st.sidebar.radio("Γλώσσα / Language / Idioma 🌍", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇺🇸 English"])

t = {
    "🇬🇷 Ελληνικά": {
        "menu": ["🏠 Αρχική", "💰 Έσοδα", "💸 Έξοδα", "🛒 Σούπερ Μάρκετ", "🐾 Missu Care", "🔔 Υπενθυμίσεις", "📜 Ιστορικό", "🎯 Στόχοι"],
        "income_cats": ["Μισθός", "Ενοίκιο", "Άλλο"],
        "expense_cats": ["🐷 Αποταμίευση", "🐾 Missu", "🛒 Supermarket", "🍕 Φαγητό", "⚡ Λογαριασμοί", "🏠 Ενοίκιο", "🎬 Διασκέδαση", "🧸 Σπίτι", "💊 Υγεία", "🌈 Άλλο"],
        "income_title": "💰 Προσθήκη Εσόδου",
        "expense_title": "💸 Καταγραφή Εξόδου",
        "shopping_title": "🛒 Λίστα για Ψώνια",
        "reminders_title": "🔔 Λογαριασμοί & Λήξεις",
        "missu_title": "🐾 Ημερολόγιο Missu",
        "history_title": "📜 Ιστορικό",
        "goals_title": "🎯 Στόχοι Αποταμίευσης",
        "amount": "Ποσό (€)",
        "desc": "Περιγραφή",
        "save": "Αποθήκευση ✨",
        "person": "Ποιος;",
        "cat": "Κατηγορία",
        "is_shared": "👫 Κοινό έξοδο (50/50);",
        "debt_info": "📊 Εκκρεμότητες μεταξύ σας",
        "urgent": "⚠️ Λήγουν σύντομα:",
        "missu_urgent": "🐾 Για τη Missu:",
        "monthly_report": "📅 Αναφορά Εξόδων",
        "month": "Μήνας",
        "total": "Σύνολο",
        "action": "Ενέργεια",
        "notes": "Σημειώσεις",
        "balance": "Υπόλοιπο 🐷",
        "date_range": "Διάστημα",
        "ranges": ["Όλα", "Αυτός ο Μήνας", "Τελευταίες 30 μέρες"],
        "goal_name": "Όνομα Στόχου",
        "goal_target": "Ποσό Στόχου (€)"
    },
    "🇪🇸 Español": {
        "menu": ["🏠 Inicio", "💰 Ingresos", "💸 Gastos", "🛒 Supermercado", "🐾 Missu Care", "🔔 Recordatorios", "📜 Historial", "🎯 Objetivos"],
        "income_cats": ["Salario", "Alquiler", "Otros"],
        "expense_cats": ["🐷 Ahorro", "🐾 Missu", "🛒 Supermercado", "🍕 Comida", "⚡ Facturas", "🏠 Alquiler", "🎬 Ocio", "🧸 Hogar", "💊 Salud", "🌈 Otros"],
        "income_title": "💰 Ingreso", "expense_title": "💸 Gasto", "shopping_title": "🛒 Lista",
        "reminders_title": "🔔 Facturas", "missu_title": "🐾 Diario de Missu", "history_title": "📜 Historial",
        "goals_title": "🎯 Objetivos", "amount": "Cantidad", "desc": "Descripción", "save": "Guardar ✨",
        "person": "Quién", "cat": "Categoría", "is_shared": "¿Compartido?", "debt_info": "📊 Deudas",
        "urgent": "⚠️ Vencen pronto:", "missu_urgent": "🐾 Missu:",
        "monthly_report": "📅 Informe", "month": "Mes", "total": "Total", "action": "Acción",
        "notes": "Notas", "balance": "Balance 🐷", "date_range": "Periodo", "ranges": ["Todo", "Este mes", "30 días"],
        "goal_name": "Nombre", "goal_target": "Meta"
    },
    "🇺🇸 English": {
        "menu": ["🏠 Home", "💰 Income", "💸 Expenses", "🛒 Shopping", "🐾 Missu Care", "🔔 Reminders", "📜 History", "🎯 Goals"],
        "income_cats": ["Salary", "Rent", "Other"],
        "expense_cats": ["🐷 Savings", "🐾 Missu", "🛒 Supermarket", "🍕 Food", "⚡ Bills", "🏠 Rent", "🎬 Entertainment", "🧸 Home", "💊 Health", "🌈 Other"],
        "income_title": "💰 Add Income", "expense_title": "💸 Expense", "shopping_title": "🛒 List",
        "reminders_title": "🔔 Bills", "missu_title": "🐾 Missu", "history_title": "📜 History",
        "goals_title": "🎯 Goals", "amount": "Amount", "desc": "Description", "save": "Save ✨",
        "person": "Who", "cat": "Category", "is_shared": "Split?", "debt_info": "📊 Debts",
        "urgent": "⚠️ Due:", "missu_urgent": "🐾 Missu:",
        "monthly_report": "📅 Report", "month": "Month", "total": "Total", "action": "Action",
        "notes": "Notes", "balance": "Balance 🐷", "date_range": "Range", "ranges": ["All", "This Month", "30 Days"],
        "goal_name": "Goal", "goal_target": "Target"
    }
}

curr_t = t[lang_choice]
choice = st.sidebar.selectbox("Μενού", curr_t["menu"])

# --- HELPERS ---
def format_date_str(date_str):
    try: return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except: return date_str

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

full_df = pd.read_sql_query("SELECT * FROM entries", conn)
if not full_df.empty:
    full_df['date_dt'] = pd.to_datetime(full_df['date'])

# --- 1. ΑΡΧΙΚΗ ---
if choice.startswith("🏠"):
    st.title("¡Hola! 🐷✨")
    
    drange = st.selectbox(curr_t["date_range"], curr_t["ranges"])
    df = full_df.copy()
    if drange == curr_t["ranges"][1]:
        df = df[df['date_dt'].dt.month == datetime.now().month]
    elif drange == curr_t["ranges"][2]:
        df = df[df['date_dt'] >= (datetime.now() - timedelta(days=30))]

    if not df.empty:
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric(curr_t["menu"][1], f"{t_inc:,.2f} €")
        c2.metric(curr_t["menu"][2], f"{t_exp:,.2f} €")
        c3.metric(curr_t["balance"], f"{(t_inc - t_exp):,.2f} €")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    today_s = str(datetime.now().date())
    next_w_s = str(datetime.now().date() + timedelta(days=7))
    with col1:
        st.subheader(curr_t["missu_urgent"])
        m_urg = c.execute("SELECT action, date FROM missu_care WHERE date >= ? AND date <= ?", (today_s, next_w_s)).fetchall()
        for a, d in m_urg: st.error(f"🦴 **{a}** ({format_date_str(d)})")
    with col2:
        st.subheader(curr_t["urgent"])
        b_urg = c.execute("SELECT title, due_date, amount FROM reminders WHERE due_date >= ? AND due_date <= ?", (today_s, next_w_s)).fetchall()
        for tb, db, ab in b_urg: st.warning(f"🧾 {tb}: {ab}€ ({format_date_str(db)})")

    st.divider()
    
    if not df.empty:
        shared = df[df['is_shared'] == 1]
        ais_paid = shared[shared['person'] == 'Άις']['amount'].sum() / 2
        kon_paid = shared[shared['person'] == 'Κωνσταντίνος']['amount'].sum() / 2
        st.subheader(curr_t["debt_info"] + " 🤝")
        if ais_paid > kon_paid: st.info(f"Ο Κωνσταντίνος χρωστάει στην Άις: **{(ais_paid - kon_paid):.2f} €** 🐷")
        elif kon_paid > ais_paid: st.info(f"Η Άις χρωστάει στον Κωνσταντίνο: **{(kon_paid - ais_paid):.2f} €** 🐷")
        else: st.success("✅ Είστε πάτσι! ❤️")

    st.divider()
    st.subheader(curr_t["monthly_report"])
    exp_only = df[df['type'] == 'Expense']
    if not exp_only.empty:
        exp_only['month_disp'] = exp_only['date_dt'].dt.strftime('%m/%Y')
        st.table(exp_only.groupby('month_disp')['amount'].sum().reset_index())
        st.bar_chart(data=exp_only.groupby('category')['amount'].sum())

# --- 2. ΕΣΟΔΑ ---
elif "💰" in choice:
    st.header(curr_t["income_title"])
    with st.form("inc_f"):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["income_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0)
        desc = st.text_input(curr_t["desc"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit(); st.balloons(); st.success("Saved! 🐷💰"); time.sleep(1); st.rerun()

# --- 3. ΕΞΟΔΑ ---
elif "💸" in choice:
    st.header(curr_t["expense_title"])
    with st.form("exp_f"):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], curr_t["expense_cats"])
        amt = st.number_input(curr_t["amount"], min_value=0.0)
        desc = st.text_input(curr_t["desc"])
        sh = st.checkbox(curr_t["is_shared"])
        up = st.file_uploader("📸", type=['jpg','png','jpeg'])
        if st.form_submit_button(curr_t["save"]):
            img_s = ""
            if up:
                img = Image.open(up); img.thumbnail((400,400))
                img_s = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt, is_shared) VALUES (?,?,?,?,?,?,?,?)",
                      ("Expense", p, cat, amt, desc, str(datetime.now().date()), img_s, 1 if sh else 0))
            conn.commit(); st.success("Saved! ✨"); time.sleep(0.5); st.rerun()

# --- 4. SUPER MARKET ---
elif "🛒" in choice:
    st.header(curr_t["shopping_title"])
    col1, col2 = st.columns(2)
    with col1:
        st.write("🏬 **Lidl**")
        for i_id, i_n in c.execute("SELECT id, name FROM common_products WHERE store='Lidl'").fetchall():
            if st.button(f"➕ {i_n}", key=f"l_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (i_n, "Lidl")); conn.commit(); st.rerun()
    with col2:
        st.write("🏬 **Σκλαβενίτης**")
        for i_id, i_n in c.execute("SELECT id, name FROM common_products WHERE store='Σκλαβενίτης'").fetchall():
            if st.button(f"➕ {i_n}", key=f"s_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (i_n, "Σκλαβενίτης")); conn.commit(); st.rerun()
    st.divider()
    for sid, sit, sst, sab in c.execute("SELECT * FROM shopping_list").fetchall():
        c_a, c_b = st.columns([0.8, 0.2])
        c_a.write(f"🛒 {sit} ({sst})")
        if c_b.button("✅", key=f"ds_{sid}"):
            c.execute("DELETE FROM shopping_list WHERE id=?", (sid,)); conn.commit(); st.rerun()
    with st.expander("Νέο Προϊόν ✨"):
        with st.form("new_p"):
            n = st.text_input("Προϊόν"); s = st.selectbox("Store", ["Lidl", "Σκλαβενίτης"])
            if st.form_submit_button("Προσθήκη"):
                c.execute("INSERT INTO common_products (name, store) VALUES (?,?)", (n, s)); conn.commit(); st.rerun()

# --- 5. MISSU CARE ---
elif "🐾" in choice:
    st.header(curr_t["missu_title"])
    with st.form("m_f"):
        a = st.text_input(curr_t["action"]); d = st.date_input("Ημερομηνία"); nt = st.text_area(curr_t["notes"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO missu_care (action, date, notes) VALUES (?,?,?)", (a, str(d), nt)); conn.commit(); st.rerun()
    for mid, ma, md, mn in c.execute("SELECT * FROM missu_care ORDER BY date DESC").fetchall():
        with st.expander(f"🐾 {format_date_str(md)} - {ma}"):
            st.write(mn)
            if st.button("🗑️", key=f"dm_{mid}"): c.execute("DELETE FROM missu_care WHERE id=?", (mid,)); conn.commit(); st.rerun()

# --- 6. ΣΤΟΧΟΙ ---
elif "🎯" in choice:
    st.header(curr_t["goals_title"])
    with st.form("g_f"):
        gn = st.text_input(curr_t["goal_name"]); gt = st.number_input(curr_t["goal_target"], min_value=0.0)
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (gn, gt)); conn.commit(); st.rerun()
    
    t_inc = full_df[full_df['type'] == 'Income']['amount'].sum() if not full_df.empty else 0
    t_exp = full_df[full_df['type'] == 'Expense']['amount'].sum() if not full_df.empty else 0
    
    # Εδώ τσεκάρουμε αν η κατηγορία περιέχει τη λέξη "Αποταμίευση" ή "Ahorro" ή "Savings"
    # για να προστεθεί ξανά στον υπολογισμό των στόχων
    spec_sav = full_df[(full_df['type'] == 'Expense') & 
                       (full_df['category'].str.contains("Αποταμίευση|Ahorro|Savings", case=False))]['amount'].sum() if not full_df.empty else 0
    
    total_sav = (t_inc - t_exp) + spec_sav
    
    st.metric("Συνολική Αποταμίευση 🐽", f"{total_sav:,.2f} €")
    st.caption(f"(Περιλαμβάνει {spec_sav:,.2f} € που έχουν ήδη μεταφερθεί)")

    for gid, gn, gt in c.execute("SELECT * FROM goals").fetchall():
        st.subheader(f"⭐ {gn}")
        prog = min(total_sav / gt, 1.0) if gt > 0 else 0
        if prog == 1.0: st.balloons()
        st.progress(prog)
        st.write(f"💪 {total_sav:,.2f} / {gt:,.2f} € ({(prog*100):.1f}%)")
        if st.button(f"🗑️ {gn}", key=f"dg_{gid}"):
            c.execute("DELETE FROM goals WHERE id=?", (gid,)); conn.commit(); st.rerun()

# --- 7. ΥΠΟΛΟΙΠΑ (HISTORY & REMINDERS) ---
elif "🔔" in choice:
    st.header(curr_t["reminders_title"])
    with st.form("rem_f"):
        tr = st.text_input("Τίτλος"); dr = st.date_input("Λήξη"); ar = st.number_input("Ποσό")
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO reminders (title, due_date, amount) VALUES (?,?,?)", (tr, str(dr), ar)); conn.commit(); st.rerun()
    for rid, rt, rd, ra in c.execute("SELECT * FROM reminders ORDER BY due_date ASC").fetchall():
        st.write(f"📅 {format_date_str(rd)} - **{rt}** ({ra}€)")
        if st.button("🗑️", key=f"dr_{rid}"): c.execute("DELETE FROM reminders WHERE id=?", (rid,)); conn.commit(); st.rerun()

elif "📜" in choice:
    st.header(curr_t["history_title"])
    for idx, r in full_df.sort_values('id', ascending=False).iterrows():
        with st.expander(f"📜 {format_date_str(r['date'])} | {r['amount']}€ | {r['category']} ({r['person']})"):
            if r['receipt']: st.image(base64.b64decode(r['receipt']))
            if st.button("🗑️ Διαγραφή", key=f"h_{r['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
