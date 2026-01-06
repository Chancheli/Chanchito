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

st.set_page_config(page_title="Chanchito Pro & Missu", layout="wide")

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
lang_choice = st.sidebar.radio("Language / Idioma", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇺🇸 English"])

t = {
    "🇬🇷 Ελληνικά": {
        "menu": ["Κεντρική", "Έσοδα", "Έξοδα", "🛒 Σούπερ Μάρκετ", "🐾 Missu Care", "🔔 Υπενθυμίσεις", "Ιστορικό", "🎯 Στόχοι"],
        "income_title": "💰 Προσθήκη Εσόδου",
        "expense_title": "💸 Καταγραφή Εξόδου",
        "shopping_title": "🛒 Λίστα για Ψώνια",
        "reminders_title": "🔔 Λογαριασμοί & Λήξεις",
        "missu_title": "🐾 Ημερολόγιο Missu",
        "history_title": "📜 Ιστορικό",
        "goals_title": "🎯 Στόχοι",
        "amount": "Ποσό (€)",
        "desc": "Περιγραφή",
        "save": "Αποθήκευση",
        "person": "Ποιος;",
        "cat": "Κατηγορία",
        "is_shared": "👫 Κοινό έξοδο (50/50);",
        "debt_info": "📊 Εκκρεμότητες μεταξύ σας",
        "quick_add": "⚡ Γρήγορη Προσθήκη",
        "export": "📥 Λήψη σε Excel",
        "urgent": "⚠️ Λήγουν σύντομα:",
        "missu_urgent": "🐾 Υπενθύμιση για Missu:",
        "monthly_report": "📅 Μηνιαία Αναφορά",
        "month": "Μήνας",
        "total": "Σύνολο",
        "action": "Ενέργεια (π.χ. Εμβόλιο)",
        "notes": "Σημειώσεις"
    },
    "🇪🇸 Español": {
        "menu": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "🐾 Missu Care", "🔔 Recordatorios", "Historial", "🎯 Objetivos"],
        "income_title": "💰 Añadir Ingreso",
        "expense_title": "💸 Registrar Gasto",
        "shopping_title": "🛒 Lista de Compras",
        "reminders_title": "🔔 Facturas",
        "missu_title": "🐾 Diario de Missu",
        "history_title": "📜 Historial",
        "goals_title": "🎯 Objetivos",
        "amount": "Cantidad (€)",
        "desc": "Descripción",
        "save": "Guardar",
        "person": "¿Quién?",
        "cat": "Categoría",
        "is_shared": "👫 ¿Gasto compartido?",
        "debt_info": "📊 Deudas pendientes",
        "quick_add": "⚡ Añadir Rápido",
        "export": "📥 Descargar Excel",
        "urgent": "⚠️ Vencen pronto:",
        "missu_urgent": "🐾 Recordatorio Missu:",
        "monthly_report": "📅 Informe Mensual",
        "month": "Mes",
        "total": "Total",
        "action": "Acción",
        "notes": "Notas"
    },
    "🇺🇸 English": {
        "menu": ["Dashboard", "Income", "Expenses", "🛒 Shopping List", "🐾 Missu Care", "🔔 Reminders", "History", "🎯 Goals"],
        "income_title": "💰 Add Income",
        "expense_title": "💸 Record Expense",
        "shopping_title": "🛒 Shopping List",
        "reminders_title": "🔔 Bills",
        "missu_title": "🐾 Missu's Diary",
        "history_title": "📜 History",
        "goals_title": "🎯 Goals",
        "amount": "Amount (€)",
        "desc": "Description",
        "save": "Save",
        "person": "Who?",
        "cat": "Category",
        "is_shared": "👫 Split bill?",
        "debt_info": "📊 Who owes who",
        "quick_add": "⚡ Quick Add",
        "export": "📥 Download Excel",
        "urgent": "⚠️ Due soon:",
        "missu_urgent": "🐾 Missu Reminder:",
        "monthly_report": "📅 Monthly Report",
        "month": "Month",
        "total": "Total",
        "action": "Action",
        "notes": "Notes"
    }
}

curr_t = t[lang_choice]
choice = st.sidebar.selectbox("Menu", curr_t["menu"])

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

df = pd.read_sql_query("SELECT * FROM entries", conn)

