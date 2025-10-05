from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import aiohttp
import os
from datetime import date
from collections import defaultdict
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage

# Env variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Daily storage
daily_data = defaultdict(lambda: defaultdict(list))
photo_data = defaultdict(lambda: defaultdict(list))

async def start(update: Update, context):
    await update.message.reply_text(
        "👋 नमस्ते! Daily Report Bot.\n\n"
        "📱 WhatsApp से messages/photos forward करो।\n"
        "📊 /report से आज की report generate करो।\n"
        "(Auto daily reset होता है।)"
    )

async def generate_report(messages: list) -> str:
    today_str = date.today().strftime("%d-%m-%Y")
    all_msgs = "\n".join(messages)
    prompt = f"""आज {today_str} की activities से एक daily report बनाओ (Hindi में):

Messages/Photos:
{all_msgs}

Report format:
- 📅 Date
- 🔹 मुख्य Activities (3-4 bullet points)
- 📷 Photos count
- 💡 Summary
"""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "mixtral-8x7b-32768", "messages": [{"role": "user", "content": prompt}]}
    async with aiohttp.ClientSession() as session:
        async with session.post(GROQ_URL, headers=headers, json=data) as resp:
            result = await resp.json()
            try:
                return result["choices"][0]["message"]["content"]
            except:
                return "❌ Error in AI response."

def create_pdf(user_id, messages, photos):
    today_str = date.today().strftime("%d-%m-%Y")
    filename = f"report_{user_id}_{today_str}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Page 1: Text summary
    story.append(Paragraph(f"Daily Report - {today_str}", styles['Title']))
    story.append(Spacer(1, 20))
    for msg in messages:
        story.append(Paragraph(msg, styles['Normal']))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # Page 2: Collage of photos (max 4)
    if photos:
        collage_file = f"collage_{user_id}.jpg"
        make_collage(photos, collage_file)
        story.append(Paragraph("Photos Collage", styles['Heading2']))
        story.append(Image(collage_file, width=400, height=400))

    doc.build(story)
    return filename

def make_collage(photos, output_file, size=(2,2)):
    images = [PILImage.open(p).resize((300,300)) for p in photos[:4]]
    grid_w, grid_h = size
    collage = PILImage.new('RGB', (300*grid_w, 300*grid_h), color="white")
    for idx, img in enumerate(images):
        x = (idx % grid_w) * 300
        y = (idx // grid_w) * 300
        collage.paste(img, (x,y))
    collage.save(output_file)

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    today = date.today()
    if update.message.text:
        msg = f"💬 {update.message.text}"
        daily_data[user_id][today].append(msg)
    elif update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        file_path = f"photo_{user_id}_{today}_{photo_file.file_unique_id}.jpg"
        await photo_file.download_to_drive(file_path)
        caption = update.message.caption or "📷 Photo"
        daily_data[user_id][today].append(caption)
        photo_data[user_id][today].append(file_path)
    await update.message.reply_text("✅ Saved!")

async def report(update: Update, context):
    user_id = update.effective_user.id
    today = date.today()
    messages = daily_data[user_id][today]
    photos = photo_data[user_id][today]

    if not messages and not photos:
        await update.message.reply_text("📭 आज कोई data नहीं मिला।")
        return

    # Generate AI summary
    summary = await generate_report(messages)

    # Create PDF
    pdf_file = create_pdf(user_id, messages, photos)

    # Send both
    await update.message.reply_text(f"📝 Summary:\n{summary}")
    await update.message.reply_document(open(pdf_file, "rb"))

def main():
    application = (
        Application.builder()
        .job_queue(None)
        .token(TELEGRAM_TOKEN)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    print("✅ Bot started...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()