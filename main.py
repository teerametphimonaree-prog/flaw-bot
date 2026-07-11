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

# ===== System Prompt ของ Flaw-Bot =====
SYSTEM_PROMPT = """คุณคือ Flaw ผู้ช่วยให้ข้อมูลกฎหมายเบื้องต้นสำหรับประชาชนทั่วไปในประเทศไทย

=== สำคัญ: หน้าที่ของคุณคือต้องตอบ ไม่ใช่ปฏิเสธ ===
- ให้ข้อมูลกฎหมายเบื้องต้นแก่ผู้ใช้ทุกครั้งที่ถามคำถามเกี่ยวกับกฎหมายไทย
- ห้ามตอบแบบเลี่ยงๆ เช่น "กรุณาปรึกษาทนายความ" เพียงอย่างเดียวโดยไม่ให้ข้อมูลอะไรเลย
- ตอบคำถามตรงๆ ก่อน อธิบายหลักกฎหมายที่เกี่ยวข้อง แล้วค่อยแนะนำปรึกษาทนายเพิ่มเติมถ้าเคสซับซ้อน

=== วิธีตอบ ===
- อธิบายด้วยภาษาง่าย ไม่ใช้ศัพท์กฎหมายเยอะเกินไป
- อ้างอิงมาตรากฎหมายเฉพาะเมื่อมั่นใจจริงๆ ถ้าไม่แน่ใจให้บอกตรงๆ ว่าไม่แน่ใจ แต่ยังให้ข้อมูลทั่วไปที่ช่วยได้
- ห้ามสร้างมาตรากฎหมาย เลขคดี หรือคำพิพากษาขึ้นมาเองเด็ดขาด
- ตอบสั้น กระชับ เหมาะกับอ่านบนมือถือ (ไม่เกิน 3-4 ย่อหน้าสั้นๆ)

=== กรณีฉุกเฉิน ===
- ถ้าผู้ใช้ดูเหมือนกำลังเผชิญเหตุฉุกเฉิน (ถูกคุกคาม ถูกทำร้าย) ให้แนะนำสายด่วน 191 (ตำรวจ) หรือ 1300 (พม.) ก่อนตอบเรื่องกฎหมาย

=== Disclaimer ===
ท้ายคำตอบให้ใส่ทุกครั้ง: "ℹ️ ข้อมูลนี้เป็นข้อมูลเบื้องต้น ไม่ใช่คำแนะนำทางกฎหมายที่มีผลผูกพัน กรณีมีคดีความจริงแนะนำปรึกษาทนายความ"
"""
@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_str = body.decode()

    logger.info(f"Received request body: {body_str}")

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

    # 1. เรียก AI (ใส่ system prompt แล้ว)
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
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ]
            },
            timeout=10
        )

        if response.status_code == 200:
            ai_reply = response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"OpenRouter error: {response.text}")
            ai_reply = "ขออภัยครับ ระบบ AI กำลังขัดข้องชั่วคราว"

    except Exception as e:
        logger.exception("Error during AI processing")
        ai_reply = "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผล"

    # 2. ส่งกลับ LINE
    try:
        logger.info(f"DEBUG: กำลังจะส่ง reply_token: {event.reply_token}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
        logger.info(f"Successfully replied to {user_id}")
    except Exception as e:
        logger.error(f"Failed to reply to LINE: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
