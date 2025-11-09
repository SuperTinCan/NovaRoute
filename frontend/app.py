# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime

# ---- Config ----
API_URL = "http://127.0.0.1:8000/analyze"
st.set_page_config(page_title="PriorityAI - Customer Service Routing", page_icon="💬", layout="wide")

# ---- Load mock user metadata & transactions from disk ----
DATA_DIR = "data"
ACCOUNTS_PATH = os.path.join(DATA_DIR, "accounts.json")
TXNS_PATH = os.path.join(DATA_DIR, "transactions.json")

def load_accounts():
    if os.path.exists(ACCOUNTS_PATH):
        with open(ACCOUNTS_PATH) as f:
            return {acct["user_id"]: acct for acct in json.load(f)}
    # fallback small built-in if no file
    return {
        "user_001": {"user_id":"user_001","name":"Alex Johnson","account_balance":2350.21,"card_status":"Active"},
        "user_002": {"user_id":"user_002","name":"Jamie Patel","account_balance":542.87,"card_status":"Frozen"},
        "user_003": {"user_id":"user_003","name":"Riley Chen","account_balance":7129.42,"card_status":"Active"},
    }

def load_txns():
    if os.path.exists(TXNS_PATH):
        with open(TXNS_PATH) as f:
            txns = json.load(f)
            df = pd.DataFrame(txns)
            # ensure timestamp is datetime
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            return df
    return pd.DataFrame(columns=[
        "txn_id","user_id","timestamp","amount","currency","merchant","merchant_category",
        "city","country","channel","is_foreign","is_high_amount","velocity_24h",
        "device_fingerprint","ip_country","merchant_risk_score","label_fraud","user_reported_issue"
    ])

accounts = load_accounts()
txns_df = load_txns()

# ---- Session State ----
if "user_chats" not in st.session_state:
    st.session_state.user_chats = {uid: [] for uid in accounts.keys()}
if "current_user" not in st.session_state:
    st.session_state.current_user = list(accounts.keys())[0]

# ---- Sidebar: user selector + save chats ----
st.sidebar.header("👤 Select Active User")
user_id = st.sidebar.selectbox(
    "Choose a user:",
    options=list(accounts.keys()),
    format_func=lambda uid: f"{accounts[uid]['name']} ({uid})"
)
st.session_state.current_user = user_id

if st.sidebar.button("💾 Save Chats"):
    os.makedirs("local_chats", exist_ok=True)
    for uid, chats in st.session_state.user_chats.items():
        with open(f"local_chats/{uid}.json", "w") as f:
            json.dump(chats, f, indent=2)
    st.sidebar.success("Chats saved locally!")

# ---- Layout: left = chat, right = account + transactions ----
left, right = st.columns([2, 3])

# ---- Left column: Chat UI ----
with left:
    user = accounts[user_id]
    st.title("💬 PriorityAI - Smart Customer Support")
    st.caption(f"Chatting as **{user.get('name','Unknown')}**  •  Balance: **{user.get('account_balance','N/A')}**  •  Card: **{user.get('card_status','N/A')}**")
    user_message = st.text_input("Enter your message:")
    if st.button("Send"):
        if user_message.strip():
            payload = {"user_id": user_id, "message": user_message}
            try:
                res = requests.post(API_URL, json=payload)
                data = res.json()
                st.session_state.user_chats[user_id].append(
                    {
                        "user": user_message,
                        "priority": data["priority"],
                        "response": data["response"],
                        "confidence": data["confidence"],
                    }
                )
            except Exception as e:
                st.error(f"Error contacting backend: {e}")
        else:
            st.warning("Please enter a message.")

    st.divider()
    st.subheader(f"Conversation with {user.get('name')}")
    chat_history = st.session_state.user_chats[user_id]
    if chat_history:
        for msg in reversed(chat_history):
            st.markdown(f"**You:** {msg['user']}")
            st.markdown(f"**Priority:** {msg['priority']} ({msg['confidence']*100:.0f}% confidence)")
            st.markdown(f"**Assistant:** {msg['response']}")
            st.markdown(f"*{msg.get('ts','') }*")
            st.markdown("---")
    else:
        st.info("No messages yet for this user.")

