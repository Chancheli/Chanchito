
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

# --- DATABASE ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS entries 
             (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, 
              amount REAL, source_desc TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals 
             (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)''')
conn.commit()

# --- SIDEBAR ---
st.sidebar.title(f"🐷 Chanchito Menu")
choice = st.sidebar.selectbox("Επιλογή", ["Κεντρική", "Έσοδα", "Έξοδα", "Ιστορικό", "🎯 Στόχοι"])

if st.sidebar.button("Log Out"):
    st.session_state["authenticated"] = False
    st.rerun()

# Φόρτωση Δεδομένων
df = pd.read_sql_query("SELECT * FROM entries", conn)
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])

# --- ΣΕΛΙΔΕΣ ---

# 1. ΚΕΝΤΡΙΚΗ (DASHBOARD) - ΕΔΩ ΕΙΝΑΙ ΟΙ ΠΙΤΕΣ ΣΟΥ!
if choice == "Κεντρική":
    st.title("📊 Η Οικονομία μας")
    if not df.empty:
        total_inc = df[df['type'] == 'Income']['amount'].sum()
        total_exp = df[df['type'] == 'Expense']['amount'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Συνολικά Έσοδα", f"{total_inc:,.2f} €")
        col2.metric("Συνολικά Έξοδα", f"{total_exp:,.2f} €")
        col3.metric("Διαθέσιμο Υπόλοιπο", f"{(total_inc - total_exp):,.2f} €", delta_color="normal")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Πού πάνε τα λεφτά; (Έξοδα)")
            exp_df = df[df['type'] == 'Expense'].groupby('category')['amount'].sum().reset_index()
            st.pie_chart(data=exp_df, values='amount', names='category')
        with c2:
            st.subheader("Ποιος ξοδεύει πιο πολύ;")
            person_df = df[df['type'] == 'Expense'].groupby('person')['amount'].sum().reset_index()
            st.bar_chart(data=person_df, x='person', y='amount')
    else:
        st.info("Δεν υπάρχουν δεδομένα ακόμα. Ξεκίνα τις καταχωρήσεις!")

# 2. ΕΣΟΔΑ (Με περισσότερα μπαλόνια!)
elif choice == "Έσοδα":
    st.header("💰 Προσθήκη Εσόδου")
    with st.form("inc_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Κατηγορία", ["Μισθός", "Ενοίκιο", "Άλλο"])
        amt = st.number_input("Ποσό (€)", min_value=0.0)
        desc = st.text_input("Περιγραφή")
        if st.form_submit_button("Αποθήκευση"):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            # Πολλά μπαλόνια για να τα προλάβεις!
            for i in range(3):
                st.balloons()
                time.sleep(0.5)
            st.success("Το χρήμα έρρευσε!")
            time.sleep(1)
            st.rerun()

# 3. ΙΣΤΟΡΙΚΟ (ΕΔΩ ΘΑ ΣΒΗΣΕΙΣ ΤΟ ΛΑΘΟΣ)
elif choice == "Ιστορικό":
    st.header("📜 Ιστορικό Κινήσεων")
    if not df.empty:
        # Ταξινόμηση από το πιο πρόσφατο
        sorted_df = df.sort_values(by='date', ascending=False)
        for idx, row in sorted_df.iterrows():
            with st.container():
                col_a, col_b = st.columns([0.85, 0.15])
                icon = "🟢" if row['type'] == 'Income' else "🔴"
                col_a.write(f"{icon} **{row['amount']:.2f}€** | {row['category']} ({row['person']}) - {row['source_desc']}")
                # ΚΟΥΜΠΙ ΔΙΑΓΡΑΦΗΣ
                if col_b.button("🗑️", key=f"del_{row['id']}"):
                    c.execute("DELETE FROM entries WHERE id=?", (row['id'],))
                    conn.commit()
                    st.warning("Η εγγραφή διαγράφηκε!")
                    time.sleep(1)
                    st.rerun()
                st.divider()
    else:
        st.info("Το ιστορικό είναι άδειο.")

# (Οι άλλες σελίδες Έξοδα & Στόχοι παραμένουν ίδιες)
elif choice == "Έξοδα":
    st.header("💸 Καταγραφή Εξόδου")
    with st.form("exp_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Κατηγορία", ["Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Άλλο"])
        amt = st.number_input("Ποσό (€)", min_value=0.0)
        desc = st.text_input("Περιγραφή")
        if st.form_submit_button("Καταχώρηση"):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Expense", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            st.rerun()

elif choice == "🎯 Στόχοι":
    st.info("Εδώ θα βλέπεις αν βγαίνει ο προϋπολογισμός σου!")
