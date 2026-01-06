
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
              amount REAL, source_desc TEXT, date TEXT, receipt TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals 
             (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS shopping_list 
             (id INTEGER PRIMARY KEY, item TEXT, store TEXT, added_by TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS common_products 
             (id INTEGER PRIMARY KEY, name TEXT, store TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reminders 
             (id INTEGER PRIMARY KEY, title TEXT, due_date TEXT, amount REAL)''')
conn.commit()

# --- TRANSLATIONS ---
lang_choice = st.sidebar.radio("Language / Idioma", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇺🇸 English"])

t = {
    "🇬🇷 Ελληνικά": {
        "menu": ["Κεντρική", "Έσοδα", "Έξοδα", "🛒 Σούπερ Μάρκετ", "🔔 Υπενθυμίσεις", "Ιστορικό", "🎯 Στόχοι"],
        "income_title": "💰 Προσθήκη Εσόδου",
        "expense_title": "💸 Καταγραφή Εξόδου",
        "shopping_title": "🛒 Λίστα για Ψώνια",
        "reminders_title": "🔔 Λογαριασμοί & Λήξεις",
        "history_title": "📜 Ιστορικό",
        "goals_title": "🎯 Στόχοι",
        "amount": "Ποσό (€)",
        "desc": "Περιγραφή",
        "save": "Αποθήκευση",
        "person": "Ποιος;",
        "cat": "Κατηγορία",
        "store": "Κατάστημα",
        "add_goal": "Προσθήκη Νέου Στόχου",
        "goal_name": "Όνομα Στόχου",
        "goal_amt": "Ποσό Στόχου (€)",
        "quick_add": "⚡ Γρήγορη Προσθήκη",
        "missu_cat": "🐾 Missu",
        "export": "📥 Λήψη σε Excel",
        "monthly_report": "📅 Μηνιαία Αναφορά Εξόδων",
        "urgent": "⚠️ Λήγουν σύντομα:",
        "no_reminders": "✅ Όλοι οι λογαριασμοί είναι τακτοποιημένοι!",
        "month": "Μήνας",
        "total": "Σύνολο"
    },
    "🇪🇸 Español": {
        "menu": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "🔔 Recordatorios", "Historial", "🎯 Objetivos"],
        "income_title": "💰 Añadir Ingreso",
        "expense_title": "💸 Registrar Gasto",
        "shopping_title": "🛒 Lista de Compras",
        "reminders_title": "🔔 Facturas y Vencimientos",
        "history_title": "📜 Historial",
        "goals_title": "🎯 Objetivos",
        "amount": "Cantidad (€)",
        "desc": "Descripción",
        "save": "Guardar",
        "person": "¿Quién?",
        "cat": "Categoría",
        "store": "Tienda",
        "add_goal": "Añadir Nuevo Objetivo",
        "goal_name": "Nombre del Objetivo",
        "goal_amt": "Cantidad Meta (€)",
        "quick_add": "⚡ Añadir Rápido",
        "missu_cat": "🐾 Missu",
        "export": "📥 Descargar Excel",
        "monthly_report": "📅 Informe Mensual",
        "urgent": "⚠️ Vencen pronto:",
        "no_reminders": "✅ ¡Todo pagado!",
        "month": "Mes",
        "total": "Total"
    },
    "🇺🇸 English": {
        "menu": ["Dashboard", "Income", "Expenses", "🛒 Shopping List", "🔔 Reminders", "History", "🎯 Goals"],
        "income_title": "💰 Add Income",
        "expense_title": "💸 Record Expense",
        "shopping_title": "🛒 Shopping List",
        "reminders_title": "🔔 Bills & Due Dates",
        "history_title": "📜 History",
        "goals_title": "🎯 Goals",
        "amount": "Amount (€)",
        "desc": "Description",
        "save": "Save",
        "person": "Who?",
        "cat": "Category",
        "store": "Store",
        "add_goal": "Add New Goal",
        "goal_name": "Goal Name",
        "goal_amt": "Target Amount (€)",
        "quick_add": "⚡ Quick Add",
        "missu_cat": "🐾 Missu",
        "export": "📥 Download Excel",
        "monthly_report": "📅 Monthly Report",
        "urgent": "⚠️ Due soon:",
        "no_reminders": "✅ All bills settled!",
        "month": "Month",
        "total": "Total"
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
    
    # URGENT REMINDERS
    st.subheader(curr_t["urgent"])
    today_dt = datetime.now().date()
    next_week = today_dt + timedelta(days=7)
    urgent_rem = c.execute("SELECT title, due_date, amount FROM reminders WHERE due_date <= ?", (str(next_week),)).fetchall()
    
    if urgent_rem:
        for title, due, amt in urgent_rem:
            st.warning(f"🕒 {title}: {amt}€ - {due}")
    else:
        st.success(curr_t["no_reminders"])

    st.divider()

    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'])
        t_inc = df[df['type'] == 'Income']['amount'].sum()
        t_exp = df[df['type'] == 'Expense']['amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric(curr_t["menu"][1], f"{t_inc:,.2f} €")
        c2.metric(curr_t["menu"][2], f"{t_exp:,.2f} €")
        c3.metric("Balance", f"{(t_inc - t_exp):,.2f} €")
        
        st.divider()
        st.subheader(curr_t["monthly_report"])
        exp_df_all = df[df['type'] == 'Expense'].copy()
        if not exp_df_all.empty:
            exp_df_all['date'] = pd.to_datetime(exp_df_all['date'])
            exp_df_all['month_year'] = exp_df_all['date'].dt.strftime('%Y-%m')
            monthly_summary = exp_df_all.groupby('month_year')['amount'].sum().reset_index()
            monthly_summary.columns = [curr_t["month"], curr_t["total"]]
            st.table(monthly_summary)
            
            st.subheader(curr_t["cat"])
            cat_df = exp_df_all.groupby('category')['amount'].sum().reset_index()
            st.bar_chart(data=cat_df, x='category', y='amount')
        
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
            conn.commit(); st.balloons(); st.rerun()

# --- 3. EXPENSES ---
elif choice == curr_t["menu"][2]:
    st.header(curr_t["expense_title"])
    with st.form("exp_form"):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox(curr_t["cat"], [curr_t["missu_cat"], "Supermarket", "Food", "Bills", "Rent", "Entertainment", "Home", "Health", "Other"])
        amt = st.number_input(curr_t["amount"], min_value=0.0, step=0.01)
        desc = st.text_input(curr_t["desc"])
        uploaded_file = st.file_uploader("Receipt Photo", type=['jpg', 'jpeg', 'png'])
        if st.form_submit_button(curr_t["save"]):
            img_str = ""
            if uploaded_file:
                img = Image.open(uploaded_file)
                img.thumbnail((400, 400))
                img_str = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt) VALUES (?,?,?,?,?,?,?)",
                      ("Expense", p, cat, amt, desc, str(datetime.now().date()), img_str))
            conn.commit(); st.success("OK!"); time.sleep(0.5); st.rerun()

# --- 4. SHOPPING LIST ---
elif choice == curr_t["menu"][3]:
    st.header(curr_t["shopping_title"])
    st.subheader(curr_t["quick_add"])
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
    with st.expander("⚙️ Settings"):
        with st.form("add_c"):
            n = st.text_input("Item name")
            s = st.selectbox("Store", ["Lidl", "Σκλαβενίτης"])
            if st.form_submit_button("Add Quick Button"):
                c.execute("INSERT INTO common_products (name, store) VALUES (?,?)", (n, s))
                conn.commit(); st.rerun()
        st.write("---")
        all_c = c.execute("SELECT * FROM common_products").fetchall()
        for cid, cn, cs in all_c:
            if st.button(f"🗑️ {cn} ({cs})", key=f"rm_c_{cid}"):
                c.execute("DELETE FROM common_products WHERE id=?", (cid,))
                conn.commit(); st.rerun()

# --- 5. REMINDERS ---
elif choice == curr_t["menu"][4]:
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

# --- 6. HISTORY ---
elif choice == curr_t["menu"][5]:
    st.header(curr_t["history_title"])
    df_show = pd.read_sql_query("SELECT * FROM entries ORDER BY id DESC", conn)
    for idx, row in df_show.iterrows():
        with st.expander(f"{row['date']} | {row['amount']:.2f}€ | {row['category']}"):
            if row['receipt']: st.image(base64.decodebytes(row['receipt'].encode()))
            if st.button("🗑️", key=f"del_{row['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

# --- 7. GOALS ---
elif choice == curr_t["menu"][6]:
    st.header(curr_t["goals_title"])
    with st.form("new_goal_form"):
        st.subheader(curr_t["add_goal"])
        g_name = st.text_input(curr_t["goal_name"])
        g_target = st.number_input(curr_t["goal_amt"], min_value=0.0)
        if st.form_submit_button(curr_t["save"]):
            if g_name and g_target > 0:
                c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (g_name, g_target))
                conn.commit(); st.success("Goal added!"); st.rerun()
    st.divider()
    total_inc = df[df['type'] == 'Income']['amount'].sum()
    total_exp = df[df['type'] == 'Expense']['amount'].sum()
    savings = total_inc - total_exp
    st.metric("Total Savings", f"{savings:,.2f} €")
    goals_list = c.execute("SELECT * FROM goals").fetchall()
    for gid, name, target in goals_list:
        st.write(f"**{name}**")
        prog = min(savings / target, 1.0) if target > 0 else 0
        st.progress(prog)
        st.write(f"{savings:,.2f} / {target:,.2f} € ({(prog*100):.1f}%)")
        if st.button(f"🗑️ Delete {name}", key=f"dg_{gid}"):
            c.execute("DELETE FROM goals WHERE id=?", (gid,))
            conn.commit(); st.rerun()