# --- 1. DASHBOARD ---
if choice in ["Κεντρική", "Panel", "Dashboard"]:
    st.title(choice)
    
    # SPLIT BILLS INFO
    if not df.empty:
        shared = df[df['is_shared'] == 1]
        ais_paid_for_shared = shared[shared['person'] == 'Άις']['amount'].sum() / 2
        kon_paid_for_shared = shared[shared['person'] == 'Κωνσταντίνος']['amount'].sum() / 2
        
        st.subheader(curr_t["debt_info"])
        if ais_paid_for_shared > kon_paid_for_shared:
            st.info(f"🤝 Ο Κωνσταντίνος χρωστάει στην Άις: **{(ais_paid_for_shared - kon_paid_for_shared):.2f} €**")
        elif kon_paid_for_shared > ais_paid_for_shared:
            st.info(f"🤝 Η Άις χρωστάει στον Κωνσταντίνο: **{(kon_paid_for_shared - ais_paid_for_shared):.2f} €**")
        else:
            st.success("✅ Είστε πάτσι!")

    st.divider()
    
    # MISSU ALERTS
    st.subheader(curr_t["missu_urgent"])
    today_dt = datetime.now().date()
    next_week = today_dt + timedelta(days=7)
    missu_urgent = c.execute("SELECT action, date FROM missu_care WHERE date >= ? AND date <= ?", 
                             (str(today_dt), str(next_week))).fetchall()
    if missu_urgent:
        for m_act, m_date in missu_urgent:
            st.error(f"🐾 **{m_act}** στις {m_date}!")
    else:
        st.write("✨ Καμία εκκρεμότητα για τη Missu σύντομα.")

    st.divider()
    
    # BILL REMINDERS
    st.subheader(curr_t["urgent"])
    urgent_rem = c.execute("SELECT title, due_date, amount FROM reminders WHERE due_date >= ? AND due_date <= ?", 
                           (str(today_dt), str(next_week))).fetchall()
    if urgent_rem:
        for title, due, amt in urgent_rem:
            st.warning(f"🕒 {title}: {amt}€ - {due}")
    else:
        st.write("✅ Όλοι οι λογαριασμοί είναι εντάξει.")

    st.divider()

    # CHARTS & MONTHLY REPORT
    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'])
        df['date'] = pd.to_datetime(df['date'])
        
        # Metrics
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric(curr_t["menu"][1], f"{t_inc:,.2f} €")
        c2.metric(curr_t["menu"][2], f"{t_exp:,.2f} €")
        c3.metric("Balance", f"{(t_inc - t_exp):,.2f} €")
        
        st.divider()
        st.subheader(curr_t["monthly_report"])
        exp_df = df[df['type'] == 'Expense'].copy()
        if not exp_df.empty:
            # Bar Chart Categories
            cat_df = exp_df.groupby('category')['amount'].sum().reset_index()
            st.bar_chart(data=cat_df, x='category', y='amount')
            
            # Monthly Table
            exp_df['month_year'] = exp_df['date'].dt.strftime('%Y-%m')
            monthly_summary = exp_df.groupby('month_year')['amount'].sum().reset_index()
            monthly_summary.columns = [curr_t["month"], curr_t["total"]]
            st.table(monthly_summary)
            
        st.download_button(label=curr_t["export"], data=to_excel(df), file_name="finances.xlsx")

