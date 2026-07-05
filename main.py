@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(f"DEBUG: ได้รับข้อความจาก {event.source.user_id}") # เพิ่มบรรทัดนี้
    user_text = event.message.text
    
    try:
        response = requests.post(
            # ... (โค้ดเดิมของคุณ)
        )
        if response.status_code == 200:
            ai_reply = response.json()['choices'][0]['message']['content']
        else:
            print(f"DEBUG: OpenRouter Error {response.text}") # เพิ่มบรรทัดนี้
            ai_reply = "ขออภัยครับ AI ตอบไม่ได้"
            
        # เพิ่มบรรทัดนี้เพื่อเช็กว่ามันกำลังจะตอบจริงๆ
        print(f"DEBUG: กำลังตอบกลับด้วย: {ai_reply}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}") # เพิ่มบรรทัดนี้
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="เกิดข้อผิดพลาดภายใน"))
