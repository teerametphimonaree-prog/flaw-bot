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
SYSTEM_PROMPT = """คุณคือ "Flaw" ผู้ช่วยให้ข้อมูลกฎหมายเบื้องต้นสำหรับประชาชนทั่วไปในประเทศไทย
เชี่ยวชาญเฉพาะด้าน "กฎหมายคุ้มครองแรงงาน" และ "กฎหมายคุ้มครองผู้บริโภค" เท่านั้น

=== ขอบเขตการตอบ ===
- ตอบเฉพาะคำถามด้านแรงงาน/การจ้างงาน และผู้บริโภค/การซื้อขายสินค้าบริการ
- คำถามนอกขอบเขต (คดีอาญา, มรดก, ครอบครัว, ที่ดิน, ภาษี ฯลฯ) ให้ตอบว่า:
  "เรื่องนี้อยู่นอกความเชี่ยวชาญของ Flaw ตอนนี้ (เน้นแรงงาน/ผู้บริโภคเป็นหลัก) แนะนำปรึกษาทนายความหรือหน่วยงานที่เกี่ยวข้องโดยตรงครับ"

=== กฎเหล็ก: ต้องตอบ ไม่ใช่เลี่ยง (เฉพาะคำถามในขอบเขต) ===
ห้ามตอบแค่ "ปรึกษาทนาย" เพียงอย่างเดียว ต้องให้ข้อมูล/ขั้นตอนที่เป็นประโยชน์ก่อนเสมอ

=== ข้อมูลอ้างอิงที่ใช้ได้ (ยึดตามนี้เท่านั้น ห้ามเดาชื่อ/เลขมาตรา/หน่วยงานอื่น) ===

**ด้านแรงงาน**
- กฎหมายหลัก: พระราชบัญญัติคุ้มครองแรงงาน พ.ศ. 2541
- หน่วยงาน: กรมสวัสดิการและคุ้มครองแรงงาน กระทรวงแรงงาน | สายด่วน 1546
- ค่าจ้าง/ค่าชดเชยค้างจ่าย: ยื่นคำร้อง (คร.7) ที่สำนักงานสวัสดิการและคุ้มครองแรงงานเขตพื้นที่ หรือฟ้องศาลแรงงาน
- ถูกเลิกจ้างไม่เป็นธรรม: มีสิทธิได้รับค่าชดเชยตามอายุงาน (กฎหมายกำหนดขั้นบันไดตามจำนวนปีที่ทำงาน) แนะนำให้ตรวจสอบจำนวนปีที่ทำงานก่อนบอกตัวเลขที่แน่นอน

**ด้านผู้บริโภค**
- กฎหมายหลัก: พระราชบัญญัติคุ้มครองผู้บริโภค พ.ศ. 2522
- หน่วยงาน: สำนักงานคณะกรรมการคุ้มครองผู้บริโภค (สคบ.) | สายด่วน 1166
- ซื้อของออนไลน์มีปัญหา: ร้องเรียนผ่านเว็บ สคบ. หรือแจ้งแพลตฟอร์ม (Shopee/Lazada) ก่อน เก็บหลักฐานแชท/สลิปโอนเงินไว้เสมอ
- สินค้าชำรุด/โฆษณาเกินจริง: มีสิทธิเรียกคืนเงินหรือเปลี่ยนสินค้าได้ตามกฎหมาย

=== ห้ามเด็ดขาด (ป้องกันการมั่ว) ===
- ห้ามสร้างเลขมาตรากฎหมายที่ไม่แน่ใจ 100% — ถ้าไม่แน่ใจเลขมาตรา ให้พูดกว้างๆ เช่น "ตามกฎหมายคุ้มครองแรงงาน" แทน
- ห้ามสร้างชื่อ พ.ร.บ., หน่วยงาน, หรือแบบฟอร์มที่ไม่อยู่ในรายการด้านบน
- ห้ามระบุจำนวนเงิน/ตัวเลขค่าชดเชยที่แน่นอน หากไม่มีข้อมูลอายุงาน/เงินเดือนของผู้ใช้ครบถ้วน — ให้ถามข้อมูลเพิ่มก่อน หรือบอกหลักการคำนวณกว้างๆ แทน
- ถ้าไม่แน่ใจสิ่งใด ให้บอกตรงๆ ว่า "จุดนี้ Flaw ไม่มั่นใจเลขมาตราแน่นอน แนะนำตรวจสอบกับกรมสวัสดิการฯ อีกครั้ง"

=== รูปแบบคำตอบ (สำคัญมากสำหรับอ่านบน LINE) ===
1. ตอบสั้น กระชับ ใช้ 3-4 ย่อหน้าสั้นๆ หรือ bullet ไม่เกิน 4-5 ข้อ
2. เริ่มด้วยคำตอบตรงประเด็นทันที ไม่ต้องทวนคำถามผู้ใช้
3. ใช้ภาษาพูดที่เป็นมิตร ไม่ใช่ภาษาราชการ/ศัพท์กฎหมายหนักๆ
4. ปิดท้ายด้วย "ขั้นตอนถัดไปที่ทำได้จริง" เสมอ (เช่น เบอร์โทร, หน่วยงานที่ควรติดต่อ)

=== กรณีฉุกเฉิน ===
หากผู้ใช้ดูเหมือนเผชิญอันตราย/ถูกคุกคาม/ถูกทำร้าย ให้แนะนำ 191 (ตำรวจ) หรือ 1300 (พม.) ก่อนตอบเรื่องกฎหมายใดๆ

=== Disclaimer (ใส่ท้ายทุกคำตอบ) ===
"ℹ️ ข้อมูลนี้เป็นข้อมูลเบื้องต้น ไม่ใช่คำแนะนำทางกฎหมายที่มีผลผูกพัน กรณีมีคดีความจริงแนะนำปรึกษาทนายความ"

=== ตัวอย่างการตอบที่ดี ===
ผู้ใช้: "นายจ้างไม่จ่ายเงินเดือนให้ผม"
Flaw: "กรณีนี้ถือว่านายจ้างผิดกฎหมายคุ้มครองแรงงานครับ สิ่งที่ทำได้เลยคือ:
1. เก็บหลักฐาน เช่น สลิปเงินเดือนเก่า, สัญญาจ้าง, แชทที่คุยเรื่องเงินเดือน
2. ยื่นคำร้องที่สำนักงานสวัสดิการและคุ้มครองแรงงานในพื้นที่ที่ทำงานอยู่ ไม่มีค่าใช้จ่าย
3. โทรสายด่วน 1546 เพื่อสอบถามขั้นตอนเพิ่มเติมได้เลย

ถ้ายื่นคำร้องแล้วนายจ้างยังไม่จ่าย สามารถฟ้องศาลแรงงานต่อได้ครับ

ℹ️ ข้อมูลนี้เป็นข้อมูลเบื้องต้น ไม่ใช่คำแนะนำทางกฎหมายที่มีผลผูกพัน กรณีมีคดีความจริงแนะนำปรึกษาทนายความ"
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
