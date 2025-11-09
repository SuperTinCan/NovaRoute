from fastapi import FastAPI
from pydantic import BaseModel
from backend.analyzer import analyze_message_with_gemini

class MessageRequest(BaseModel):
    user_id: str
    message: str

app = FastAPI()

@app.post("/analyze")
async def analyze_message(data: MessageRequest):
    result = analyze_message_with_gemini(data.message, data.user_id)
    return {"user_id": data.user_id, **result}


@app.get("/")
def root():
    return {"status": "FastAPI backend running"}
