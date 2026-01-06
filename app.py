import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import time
import base64
import json
from io import BytesIO
from PIL import Image
import plotly.express as px
from streamlit_lottie import st_lottie

# --- ΡΥΘΜΙΣΗ ΚΩΔΙΚΟΥ ---
MASTER_PASSWORD = "γουρουνακια3" 

st.set_page_config(page_title="Chanchito Pro & Missu", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-label { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
    .metric-value { font-size: 28px; font-weight: bold; }
    .stButton>button { border-radius: 12px; font-weight: bold; width: 100%; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

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

# --- DATABASE SETUP ---
conn = sqlite3.connect('finance_home.db', check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, type TEXT, person TEXT, category TEXT, amount REAL, source_desc TEXT, date TEXT, receipt TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL)")
c.execute("CREATE TABLE IF NOT EXISTS shopping_list (id INTEGER PRIMARY KEY, item TEXT, store TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS common_products (id INTEGER PRIMARY KEY, name TEXT, store TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, title TEXT, due_date TEXT, status TEXT)")
conn.commit()

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

# --- TRANSLATIONS ---
lang_choice = st.sidebar.radio("Language", ["🇬🇷 Ελληνικά", "🇪🇸 Español", "🇬Β English"])
t = {
    "🇬🇷 Ελληνικά": {
        "menu": ["Κεντρική", "Έσοδα", "Έξοδα", "🛒 Σούπερ Μάρκετ", "Ιστορικό", "🎯 Στόχοι", "🔔 Υπενθυμίσεις"],
        "income": "Έσοδα", "expense": "Έξοδα", "balance": "Υπόλοιπο", "report": "📅 Μηνιαία Αναφορά",
        "month": "Μήνας", "total": "Σύνολο", "save": "Αποθήκευση", "person": "Ποιος;", "amt": "Ποσό (€)"
    },
    "🇪🇸 Español": {
        "menu": ["Panel", "Ingresos", "Gastos", "🛒 Supermercado", "Historial", "🎯 Objetivos", "🔔 Recordatorios"],
        "income": "Ingresos", "expense": "Gastos", "balance": "Saldo", "report": "📅 Mensual",
        "month": "Mes", "total": "Total", "save": "Guardar", "person": "¿Quién?", "amt": "Cantidad (€)"
    },
    "🇬Β English": {
        "menu": ["Dashboard", "Income", "Expenses", "🛒 Shopping", "History", "🎯 Goals", "🔔 Reminders"],
        "income": "Income", "expense": "Expenses", "balance": "Balance", "report": "📅 Monthly Report",
        "month": "Month", "total": "Total", "save": "Save", "person": "Who?", "amt": "Amount (€)"
    }
}
curr_t = t[lang_choice]
choice = st.sidebar.selectbox("Menu", curr_t["menu"])

# Data Loading
df_raw = pd.read_sql_query("SELECT * FROM entries", conn)

# --- 1. DASHBOARD ---
if choice in ["Κεντρική", "Panel", "Dashboard"]:
    col_lottie, col_title = st.columns([1, 4])
    with col_lottie:
        # Hardcoded Piggy Animation
        pig_data = {"v":"5.7.1","fr":30,"ip":0,"op":60,"w":500,"h":500,"nm":"Piggy","ddd":0,"assets":[],"layers":[{"ddd":0,"ind":1,"ty":4,"nm":"Body","sr":1,"ks":{"o":{"a":0,"k":100,"ix":11},"r":{"a":0,"k":0,"ix":10},"p":{"a":0,"k":[250,250,0],"ix":2},"a":{"a":0,"k":[0,0,0],"ix":1},"s":{"a":1,"k":[{"i":{"x":[0.667,0.667,0.667],"y":[1,1,1]},"o":{"x":[0.333,0.333,0.333],"y":[0,0,0]},"t":0,"s":[100,100,100]},{"i":{"x":[0.667,0.667,0.667],"y":[1,1,1]},"o":{"x":[0.333,0.333,0.333],"y":[0,0,0]},"t":30,"s":[105,95,100]},{"t":60,"s":[100,100,100]}],"ix":6}},"shapes":[{"ty":"gr","it":[{"d":1,"ty":"el","s":{"a":0,"k":[200,180],"ix":2},"p":{"a":0,"k":[0,0],"ix":3},"nm":"Circle","mn":"ADBE Vector Shape - Ellipse","hd":False},{"ty":"fl","c":{"a":0,"k":[1,0.75,0.79,1],"ix":4},"o":{"a":0,"k":100,"ix":5},"r":1,"bm":0,"nm":"Fill","mn":"ADBE Vector Graphic - Fill","hd":False},{"ty":"tr","p":{"a":0,"k":[0,0],"ix":2},"a":{"a":0,"k":[0,0],"ix":1},"s":{"a":0,"k":[100,100],"ix":3},"r":{"a":0,"k":0,"ix":6},"o":{"a":0,"k":100,"ix":7},"sk":{"a":0,"k":0,"ix":4},"sa":{"a":0,"k":0,"ix":5},"nm":"Transform"}],"nm":"Group 1","np":2,"cix":2,"bm":0,"ix":1,"mn":"ADBE Vector Group","hd":False}]}]}
        st_lottie(pig_data, height=120, key="pig_dash")
    with col_title:
        st.title(choice)
    
    if not df_raw.empty:
        df_raw['amount'] = pd.to_numeric(df_raw['amount'])
        t_inc = df_raw[df_raw['type'] == 'Income']['amount'].sum()
        t_exp = df_raw[df_raw['type'] == 'Expense']['amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-label" style="color:#4CAF50">➕ {curr_t["income"]}</div><div class="metric-value">{t_inc:,.2f} €</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-label" style="color:#FF5252">➖ {curr_t["expense"]}</div><div class="metric-value">{t_exp:,.2f} €</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-label" style="color:#2196F3">💎 {curr_t["balance"]}</div><div class="metric-value">{(t_inc - t_exp):,.2f} €</div></div>', unsafe_allow_html=True)
        
        st.divider()
        exp_df = df_raw[df_raw['type'] == 'Expense'].copy()
        if not exp_df.empty:
            # 1. ΓΡΑΦΗΜΑ ΠΡΩΤΟ
            st.subheader("📊 Κατανομή Εξόδων")
            fig = px.pie(exp_df, values='amount', names='category', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # 2. ΜΗΝΙΑΙΑ ΑΝΑΦΟΡΑ ΔΕΥΤΕΡΗ
            st.subheader(curr_t["report"])
            exp_df['month_yr'] = pd.to_datetime(exp_df['date']).dt.strftime('%B %Y')
            monthly_sum = exp_df.groupby('month_yr')['amount'].sum().reset_index()
            monthly_sum.columns = [curr_t['month'], curr_t['total']]
            st.table(monthly_sum)

        st.download_button("📥 Excel", data=to_excel(df_raw), file_name="chanchito_export.xlsx")
    else:
        st.info("No data yet.")

# --- 2. INCOME ---
elif choice == curr_t["menu"][1]:
    st.header(curr_t["income"])
    with st.form("inc_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Category", ["Μισθός", "Ενοίκιο", "Άλλο"])
        amt = st.number_input(curr_t["amt"], min_value=0.0)
        desc = st.text_input("Desc")
        if st.form_submit_button(curr_t["save"]):
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date) VALUES (?,?,?,?,?,?)", ("Income", p, cat, amt, desc, str(date.today())))
            conn.commit(); st.success("Saved!"); time.sleep(1); st.rerun()

# --- 3. EXPENSES ---
elif choice == curr_t["menu"][2]:
    st.header(curr_t["expense"])
    with st.form("exp_form", clear_on_submit=True):
        p = st.selectbox(curr_t["person"], ["Άις", "Κωνσταντίνος"])
        cat = st.selectbox("Category", ["🐾 Missu", "Σούπερ Μάρκετ", "Φαγητό", "Λογαριασμοί", "Σπίτι", "Υγεία", "Ενοίκιο", "Άλλο"])
        amt = st.number_input(curr_t["amt"], min_value=0.0)
        desc = st.text_input("Desc")
        up = st.file_uploader("Receipt", type=['jpg', 'png'])
        if st.form_submit_button(curr_t["save"]):
            img_s = ""
            if up:
                img = Image.open(up).convert('RGB'); img.thumbnail((400, 400))
                img_s = image_to_base64(img)
            c.execute("INSERT INTO entries (type, person, category, amount, source_desc, date, receipt) VALUES (?,?,?,?,?,?,?)", ("Expense", p, cat, amt, desc, str(date.today()), img_s))
            conn.commit(); st.success("Saved!"); time.sleep(1); st.rerun()

# --- 4. SHOPPING ---
elif choice == curr_t["menu"][3]:
    st.header(curr_t["menu"][3])
    cl, cs = st.columns(2)
    with cl:
        st.subheader("Lidl")
        for lid_id, lid_n in c.execute("SELECT id, name FROM common_products WHERE store='Lidl'").fetchall():
            if st.button(f"➕ {lid_n}", key=f"lid_{lid_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (lid_n, "Lidl")); conn.commit(); st.rerun()
    with cs:
        st.subheader("Σκλαβενίτης")
        for sk_id, sk_n in c.execute("SELECT id, name FROM common_products WHERE store='Σκλαβενίτης'").fetchall():
            if st.button(f"➕ {sk_n}", key=f"sk_{sk_id}"):
                c.execute("INSERT INTO shopping_list (item, store) VALUES (?,?)", (sk_n, "Σκλαβενίτης")); conn.commit(); st.rerun()
    st.divider()
    for sid, itm, sto in c.execute("SELECT id, item, store FROM shopping_list").fetchall():
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"🛒 **{itm}** ({sto})")
        if col2.button("✅", key=f"done_{sid}"):
            c.execute("DELETE FROM shopping_list WHERE id=?", (sid,)); conn.commit(); st.rerun()
    with st.expander("Προσθήκη Προϊόντων"):
        with st.form("q_add"):
            n, s = st.text_input("Προϊόν"), st.selectbox("Store", ["Lidl", "Σκλαβενίτης"])
            if st.form_submit_button("Add"):
                c.execute("INSERT INTO common_products (name, store) VALUES (?,?)", (n, s)); conn.commit(); st.rerun()

# --- 5. HISTORY ---
elif choice == curr_t["menu"][4]:
    st.header("Ιστορικό")
    for idx, r in df_raw.sort_values('id', ascending=False).iterrows():
        with st.expander(f"{r['date']} | {r['amount']}€ | {r['category']}"):
            if r['receipt']: st.image(base64.b64decode(r['receipt']))
            st.write(f"Περιγραφή: {r['source_desc']}")
            if st.button("🗑️ Διαγραφή", key=f"del_{r['id']}"):
                c.execute("DELETE FROM entries WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

# --- 6. GOALS ---
elif choice == curr_t["menu"][5]:
    st.header("🎯 Στόχοι")
    with st.form("goal_f"):
        gn, ga = st.text_input("Στόχος"), st.number_input("Ποσό", min_value=0.0)
        if st.form_submit_button("Προσθήκη"):
            c.execute("INSERT INTO goals (name, target_amount) VALUES (?,?)", (gn, ga)); conn.commit(); st.rerun()
    
    total_bal = df_raw[df_raw['type'] == 'Income']['amount'].sum() - df_raw[df_raw['type'] == 'Expense']['amount'].sum()
    for gid, gn, gt in c.execute("SELECT * FROM goals").fetchall():
        st.write(f"**{gn}** ({total_bal:,.2f} / {gt:,.2f} €)")
        prog = min(total_bal/gt, 1.0) if gt > 0 else 0
        st.progress(prog)
        if st.button("🗑️", key=f"g_del_{gid}"):
            c.execute("DELETE FROM goals WHERE id=?", (gid,)); conn.commit(); st.rerun()

# --- 7. REMINDERS ---
elif choice == curr_t["menu"][6]:
    st.header("🔔 Υπενθυμίσεις")
    with st.form("rem_f"):
        rt, rd = st.text_input("Τίτλος"), st.date_input("Ημερομηνία")
        if st.form_submit_button("Add"):
            c.execute("INSERT INTO reminders (title, due_date, status) VALUES (?,?,?)", (rt, str(rd), "Pending")); conn.commit(); st.rerun()
    for rid, rit, rid_d, ris in c.execute("SELECT * FROM reminders ORDER BY due_date ASC").fetchall():
        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        c1.write(f"📅 {rid_d} - **{rit}**")
        c2.write("🔴" if ris == "Pending" else "🟢")
        if c3.button("✅", key=f"r_done_{rid}"):
            c.execute("UPDATE reminders SET status='Paid' WHERE id=?", (rid,)); conn.commit(); st.rerun()
        if c3.button("🗑️", key=f"r_del_{rid}"):
            c.execute("DELETE FROM reminders WHERE id=?", (rid,)); conn.commit(); st.rerun()
