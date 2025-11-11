# 💬 NovaRoute: Intelligent Customer Routing Assistant 
> Built for Capital One Hackathon 2025

## 🚀 Overview  
**NovaRoute** is an AI-driven customer service platform that intelligently routes user inquiries based on *fraud risk*, *intent*, and *urgency*.  
By merging traditional fraud detection with generative AI reasoning, NovaRoute ensures high-risk or urgent users are prioritized for human support, while routine requests are handled instantly by an AI chatbot.

---

## 🧠 Features  
- **AI-Powered Routing:** Uses Gemini AI to determine message intent and priority.  
- **Fraud Risk Detection:** Integrates an unsupervised **IsolationForest** model to detect anomalous transactions.  
- **Dynamic Fraud Injection:** Simulate high-risk behavior and see real-time updates to risk scores.  
- **Streamlit Dashboard:** Visualizes user profiles, recent transactions, and live chats with adjustable filters.  
- **Multi-User Simulation:** Switch between multiple mock customers with persistent chat histories.  

---

## ⚙️ Tech Stack  
- **Frontend:** Streamlit (Python)  
- **Backend:** FastAPI  
- **AI:** Gemini API for conversation + prioritization  
- **ML:** Scikit-learn IsolationForest model (trained in Google Colab)  
- **Data:** Synthetic datasets generated with pandas & Faker  
- **Visualization:** Altair for fraud and transaction analytics  

---

## 🏗️ Architecture
```
User → Streamlit UI → FastAPI Backend → Gemini Model → Priority Routing
                        ↓                  ↑
                Fraud Detection → Fraud Scores
```

---

## 🧩 Installation
```bash
# Clone repository
git clone https://github.com/supertincan/NovaRoute.git
cd NovaRoute

# Create virtual environment
uv venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows

# Install dependencies
uv add fastapi uvicorn streamlit pandas faker python-dotenv requests scikit-learn
```

---

## ▶️ Usage

Run both frontend and backend in separate terminals:
```bash
# Terminal 1 - backend
uvicorn backend.main:app --reload

# Terminal 2 - frontend
streamlit run frontend/app.py
```

## 📊 Data Simulation

Generate and inject fake high-risk transactions directly from the UI:

Select a mock user.

Click “Inject High-Fraud for this user.”

Watch fraud scores and chat priorities update dynamically.

## 💡 How It Works

- **Fraud Model:** Detects anomalous transactions using IsolationForest trained on synthetic banking data.

- **Gemini Integration:** Processes message context + risk data to assign routing priority (Low, Medium, High).

- **Routing Logic:** Low-priority → handled by AI, High-priority → escalated to a live agent simulation.

## 🏆 Hackathon Impact

NovaRoute showcases how **data-driven fraud analysis** and **AI language reasoning** can merge to improve customer experience, reduce wait times, and optimize human resource allocation.

## 🧭 Future Work

- Expand routing logic using reinforcement learning for adaptive optimization.

- Integrate live transaction APIs for real-time fraud data.

- Deploy as an internal Capital One customer support tool.

## 👥 Team

Developed by Artin Seyrafi for Capital One Hackathon 2025

**Tech Focus:** AI Infrastructure, Fraud Analytics, and Intelligent Customer Support Systems