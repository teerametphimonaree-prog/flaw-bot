import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import uvicorn

app = FastAPI()

# --- ใส่ค่าตรงๆ ตรงนี้เลย เพื่อตัดปัญหาเรื่อง Environment บน Render ---
LINE_CHANNEL_ACCESS_TOKEN = "t24m8xBgP/QKEsrqW6bLKnX9W7mtHjkdyeYuHDl30bmtHKOvcvkyzyn3EPR2PtMRC2Pr2NAT66SPvogb4EZps0ekZ9Ury4xZOTbrWUg7q4ae3dMp7yPt51VI1aHrOOX6LgjT+s2wXRMzK9uH5OuZEAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "fde0b7ca988eeb5f4460fdae8fcf9e5a"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    # ทดสอบแค่ให้มันตอบกลับมาว่าได้รับข้อความแล้ว
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="บอทได้รับข้อความแล้ว!"))

if __name__ == "__main__":
    # ใช้พอร์ตที่ Render กำหนด
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
