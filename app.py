

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
    pwd_input = st.text_input("Κωδικός πρόσβασης:", type="password")
    if st.button("Είσοδος"):
        if pwd_input == MASTER_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Λάθος κωδικός!")
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

# --- SIDEBAR MENU ---
st.sidebar.title(f"🐷 Chanchito Menu")
choice = st.sidebar.selectbox("Επιλογή", ["Κεντρική", "Έσοδα", "Έξοδα", "Ιστορικό", "🎯 Στόχοι"])

if st.sidebar.button("Log Out"):
    st.session_state["authenticated"] = False
    st.rerun()

# Φόρτωση Δεδομένων
df = pd.read_sql_query("SELECT * FROM entries", conn)
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])

# --- 1. ΚΕΝΤΡΙΚΗ (DASHBOARD) ---
if choice == "Κεντρική":
    st.title("📊 Η Οικονομία μας")
    if not df.empty:
        total_inc = df[df['type'] == 'Income']['amount'].sum()
        total_exp = df[df['type'] == 'Expense']['amount'].sum()
        balance = total_inc - total_exp
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Συνολικά Έσοδα", f"{total_inc:,.2f} €")
        col2.metric("Συνολικά Έξοδα", f"{total_exp:,.2f} €")
        col3.metric("Πραγματικό Υπόλοιπο", f"{balance:,.2f} €")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Πού πάνε τα λεφτά;")
            exp_only = df[df['type'] == 'Expense']
            if not exp_only.empty:
                exp_df = exp_only.groupby('category')['amount'].sum().reset_index()
                st.write("Πίτα Εξόδων")
                st.vega_lite_chart(exp_df, {
                    'mark': {'type': 'arc', 'innerRadius': 50},
                    'encoding': {
                        'theta': {'field': 'amount', 'type': 'quantitative'},
                        'color': {'field': 'category', 'type': 'nominal'},
                    }
                })
        with c2:
            st.subheader("Έσοδα vs Έξοδα ανά Άτομο")
            person_df = df.groupby(['person', 'type'])['amount'].sum().unstack().fillna(0)
            st.bar_chart(person_df)
    else:
        st.info("Δεν υπάρχουν δεδομένα. Ξεκίνα να καταγράφεις!")

# --- 2. ΕΣΟΔΑ ---
elif choice == "Έσοδα":
    st.header("💰 Προσθήκη Εσόδου")
    with st.form("inc_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Κατηγορία", ["Μισθός", "Ενοίκιο", "Άλλο"])
        # Εδώ επιτρέπουμε δεκαδικά με τελεία
        amt = st.number_input("Ποσό (€) - Χρησιμοποίησε τελεία για δεκαδικά", min_value=0.0, step=0.01, format="%.2f")
        desc = st.text_input("Περιγραφή")
        if st.form_submit_button("Αποθήκευση"):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            # Πολλά μπαλόνια!
            for _ in range(3):
                st.balloons()
                time.sleep(0.3)
            st.success("Έγινε η καταχώρηση!")
            time.sleep(1)
            st.rerun()

# --- 3. ΕΞΟΔΑ ---
elif choice == "Έξοδα":
    st.header("💸 Καταγραφή Εξόδου")
    with st.form("exp_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Κατηγορία", ["Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Άλλο"])
        amt = st.number_input("Ποσό (€)", min_value=0.0, step=0.01, format="%.2f")
        desc = st.text_input("Περιγραφή")
        if st.form_submit_button("Καταχώρηση"):
            c.execute("INSERT INTO entries (type, person, category
