import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = FastAPI()

def ask_flaw_with_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"model": "google/gemini-pro-1.5", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content'] if response.status_code == 200 else "AI Error"
    except: return "System Error"

@app.post("/callback")
async def handle_callback(request: Request):
    payload = await request.json()
    for event in payload.get("events", []):
        if event.get("type") == "message":
            reply_token = event["replyToken"]
            user_text = event["message"]["text"]
            reply_text = ask_flaw_with_openrouter(user_text)
            requests.post("https://api.line.me/v2/bot/message/reply",
                headers={"Authorization": f"Bearer {LINE_TOKEN}", "Content-Type": "application/json"},
                json={"replyToken": reply_token, "messages": [{"type": "text", "text": reply_text}]})
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)