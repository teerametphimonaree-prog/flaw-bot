import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import requests
import uvicorn

load_dotenv()
app = FastAPI()

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    
    # --- บรรทัดนักสืบ ---
    print(f"--- บอทได้รับข้อความ: {body.decode()} ---") 
    
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        print("--- ผิดพลาด: Signature ไม่ตรง! ---")
        raise HTTPException(status_code=400)
    return {"status": "ok"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(f"--- กำลังตอบกลับข้อความ: {event.message.text} ---")
    # (โค้ด OpenRouter ของคุณตรงนี้)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="บอทได้รับข้อความแล้ว!"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
