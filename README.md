# Daily Report Bot

## Features
- WhatsApp से forward किए गए messages/photos save करता है
- AI (Groq API) से daily summary बनाता है
- PDF generate करता है (Page 1: text summary, Page 2: photo collage)
- Telegram पर text + PDF दोनों भेजता है

## Deploy on Railway
1. इस repo को GitHub पर push करो
2. Railway में नया project बनाओ → repo connect करो
3. Env Variables set करो:
   - TELEGRAM_TOKEN
   - GROQ_API_KEY
4. Deploy हो जाएगा 🚀