# ---- Right column: Account details and transaction list ----
with right:
    st.header("Account Overview")
    acct = accounts[user_id]

    # pretty account panel
    cols = st.columns([2,3])
    with cols[0]:
        st.metric("Account Balance", f"${acct.get('account_balance', 'N/A')}")
        st.write(f"**Status:** {acct.get('card_status','N/A')}")

        fraud_path = "data/fraud_scores.csv"
        if os.path.exists(fraud_path):
            risk_df = pd.read_csv(fraud_path)
            if user_id in risk_df["user_id"].values:
                avg_score = risk_df[risk_df["user_id"] == user_id]["fraud_score"].mean()
                st.metric("Avg Fraud Risk", f"{avg_score:.2f}")

    with cols[1]:
        st.write(f"**Opened:** {acct.get('opened_at', 'unknown')}")
        st.write(f"**Reported Priority:** {acct.get('reported_priority', 'N/A')}")
        st.write(f"**Chargebacks:** {acct.get('chargeback_history',0)}")
        st.write(f"**Last login country:** {acct.get('last_login_ip_country','N/A')}")

    st.divider()
    st.subheader("Recent Transactions")

    # filter transactions for selected user
    user_txns = txns_df[txns_df["user_id"] == user_id].copy()

    if user_txns.empty:
        st.info("No transactions available for this user (run scripts/generate_data.py).")
    else:
        # sort newest first
        user_txns = user_txns.sort_values("timestamp", ascending=False)

        # quick filters
        with st.expander("Filters"):
            col1, col2, col3 = st.columns(3)
            with col1:
                min_amt = st.number_input("Min amount", value=0.0, step=1.0, key="min_amt")
            with col2:
                only_foreign = st.checkbox("Only foreign txns", value=False, key="only_foreign")
            with col3:
                show_fraud = st.checkbox("Highlight flagged fraud", value=True, key="show_fraud")

            # apply filters
            if min_amt > 0:
                user_txns = user_txns[user_txns["amount"] >= float(min_amt)]
            if only_foreign:
                user_txns = user_txns[user_txns["is_foreign"] == 1]

        # display a compact dataframe with the most relevant columns
        display_cols = ["timestamp","txn_id","merchant","merchant_category","amount","country","channel","is_foreign","merchant_risk_score","label_fraud"]
        available_cols = [c for c in display_cols if c in user_txns.columns]
        df_display = user_txns[available_cols].copy()

        # pretty format timestamp and amount
        if "timestamp" in df_display.columns:
            df_display["timestamp"] = df_display["timestamp"].dt.tz_convert(None).dt.strftime("%Y-%m-%d %H:%M:%S")
        if "amount" in df_display.columns:
            df_display["amount"] = df_display["amount"].map(lambda x: f"${x:,.2f}")

        # highlight fraud rows
        def highlight_fraud(row):
            return ["background-color: #ffdddd" if row.get("label_fraud",0)==1 else "" for _ in row]

        st.write(f"Showing {len(df_display)} transaction(s).")
        st.dataframe(df_display, width="stretch", height=360)

        # option to view raw JSON for a selected txn
        txn_ids = df_display["txn_id"].tolist() if "txn_id" in df_display.columns else []
        selected_txn = st.selectbox("Inspect transaction (raw)", options=["--"] + txn_ids)
        if selected_txn and selected_txn != "--":
            raw = user_txns[user_txns["txn_id"] == selected_txn].to_dict(orient="records")
            st.json(raw[0])

    st.divider()
    # small analytics for the user
    st.subheader("Quick Analytics")

    if ("label_fraud" in user_txns.columns) and (len(user_txns) > 0):
        # Map 0/1 -> strings, handle NaNs, then count
        status_df = (
            user_txns["label_fraud"]
            .map({0: "Not flagged", 1: "Flagged"})
            .fillna("Unknown")
            .astype("string")
            .value_counts(dropna=False)
            .rename_axis("Status")
            .reset_index(name="Count")
        )

        # Ensure dtype clarity for Altair
        status_df = status_df.astype({"Status": "string", "Count": "int64"})

        # Keep a stable order if both classes exist
        order = [s for s in ["Flagged", "Not flagged", "Unknown"] if s in set(status_df["Status"])]

        chart = (
            alt.Chart(status_df)
            .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
            .encode(
                x=alt.X("Status:N", sort=order, title="Transaction status"),
                y=alt.Y("Count:Q"),
                color=alt.Color("Status:N", legend=None),
                tooltip=[alt.Tooltip("Status:N"), alt.Tooltip("Count:Q")]
            )
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.write("No analytics available.")

