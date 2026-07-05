import os
import requests
import logging
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import uvicorn

# ตั้งค่า Logging ให้แสดงบนหน้าจอ Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# โหลดค่าจาก Environment
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET", ""))
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_str = body.decode()
    
    logger.info(f"Received request body: {body_str}") # เช็กว่า LINE ส่งอะไรมา
    
    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature error")
        raise HTTPException(status_code=400)
    return {"status": "ok"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text
    logger.info(f"Processing message from {user_id}: {user_text}")

    try:
        # เรียก AI ผ่าน OpenRouter
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
            },
            timeout=10 # เพิ่ม Timeout เพื่อป้องกันบอทค้าง
        )
        
        if response.status_code == 200:
            ai_reply = response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"OpenRouter returned status {response.status_code}: {response.text}")
            ai_reply = "ขออภัยครับ ระบบ AI กำลังขัดข้องชั่วคราว"
            
    except Exception as e:
        logger.exception("Error during AI processing")
        ai_reply = "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผล"

    # ส่งกลับ LINE
    try:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
        logger.info(f"Successfully replied to {user_id}")
    except Exception as e:
        logger.error(f"Failed to reply to LINE: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
