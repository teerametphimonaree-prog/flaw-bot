import os
import requests
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import uvicorn

app = FastAPI()

# ดึงค่าจาก Environment Variables ที่คุณตั้งไว้ใน Render
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET", ""))
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400)
    return {"status": "ok"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    
    # 1. ส่งข้อความไปถาม AI ที่ OpenRouter
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://render.com", 
                "X-Title": "Flaw-Bot",
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": user_text}]
            }
        )
        # 2. รับคำตอบจาก AI
        if response.status_code == 200:
            ai_reply = response.json()['choices'][0]['message']['content']
        else:
            ai_reply = "ขออภัยครับ ตอนนี้ AI กำลังยุ่งอยู่ ลองใหม่นะครับ"
    except Exception as e:
        ai_reply = "เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI ครับ"
        print(f"Error: {e}")
        
    # 3. ส่งคำตอบกลับเข้า LINE
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
