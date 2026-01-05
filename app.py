import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- ΡΥΘΜΙΣΗ ΚΩΔΙΚΟΥ ---
MASTER_PASSWORD = "γουρουνακια3" 

st.set_page_config(page_title="Chanchito Pro", layout="wide")

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Login Required")
    pwd_input = st.text_input("Κωδικός πρόσβασης / Password:", type="password")
    if st.button("Είσοδος / Enter"):
        if pwd_input == MASTER_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Λάθος κωδικός / Wrong Password!")
    st.stop()

# --- DATABASE SETUP ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS entries 
             (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, 
              amount REAL, source_desc TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals 
             (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)''')
conn.commit()

# --- ΓΛΩΣΣΕΣ ---
languages = {
    "🇬🇷 Ελληνικά": {
        "title": "🐷 Chanchito Οικονομία",
        "dash": "Κεντρική", "inc": "Έσοδα", "exp": "Έξοδα", "hist": "Ιστορικό", "goals": "🎯 Στόχοι",
        "person": "Ποιος;", "amount": "Ποσό (€)", "cat": "Κατηγορία", "desc": "Περιγραφή", "save": "Αποθήκευση",
        "success": "Έγινε η καταχώρηση!", "delete": "Διαγράφηκε!", "no_data": "Δεν υπάρχουν δεδομένα."
    },
    "🇪🇸 Español": {
        "title": "🐷 Chanchito Economía",
        "dash": "Panel", "inc": "Ingresos", "exp": "Gastos", "hist": "Historial", "goals": "🎯 Objetivos",
        "person": "¿Quién?", "amount": "Cantidad (€)", "cat": "Categoría", "desc": "Descripción", "save": "Guardar",
        "success": "¡Entrada guardada!", "delete": "¡Eliminado!", "no_data": "No hay datos todavía."
    },
    "🇬🇧 English": {
        "title": "🐷 Chanchito Finance",
        "dash": "Dashboard", "inc": "Income", "exp": "Expenses", "hist": "History", "goals": "🎯 Goals",
        "person": "Who?", "amount": "Amount (€)", "cat": "Category", "desc": "Description", "save": "Save",
        "success": "Entry saved!", "delete": "Deleted!", "no_data": "No data yet."
    }
}

lang_choice = st.sidebar.radio("Language / Γλώσσα", list(languages.keys()))
L = languages[lang_choice]

st.sidebar.title(f"Menu")
choice = st.sidebar.selectbox("Επιλογή", [L["dash"], L["inc"], L["exp"], L["hist"], L["goals"]])

if st.sidebar.button("Log Out"):
    st.session_state["authenticated"] = False
    st.rerun()

# Φόρτωση Δεδομένων
df = pd.read_sql_query("SELECT * FROM entries", conn)
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])

# --- 1. ΚΕΝΤΡΙΚΗ ---
if choice == L["dash"]:
    st.title(f"📊 {L['dash']}")
    if not df.empty:
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric(L["inc"], f"{t_inc:,.2f} €")
        col2.metric(L["exp"], f"{t_exp:,.2f} €")
        col3.metric("Balance", f"{(t_inc - t_exp):,.2f} €")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(L["exp"])
            exp_only = df[df['type'] == 'Expense']
            if not exp_only.empty:
                exp_df = exp_only.groupby('category')['amount'].sum().reset_index()
                st.vega_lite_chart(exp_df, {
                    'mark': {'type': 'arc', 'innerRadius': 40},
                    'encoding': {
                        'theta': {'field': 'amount', 'type': 'quantitative'},
                        'color': {'field': 'category', 'type': 'nominal'},
                    }
                })
        with c2:
            st.subheader("User Split")
            person_df = df.groupby(['person', 'type'])['amount'].sum().unstack().fillna(0)
            st.bar_chart(person_df)
    else:
        st.info(L["no_data"])

# --- 2. ΕΣΟΔΑ ---
elif choice == L["inc"]:
    st.header(f"💰 {L['inc']}")
    with st.form("inc_form"):
        p = st.selectbox(L["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(L["cat"], ["Μισθός", "Ενοίκιο", "Άλλο"])
        amt = st.number_input(L["amount"], min_value=0.0, step=0.01, format="%.2f")
        desc = st.text_input(L["desc"])
        if st.form_submit_button(L["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            for _ in range(3): st.balloons(); time.sleep(0.3)
            st.success(L["success"])
            time.sleep(1)
            st.rerun()

# --- 3. ΕΞΟΔΑ ---
elif choice == L["exp"]:
    st.header(f"💸 {L['exp']}")
    with st.form("exp_form"):
        p = st.selectbox(L["person"], ["Άις", "Κωνσταντίνος"])
        # Εδώ προστέθηκε η κατηγορία Missu!
        cat = st.selectbox(L["cat"], ["Missu", "Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Άλλο"])
        amt = st.number_input(L["amount"], min_value=0.0, step=0.01, format="%.2f")
        desc = st.text_input(L["desc"])
        if st.form_submit_button(L["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Expense", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            st.warning(L["success"])
            time.sleep(1)
            st.rerun()

# --- 4. ΙΣΤΟΡΙΚΟ ---
elif choice == L["hist"]:
    st.header(f"📜 {L['hist']}")
    if not df.empty:
        sorted_df = df.sort_values(by='id', ascending=False)
        for idx, row in sorted_df.iterrows():
            col_text, col_del = st.columns([0.8, 0.2])
            icon = "🟢" if row['type'] == 'Income' else "🔴"
            col_text.write(f"{icon} {row['date'].date()} | **{row['amount']:.2f}€** | {row['person']} | {row['category']}")
            if col_del.button("🗑️", key=f"del_{row['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (row['id'],))
                conn.commit()
                st.error(L["delete"])
                time.sleep(1)
                st.rerun()
            st.divider()
    else:
        st.info(L["no_data"])

# --- 5. ΣΤΟΧΟΙ ---
elif choice == L["goals"]:
    st.header(L["goals"])
    total_inc = df[df['type'] == 'Income']['amount'].sum()
    total_exp = df[df['type'] == 'Expense']['amount'].sum()
    real_money = total_inc - total_exp
    st.write(f"### Net Available: {real_money:,.2f} €")
    
    with st.expander("Add Goal"):
        g_name = st.text_input("Name")
        g_amt = st.number_input("Target Amount", min_value=0.0)
        if st.button(L["save"]):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (g_name, g_amt))
            conn.commit()
            st.rerun()
            
    goals_df = pd.read_sql_query("SELECT * FROM goals", conn)
    for idx, row in goals_df.iterrows():
        st.subheader(row['name'])
        prog = min(real_money / row['target_amount'], 1.0) if row['target_amount'] > 0 else 0
        st.progress(prog)
        st.write(f"{prog*100:.1f}% ({real_money:,.2f} / {row['target_amount']:,.2f}€)")
        if st.button("Delete Goal", key=f"g_{row['id']}"):
            c.execute("DELETE FROM goals WHERE id=?", (row['id'],))
            conn.commit()
            st.rerun()