# --- 2. INCOME ---
elif choice == curr_t["menu"][1]:
    st.header(curr_t["income_title"])
    with st.form("inc_form"):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], ["Salary", "Rent", "Other"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input(curr_t["desc"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            st.balloons()
            st.success("Saved!")
            time.sleep(1)
            st.rerun()

# --- 3. EXPENSES ---
elif choice == curr_t["menu"][2]:
    st.header(curr_t["expense_title"])
    with st.form("exp_form"):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], ["🐾 Missu", "Supermarket", "Food", "Bills", "Rent", "Entertainment", "Home", "Health", "Other"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input(curr_t["desc"])
        shared_check = st.checkbox(curr_t["is_shared"])
        uploaded_file = st.file_uploader("Receipt Photo", type=['jpg', 'jpeg', 'png'])
        if st.form_submit_button(curr_t["save"]):
            img_str = ""
            if uploaded_file:
                img = Image.open(uploaded_file)
                img.thumbnail((400, 400))
                img_str = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt, is_shared) VALUES (?,?,?,?,?,?,?,?)",
                      ("Expense", p, cat, amt, desc, str(datetime.now().date()), img_str, 1 if shared_check else 0))
            conn.commit()
            st.success("OK!")
            time.sleep(0.5)
            st.rerun()

# --- 4. SHOPPING LIST ---
elif choice == curr_t["menu"][3]:
    st.header(curr_t["shopping_title"])
    col_l, col_s = st.columns(2)
    with col_l:
        st.write("🏬 **Lidl**")
        lidl_items = c.execute("SELECT id, name FROM common_products WHERE store='Lidl'").fetchall()
        for i_id, i_name in lidl_items:
            if st.button(f"+ {i_name}", key=f"ql_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store, added_by) VALUES (?,?,?)", (i_name, "Lidl", "App"))
                conn.commit(); st.rerun()
    with col_s:
        st.write("🏬 **Σκλαβενίτης**")
        sklav_items = c.execute("SELECT id, name FROM common_products WHERE store='Σκλαβενίτης'").fetchall()
        for i_id, i_name in sklav_items:
            if st.button(f"+ {i_name}", key=f"qs_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store, added_by) VALUES (?,?,?)", (i_name, "Σκλαβενίτης", "App"))
                conn.commit(); st.rerun()
    st.divider()
    items = c.execute("SELECT * FROM shopping_list").fetchall()
    for item_id, name, st_name, added_by in items:
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"🛒 **{name}** ({st_name})")
        if c2.button("✅", key=f"ds_{item_id}"):
            c.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
            conn.commit(); st.rerun()

# --- 5. MISSU CARE ---
elif choice == curr_t["menu"][4]:
    st.header(curr_t["missu_title"])
    with st.form("missu_form"):
        act = st.text_input(curr_t["action"])
        dt_missu = st.date_input("Date")
        nts = st.text_area(curr_t["notes"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO missu_care (action, date, notes) VALUES (?,?,?)", (act, str(dt_missu), nts))
            conn.commit(); st.rerun()
    st.divider()
    missu_data = c.execute("SELECT * FROM missu_care ORDER BY date DESC").fetchall()
    for mid, mact, mdt, mnts in missu_data:
        with st.expander(f"🐾 {mdt} - {mact}"):
            st.write(mnts)
            if st.button("🗑️", key=f"del_m_{mid}"):
                c.execute("DELETE FROM missu_care WHERE id=?", (mid,))
                conn.commit(); st.rerun()

# --- 6. REMINDERS (BILLS) ---
elif choice == curr_t["menu"][5]:
    st.header(curr_t["reminders_title"])
    with st.form("rem_form"):
        t_rem = st.text_input("Title")
        d_rem = st.date_input("Due Date")
        a_rem = st.number_input("Amount (€)", min_value=0.0)
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO reminders (title, due_date, amount) VALUES (?,?,?)", (t_rem, str(d_rem), a_rem))
            conn.commit(); st.rerun()
    st.divider()
    all_rems = c.execute("SELECT * FROM reminders ORDER BY due_date ASC").fetchall()
    for rid, rt, rd, ra in all_rems:
        c1, c2, c3 = st.columns([0.5, 0.3, 0.2])
        c1.write(f"📅 {rd} - **{rt}**")
        c2.write(f"{ra} €")
        if c3.button("🗑️", key=f"del_rem_{rid}"):
            c.execute("DELETE FROM reminders WHERE id=?", (rid,))
            conn.commit(); st.rerun()

# --- 7. HISTORY & 8. GOALS (Προστέθηκαν για πληρότητα) ---
elif choice == curr_t["menu"][6]:
    st.header(curr_t["history_title"])
    df_show = pd.read_sql_query("SELECT * FROM entries ORDER BY id DESC", conn)
    for idx, row in df_show.iterrows():
        with st.expander(f"{row['date']} | {row['amount']:.2f}€ | {row['category']}"):
            if row['receipt']: st.image(base64.b64decode(row['receipt']))
            if st.button("🗑️", key=f"del_{row['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

elif choice == curr_t["menu"][7]:
    st.header(curr_t["goals_title"])
    with st.form("goal_f"):
        gn = st.text_input(curr_t["goal_name"])
        ga = st.number_input(curr_t["goal_amt"])
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (gn, ga))
            conn.commit(); st.rerun()
