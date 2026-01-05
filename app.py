import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- ΡΥΘΜΙΣΗ ΚΩΔΙΚΟΥ ---
MASTER_PASSWORD = "γουρουνακια3" # <-- Εδώ αλλάζεις τον κωδικό σου!

st.set_page_config(page_title="Pro Home Budget", layout="wide")

# --- LOGIN "ΠΟΡΤΑ" ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Login Required")
    pwd_input = st.text_input("Παρακαλώ εισάγετε τον κωδικό πρόσβασης:", type="password")
    if st.button("Είσοδος"):
        if pwd_input == MASTER_PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Πρόσβαση επετράπη!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Λάθος κωδικός! Προσπαθήστε ξανά.")
    st.stop() # Σταματάει την εκτέλεση της υπόλοιπης εφαρμογής

# --- ΑΠΟ ΕΔΩ ΚΑΙ ΚΑΤΩ Ο ΚΩΔΙΚΑΣ ΤΡΕΧΕΙ ΜΟΝΟ ΑΝ Ο ΚΩΔΙΚΟΣ ΕΙΝΑΙ ΣΩΣΤΟΣ ---

# --- DATABASE SETUP ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS entries 
             (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, 
              amount REAL, source_desc TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals 
             (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS monthly_budget (id INTEGER PRIMARY KEY, amount REAL)''')
conn.commit()

# --- ΓΛΩΣΣΕΣ (DICTIONARY) ---
languages = {
    "🇬🇷 Ελληνικά": {
        "title": "💎 Έξυπνη Οικονομία",
        "dash": "Dashboard", "inc": "Έσοδα", "exp": "Έξοδα", "hist": "Ιστορικό & Roasts", "goals": "🎯 Στόχοι",
        "person": "Ποιος;", "amount": "Ποσό (€)", "cat": "Κατηγορία", "desc": "Περιγραφή", "save": "Αποθήκευση",
        "m_save_goal": "Μηνιαίος Στόχος Αποταμίευσης", "success_save": "Έγινε η καταχώρηση!",
        "total_exp_msg": "Συνολικά Έξοδα:", "no_data": "Δεν υπάρχουν δεδομένα ακόμα."
    },
    "🇬🇧 English": {
        "title": "💎 Smart Home Economy",
        "dash": "Dashboard", "inc": "Incomes", "exp": "Expenses", "hist": "History & Roasts", "goals": "🎯 Goals",
        "person": "Who?", "amount": "Amount (€)", "cat": "Category", "desc": "Description", "save": "Save",
        "m_save_goal": "Monthly Savings Goal", "success_save": "Entry saved!",
        "total_exp_msg": "Total Expenses:", "no_data": "No data yet."
    },
    "🇪🇸 Español": {
        "title": "💎 Economía Inteligente",
        "dash": "Panel", "inc": "Ingresos", "exp": "Gastos", "hist": "Historial & Roasts", "goals": "🎯 Objetivos",
        "person": "¿Quién?", "amount": "Cantidad (€)", "cat": "Categoría", "desc": "Descripción", "save": "Guardar",
        "m_save_goal": "Meta de Ahorro Mensual", "success_save": "¡Entrada guardada!",
        "total_exp_msg": "Gastos Totales:", "no_data": "¡No hay datos todavía!"
    }
}

# Επιλογή Γλώσσας στο Sidebar
lang_choice = st.sidebar.selectbox("🌐 Language / Γλώσσα", list(languages.keys()))
L = languages[lang_choice]

st.title(L["title"])

# Logout Button στο Sidebar
if st.sidebar.button("Log Out"):
    st.session_state["authenticated"] = False
    st.rerun()

ALL_CATEGORIES = ["Σούπερ Μάρκετ", "Φαγητό", "Καφές", "Missu", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Μεταφορικά", "Άλλο"]

menu = [L["dash"], L["inc"], L["exp"], L["hist"], L["goals"]]
choice = st.sidebar.selectbox("Menu", menu)

df = pd.read_sql_query("SELECT * FROM entries", conn)
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.to_period('M').astype(str)

# --- DASHBOARD ---
if choice == L["dash"]:
    if not df.empty:
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric(L["inc"], f"{t_inc:,.2f}€")
        c2.metric(L["exp"], f"{t_exp:,.2f}€")
        c3.metric("Balance", f"{(t_inc-t_exp):,.2f}€")
        st.divider()
        st.subheader(L["exp"])
        exp_df = df[df['type'] == 'Expense'].groupby('category')['amount'].sum().reset_index()
        st.bar_chart(data=exp_df, x='category', y='amount', color="#e74c3c")
    else: st.info(L["no_data"])

# --- ΕΣΟΔΑ / ΕΞΟΔΑ ---
elif choice in [L["inc"], L["exp"]]:
    is_inc = choice == L["inc"]
    st.subheader(f"➕ {choice}")
    with st.form("entry_form"):
        p = st.selectbox(L["person"], ["Άις", "Κωνσταντίνος"])
        amt = st.number_input(L["amount"], min_value=0.0)
        cat = "Income" if is_inc else st.selectbox(L["cat"], ALL_CATEGORIES)
        desc = st.text_input(L["desc"])
        d = st.date_input("Date")
        if st.form_submit_button(L["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income" if is_inc else "Expense", p, cat, amt, desc, str(d)))
            conn.commit()
            if is_inc:
                st.balloons()
                time.sleep(2)
            st.success(L["success_save"])
            time.sleep(1)
            st.rerun()

# --- ΙΣΤΟΡΙΚΟ & ROASTS ---
elif choice == L["hist"]:
    if not df.empty:
        f1, f2 = st.columns(2)
        with f1: sel_month = st.selectbox("Month", sorted(df['month_year'].unique(), reverse=True))
        with f2: sel_person = st.selectbox("Person", ["Όλοι", "Άις", "Κωνσταντίνος"])
        
        filtered = df[df['month_year'] == sel_month]
        if sel_person != "Όλοι": filtered = filtered[filtered['person'] == sel_person]
        
        st.info(f"{L['total_exp_msg']} {filtered[filtered['type']=='Expense']['amount'].sum():,.2f} €")
        
        # Roast Logic
        ais_t = df[(df['type'] == 'Expense') & (df['month_year'] == sel_month) & (df['person'] == 'Άις')]['amount'].sum()
        kon_t = df[(df['type'] == 'Expense') & (df['month_year'] == sel_month) & (df['person'] == 'Κωνσταντίνος')]['amount'].sum()
        if ais_t > kon_t: st.error(f"⚠️ Roast: Άις, είσαι {ais_t-kon_t:.2f}€ πάνω από τον Κωνσταντίνο!")
        elif kon_t > ais_t: st.error(f"⚠️ Roast: Κωνσταντίνε, είσαι {kon_t-ais_t:.2f}€ πάνω από την Άις!")

        st.divider()
        for idx, row in filtered.iterrows():
            col_a, col_b = st.columns([0.8, 0.2])
            icon = "💰" if row['type'] == 'Income' else "💸"
            col_a.write(f"{icon} {row['date'].strftime('%d/%m')} | {row['person']} | {row['category']}: {row['amount']}€ ({row['source_desc']})")
            if col_b.button("🗑️", key=f"del_{row['id']}"):
                c.execute("DELETE FROM entries WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
    else: st.info(L["no_data"])

# --- ΣΤΟΧΟΙ & ΑΠΟΤΑΜΙΕΥΣΗ ---
elif choice == L["goals"]:
    st.header(L["goals"])
    with st.form("monthly_goal_form"):
        st.subheader(L["m_save_goal"])
        res = c.execute("SELECT amount FROM monthly_budget").fetchone()
        curr_b = res[0] if res else 0.0
        new_b = st.number_input(L["amount"], value=float(curr_b))
        if st.form_submit_button(L["save"]):
            c.execute("DELETE FROM monthly_budget")
            c.execute("INSERT INTO monthly_budget (amount) VALUES (?)", (new_b,))
            conn.commit()
            st.success("Target Updated!")
            st.rerun()
