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

# --- SIDEBAR & ΓΛΩΣΣΑ ---
lang = st.sidebar.radio("Γλώσσα / Language", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇬🇧 English"])

# Μεταφράσεις
if lang == "🇬🇷 Ελληνικά":
    t = {"dash": "Κεντρική", "inc": "Έσοδα", "exp": "Έξοδα", "hist": "Ιστορικό", "goals": "🎯 Στόχοι", "cat": "Κατηγορία"}
elif lang == "🇪🇸 Español":
    t = {"dash": "Panel", "inc": "Ingresos", "exp": "Gastos", "hist": "Historial", "goals": "🎯 Objetivos", "cat": "Categoría"}
else:
    t = {"dash": "Dashboard", "inc": "Income", "exp": "Expenses", "hist": "History", "goals": "🎯 Goals", "cat": "Category"}

st.sidebar.title(f"🐷 Chanchito Menu")
choice = st.sidebar.selectbox("Επιλογή", [t["dash"], t["inc"], t["exp"], t["hist"], t["goals"]])

# Φόρτωση Δεδομένων
df = pd.read_sql_query("SELECT * FROM entries", conn)
df['date'] = pd.to_datetime(df['date'])

# --- ΣΕΛΙΔΕΣ ---

# 1. ΕΣΟΔΑ (Με Κατηγορίες & Μπαλόνια)
if choice == t["inc"]:
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
            st.balloons()
            st.snow() # Πυροτεχνήματα/Χιόνι για έξτρα χαρά!
            st.success("Το χρήμα έρρευσε!")
            time.sleep(1)
            st.rerun()

# 2. ΕΞΟΔΑ
elif choice == t["exp"]:
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
            st.warning("Έφυγαν τα λεφτά...")
            time.sleep(1)
            st.rerun()

# 3. ΕΞΥΠΝΟΙ ΣΤΟΧΟΙ
elif choice == t["goals"]:
    st.header("🎯 Στόχοι Αγορών")
    
    # Υπολογισμός Διαθέσιμου Υπολοίπου (Πραγματικά λεφτά)
    total_inc = df[df['type'] == 'Income']['amount'].sum()
    total_exp = df[df['type'] == 'Expense']['amount'].sum()
    real_money = total_inc - total_exp
    
    st.metric("Πραγματικό Περίσσευμα (Net Balance)", f"{real_money:,.2f} €")
    
    st.divider()
    
    # Φόρμα Στόχου
    with st.expander("Προσθήκη Νέου Στόχου (π.χ. Καναπές)"):
        g_name = st.text_input("Τι θέλεις να αγοράσεις;")
        g_amt = st.number_input("Πόσο κοστίζει;", min_value=0.0)
        if st.button("Προσθήκη Στόχου"):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (g_name, g_amt))
            conn.commit()
            st.rerun()

    # Εμφάνιση Στόχων
    goals_df = pd.read_sql_query("SELECT * FROM goals", conn)
    for idx, row in goals_df.iterrows():
        st.subheader(f"🏷️ {row['name']}")
        # Υπολογισμός προόδου
        progress = min(real_money / row['target_amount'], 1.0) if row['target_amount'] > 0 else 0
        
        col1, col2 = st.columns([0.8, 0.2])
        col1.progress(progress)
        col2.write(f"{progress*100:.1f}%")
        
        if real_money >= row['target_amount']:
            st.success(f"✅ Μπορείς να το αγοράσεις! Περισσεύουν {real_money - row['target_amount']:.2f} € μετά την αγορά.")
        else:
            st.info(f"⏳ Σου λείπουν ακόμα {row['target_amount'] - real_money:.2f} €.")
        
        if st.button("Διαγραφή Στόχου", key=f"goal_{row['id']}"):
            c.execute("DELETE FROM goals WHERE id=?", (row['id'],))
            conn.commit()
            st.rerun()

# (Τα υπόλοιπα Dashboards & History παραμένουν ως είχαν)
else:
    st.info("Επίλεξε μια ενότητα από το μενού αριστερά!")
