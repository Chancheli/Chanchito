
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
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
              amount REAL, source_desc TEXT, date TEXT, receipt TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals 
             (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS shopping_list 
             (id INTEGER PRIMARY KEY, item TEXT, store TEXT, added_by TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS common_products 
             (id INTEGER PRIMARY KEY, name TEXT, store TEXT)''')
conn.commit()

# --- FUNCTIONS ---
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- MENU ---
lang_choice = st.sidebar.radio("Language", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇬🇧 English"])
menu_options = {
    "🇬🇷 Ελληνικά": ["Κεντρική", "Έσοδα", "Έξοδα", "🛒 Σούπερ Μάρκετ", "Ιστορικό", "🎯 Στόχοι"],
    "🇪🇸 Español": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "Historial", "🎯 Objetivos"],
    "🇬🇧 English": ["Dashboard", "Income", "Expenses", "🛒 Shopping List", "History", "🎯 Goals"]
}
choice = st.sidebar.selectbox("Menu", menu_options[lang_choice])

df = pd.read_sql_query("SELECT * FROM entries", conn)

# --- 1. ΚΕΝΤΡΙΚΗ ---
if choice in ["Κεντρική", "Panel", "Dashboard"]:
    st.title("📊 Dashboard")
    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'])
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Έσοδα", f"{t_inc:,.2f} €")
        c2.metric("💸 Έξοδα", f"{t_exp:,.2f} €")
        c3.metric("⚖️ Υπόλοιπο", f"{(t_inc - t_exp):,.2f} €")
        st.divider()
        exp_only = df[df['type'] == 'Expense']
        if not exp_only.empty:
            exp_df = exp_only.groupby('category')['amount'].sum().reset_index()
            st.subheader("Έξοδα ανά Κατηγορία")
            st.bar_chart(data=exp_df, x='category', y='amount')
    else: st.info("Δεν υπάρχουν δεδομένα.")

# --- 2. ΕΣΟΔΑ ---
elif choice in ["Έσοδα", "Ingresos", "Income"]:
    st.header("💰 Προσθήκη Εσόδου")
    with st.form("inc_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Κατηγορία", ["Μισθός", "Ενοίκιο", "Άλλο"])
        amt = st.number_input("Ποσό (€)", min_value=0.0, step=0.01, format="%.2f")
        desc = st.text_input("Περιγραφή")
        if st.form_submit_button("Αποθήκευση"):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)",
                      ("Income", p, cat, amt, desc, str(datetime.now().date())))
            conn.commit()
            st.balloons(); st.rerun()

# --- 3. ΕΞΟΔΑ ---
elif choice in ["Έξοδα", "Gastos", "Expenses"]:
    st.header("💸 Καταγραφή Εξόδου")
    with st.form("exp_form"):
        p = st.selectbox("Ποιος;", ["Άις", "Κωνσταντίνος"])
        # Εδώ το σωστό όνομα Missu 🐾
        cat = st.selectbox("Κατηγορία", ["🐾 Missu", "Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Ενοίκιο", "Διασκέδαση", "Σπίτι", "Υγεία", "Άλλο"])
        amt = st.number_input("Ποσό (€)", min_value=0.0, step=0.01, format="%.2f")
        desc = st.text_input("Περιγραφή")
        uploaded_file = st.file_uploader("Φωτογραφία Απόδειξης", type=['jpg', 'jpeg', 'png'])
        if st.form_submit_button("Καταχώρηση"):
            img_str = ""
            if uploaded_file:
                img = Image.open(uploaded_file)
                img.thumbnail((400, 400))
                img_str = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt) VALUES (?,?,?,?,?,?,?)",
                      ("Expense", p, cat, amt, desc, str(datetime.now().date()), img_str))
            conn.commit()
            st.success("Καταγράφηκε!"); time.sleep(0.5); st.rerun()

# --- 4. ΣΟΥΠΕΡ ΜΑΡΚΕΤ ---
elif choice in ["🛒 Σούπερ Μάρκετ", "🛒 Supermercado", "🛒 Shopping List"]:
    st.header("🛒 Λίστα για Ψώνια")
    
    st.subheader("⚡ Γρήγορη Προσθήκη (Lidl & Σκλαβενίτης)")
    col_l, col_s = st.columns(2)
    
    with col_l:
        st.write("🏬 **Lidl**")
        lidl_items = c.execute("SELECT id, name FROM common_products WHERE store='Lidl'").fetchall()
        for i_id, i_name in lidl_items:
            if st.button(f"+ {i_name}", key=f"quick_l_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store, added_by) VALUES (?,?,?)", (i_name, "Lidl", "Χρήστης"))
                conn.commit(); st.rerun()
                
    with col_s:
        st.write("🏬 **Σκλαβενίτης**")
        sklav_items = c.execute("SELECT id, name FROM common_products WHERE store='Σκλαβενίτης'").fetchall()
        for i_id, i_name in sklav_items:
            if st.button(f"+ {i_name}", key=f"quick_s_{i_id}"):
                c.execute("INSERT INTO shopping_list (item, store, added_by) VALUES (?,?,?)", (i_name, "Σκλαβενίτης", "Χρήστης"))
                conn.commit(); st.rerun()

    st.divider()

    view_store = st.radio("Φίλτρο:", ["Όλα", "Lidl", "Σκλαβενίτης"], horizontal=True)
    q = "SELECT * FROM shopping_list"
    if view_store != "Όλα": q += f" WHERE store='{view_store}'"
    
    items = c.execute(q).fetchall()
    if items:
        for item_id, name, st_name, added_by in items:
            c1, c2 = st.columns([0.8, 0.2])
            c1.write(f"🛒 **{name}** ({st_name})")
            if c2.button("✅ Πήρα", key=f"del_shop_{item_id}"):
                c.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
                conn.commit(); st.rerun()
    else: st.info("Η λίστα είναι άδεια!")

    st.divider()

    with st.expander("⚙️ Διαχείριση Προϊόντων (Πρόσθεσε κουμπιά)"):
        with st.form("add_common_item", clear_on_submit=True):
            new_c_item = st.text_input("Όνομα προϊόντος (π.χ. Άμμος Missu)")
            new_c_store = st.selectbox("Κατάστημα:", ["Lidl", "Σκλαβενίτης"])
            if st.form_submit_button("Προσθήκη"):
                if new_c_item:
                    c.execute("INSERT INTO common_products (name, store) VALUES (?,?)", (new_c_item, new_c_store))
                    conn.commit(); st.rerun()
        
        st.write("---")
        all_c = c.execute("SELECT * FROM common_products").fetchall()
        for cid, cn, cs in all_c:
            if st.button(f"🗑️ Διαγραφή: {cn} ({cs})", key=f"rm_c_{cid}"):
                c.execute("DELETE FROM common_products WHERE id=?", (cid,))
                conn.commit(); st.rerun()

# --- 5. ΙΣΤΟΡΙΚΟ ---
elif choice in ["Ιστορικό", "Historial", "History"]:
    st.header("📜 Ιστορικό")
    df_show = pd.read_sql_query("SELECT * FROM entries ORDER BY id DESC", conn)
    for idx, row in df_show.iterrows():
        with st.expander(f"{row['date']} | {row['amount']:.2f}€ | {row['category']}"):
            st.write(f"Περιγραφή: {row['source_desc']}")
            if row['receipt']:
                st.image(base64.b64decode(row['receipt']))
            if st.button("🗑️ Διαγραφή", key=f"del_entry_{row['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

# --- 6. ΣΤΟΧΟΙ ---
elif choice == "🎯 Στόχοι":
    st.header("🎯 Στόχοι")
    total_inc = df[df['type'] == 'Income']['amount'].sum()
    total_exp = df[df['type'] == 'Expense']['amount'].sum()
    real_money = total_inc - total_exp
    st.metric("Υπόλοιπο", f"{real_money:,.2f} €")
    
    goals_df = pd.read_sql_query("SELECT * FROM goals", conn)
    for idx, row in goals_df.iterrows():
        st.subheader(row['name'])
        prog = min(real_money / row['target_amount'], 1.0) if row['target_amount'] > 0 else 0
        st.progress(prog)
        if st.button("Διαγραφή Στόχου", key=f"goal_del_{row['id']}"):
            c.execute("DELETE FROM goals WHERE id=?", (row['id'],))
            conn.commit(); st.rerun()
