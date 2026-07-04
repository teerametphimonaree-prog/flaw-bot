import os
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = FastAPI()

# ตรงนี้ถ้าค่าใน Environment เป็น None มันจะ Error เลย เราจะแก้ด้วยการใส่ค่าตรงๆ ไปก่อนเพื่อทดสอบ!
# วิธีนี้ทำเพื่อเช็คว่าโค้ดเราทำงานได้แน่ๆ
LINE_TOKEN = "ใส่ TOKEN ของคุณตรงนี้เลย (ไม่ต้องผ่าน os.getenv)"
LINE_SECRET = "ใส่ SECRET ของคุณตรงนี้เลย"

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    handler.handle(body.decode(), signature)
    return {"status": "ok"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="บอทตอบกลับแล้ว!"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
