# backend/analyzer.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json, re

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

import pandas as pd

# Load fraud scores from CSV once at startup
FRAUD_PATH = "data/fraud_scores.csv"

fraud_df = None
if os.path.exists(FRAUD_PATH):
    fraud_df = pd.read_csv(FRAUD_PATH)
else:
    print("⚠️ No fraud_scores.csv found — running without risk context.")


def get_user_risk_summary(user_id: str) -> str:
    """Return summarized fraud context for a user."""
    if fraud_df is None or user_id not in fraud_df["user_id"].values:
        return "No fraud risk data available."
    
    user_txns = fraud_df[fraud_df["user_id"] == user_id]
    mean_score = round(user_txns["fraud_score"].mean(), 3)
    high_risk_pct = round((user_txns["fraud_label"].mean()) * 100, 1)
    
    tier = "High" if mean_score > 0.75 else "Medium" if mean_score > 0.4 else "Low"
    return f"User fraud risk: {tier} (avg score {mean_score}, {high_risk_pct}% of recent transactions flagged)."

# load once (or at app start)
txns_df = pd.read_csv("data/transactions.csv", parse_dates=["timestamp"], keep_default_na=False)
fraud_df = pd.read_csv("data/fraud_scores.csv")

def get_fraud_transactions_for_user(user_id: str) -> pd.DataFrame:
    """Return full transaction rows flagged as fraud for user_id, newest first."""
    # filter fraud rows for the user
    user_fraud = fraud_df[(fraud_df["user_id"] == user_id) & (fraud_df["fraud_label"] == 1)]

    if user_fraud.empty:
        return pd.DataFrame(columns=txns_df.columns)  # empty df with same schema

    # merge to get full txn details
    merged = user_fraud.merge(txns_df, on="txn_id", how="left", suffixes=("_f",""))
    # prefer the full txn columns from txns_df; sort newest first
    if "timestamp" in merged.columns:
        merged["timestamp"] = pd.to_datetime(merged["timestamp"], utc=True, errors="coerce")
        merged = merged.sort_values("timestamp", ascending=False)
    return merged



# # Define your model
model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_message_with_gemini(message: str, user_id: str) -> dict:
    """Ask Gemini to classify a message and produce a short response with fraud context."""
    risk_info = get_user_risk_summary(user_id)
    print(get_fraud_transactions_for_user(user_id))

    prompt = f"""
    You are a Capital One customer service assistant.
    Below is the user's fraud analysis summary and message.

    FRAUD CONTEXT:
    {risk_info}

    USER MESSAGE:
    "{message}"

    Based on both the fraud context and message content, classify the issue as HIGH, MEDIUM, or LOW priority:
    - HIGH: Fraud, suspicious activity, financial distress, or high-risk account.
    - MEDIUM: Payment issues, balance questions, routine service requests.
    - LOW: General information, settings, or low-risk topics.

    If the FRAUD CONTEXT indicates low risk, classify the context with less priority.

    Respond with this JSON:
    {{
      "priority": "HIGH|MEDIUM|LOW",
      "response": "short helpful message to the user",
      "confidence": 0.9
    }}
    """

    try:
        result = model.generate_content(prompt)
        text = result.text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print("Gemini error:", e)

    return {"priority": "LOW", "response": "Default response.", "confidence": 0.7}

# def analyze_message_with_gemini(message: str) -> dict:
#     """Use Gemini to classify priority and generate a response."""
#     prompt = f"""
#     You are a Capital One customer service assistant.
#     A user said: "{message}"

#     Classify the issue as HIGH, MEDIUM, or LOW priority:
#     - HIGH: Fraud, suspicious activity, or financial distress
#     - MEDIUM: Payments, balance inquiries, or due dates
#     - LOW: General info or settings

#     Respond with a short message to the user and include a JSON summary like:
#     {{
#         "priority": "HIGH",
#         "response": "Connecting you with a live agent...",
#         "confidence": 0.95
#     }}
#     """

#     result = model.generate_content(prompt)
#     text = result.text.strip()

#     # quick and dirty parse (Gemini outputs structured text)
#     try:
#         json_text = re.search(r'\{.*\}', text, re.DOTALL).group(0)
#         parsed = json.loads(json_text)
#         return parsed
#     except Exception:
#         # fallback if parsing fails
#         return {
#             "priority": "LOW",
#             "response": "This message will be handled by the assistant.",
#             "confidence": 0.7,
#         }
